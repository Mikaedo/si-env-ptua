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
    return {"id": chantier.id, "nom": chantier.nom, "commune": chantier.commune, "geom": geom}


def _admin_only(courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    if courant.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur")
    return courant


@router.get("", response_model=list[schemas.ChantierOut])
def lister_chantiers(db: Session = Depends(get_db),
                     courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    return [_serialize_chantier(c) for c in db.query(models.Chantier).order_by(models.Chantier.nom).all()]


@router.post("", response_model=schemas.ChantierOut)
def creer_chantier(data: schemas.ChantierCreate, db: Session = Depends(get_db), _: models.Utilisateur = Depends(_admin_only)):
    geom = None
    if data.latitude is not None and data.longitude is not None:
        geom = func.ST_SetSRID(func.ST_MakePoint(data.longitude, data.latitude), 4326)
    chantier = models.Chantier(nom=data.nom, commune=data.commune, geom=geom)
    db.add(chantier)
    db.commit()
    db.refresh(chantier)
    return _serialize_chantier(chantier)


@router.patch("/{chantier_id}", response_model=schemas.ChantierOut)
def modifier_chantier(chantier_id: int, data: schemas.ChantierCreate, db: Session = Depends(get_db), _: models.Utilisateur = Depends(_admin_only)):
    chantier = db.query(models.Chantier).filter(models.Chantier.id == chantier_id).first()
    if not chantier:
        raise HTTPException(status_code=404, detail="Chantier introuvable")
    chantier.nom = data.nom
    chantier.commune = data.commune
    if data.latitude is not None and data.longitude is not None:
        chantier.geom = func.ST_SetSRID(func.ST_MakePoint(data.longitude, data.latitude), 4326)
    db.commit()
    db.refresh(chantier)
    return _serialize_chantier(chantier)


@router.delete("/{chantier_id}")
def supprimer_chantier(chantier_id: int, db: Session = Depends(get_db), _: models.Utilisateur = Depends(_admin_only)):
    chantier = db.query(models.Chantier).filter(models.Chantier.id == chantier_id).first()
    if not chantier:
        raise HTTPException(status_code=404, detail="Chantier introuvable")
    if db.query(models.Signalement).filter(models.Signalement.chantier_id == chantier_id).first():
        raise HTTPException(status_code=409, detail="Impossible de supprimer un chantier lié à des signalements")
    db.delete(chantier)
    db.commit()
    return {"message": "Chantier supprimé"}
