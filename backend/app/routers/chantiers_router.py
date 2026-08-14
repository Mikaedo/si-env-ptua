"""
chantiers_router.py
-------------------
- GET /chantiers : lister les chantiers
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.shape import to_shape

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/chantiers", tags=["Chantiers"])


def _serialize_chantier(chantier: models.Chantier):
    geom = None
    if chantier.geom:
        try:
            point = to_shape(chantier.geom)
            geom = {"type": "Point", "coordinates": (point.x, point.y)}
        except Exception:
            geom = None
    return {
        "id": chantier.id,
        "nom": chantier.nom,
        "commune": chantier.commune,
        "geom": geom,
        "rayon_influence_m": chantier.rayon_influence_m,
    }


def _parametrage_metier(courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    """Profils habilites a tenir le referentiel des chantiers.

    Decider qu'un ouvrage entre dans le perimetre du suivi, le positionner sur
    la carte et fixer l'etendue de sa zone d'influence sont des decisions
    environnementales. Elles reviennent au specialiste du suivi
    environnemental, qui connait les emprises et repond du PGES, et non a
    l'administrateur de la plateforme, dont le metier porte sur les comptes et
    l'exploitation. Ce dernier conserve l'acces pour assurer la continuite du
    service.
    """
    autorises = (models.RoleEnum.SPEC_ENV, models.RoleEnum.ADMIN)
    if courant.role not in autorises:
        raise HTTPException(
            status_code=403,
            detail="Le référentiel des chantiers relève du spécialiste du suivi environnemental.",
        )
    return courant


@router.get("", response_model=list[schemas.ChantierOut])
def lister_chantiers(db: Session = Depends(get_db),
                     courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    return [_serialize_chantier(c) for c in db.query(models.Chantier).order_by(models.Chantier.nom).all()]


@router.post("", response_model=schemas.ChantierOut)
def creer_chantier(data: schemas.ChantierCreate, db: Session = Depends(get_db), _: models.Utilisateur = Depends(_parametrage_metier)):
    geom = None
    if data.latitude is not None and data.longitude is not None:
        # Ecriture en EWKT plutot qu'avec ST_MakePoint : PostGIS interprete
        # cette forme nativement, et elle reste une simple chaine sous les
        # moteurs qui ignorent le spatial, ce qui rend le referentiel des
        # chantiers testable hors PostgreSQL.
        geom = f"SRID=4326;POINT({data.longitude} {data.latitude})"
    chantier = models.Chantier(
        nom=data.nom, commune=data.commune, geom=geom,
        rayon_influence_m=data.rayon_influence_m or 1500,
    )
    db.add(chantier)
    db.commit()
    db.refresh(chantier)
    return _serialize_chantier(chantier)


@router.patch("/{chantier_id}", response_model=schemas.ChantierOut)
def modifier_chantier(chantier_id: int, data: schemas.ChantierCreate, db: Session = Depends(get_db), _: models.Utilisateur = Depends(_parametrage_metier)):
    chantier = db.query(models.Chantier).filter(models.Chantier.id == chantier_id).first()
    if not chantier:
        raise HTTPException(status_code=404, detail="Chantier introuvable")
    chantier.nom = data.nom
    chantier.commune = data.commune
    if data.rayon_influence_m is not None:
        chantier.rayon_influence_m = data.rayon_influence_m
    if data.latitude is not None and data.longitude is not None:
        chantier.geom = f"SRID=4326;POINT({data.longitude} {data.latitude})"
    db.commit()
    db.refresh(chantier)
    return _serialize_chantier(chantier)


@router.delete("/{chantier_id}")
def supprimer_chantier(chantier_id: int, db: Session = Depends(get_db), _: models.Utilisateur = Depends(_parametrage_metier)):
    chantier = db.query(models.Chantier).filter(models.Chantier.id == chantier_id).first()
    if not chantier:
        raise HTTPException(status_code=404, detail="Chantier introuvable")
    if db.query(models.Signalement).filter(models.Signalement.chantier_id == chantier_id).first():
        raise HTTPException(status_code=409, detail="Impossible de supprimer un chantier lié à des signalements")
    db.delete(chantier)
    db.commit()
    return {"message": "Chantier supprimé"}
