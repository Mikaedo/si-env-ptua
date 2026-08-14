from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/plaintes", tags=["Plaintes"])


def _require_plainte_role(courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    """Profils habilites a instruire une plainte."""
    if courant.role not in (models.RoleEnum.SPEC_PAR, models.RoleEnum.ADMIN):
        raise HTTPException(status_code=403, detail="Accès réservé au suivi P.A.R")
    return courant


def _require_lecture_plainte(courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    """Profils habilites a consulter la file des plaintes.

    La Banque Africaine de Developpement s'y ajoute parce que le traitement des
    doleances releve directement de sa sauvegarde operationnelle relative a la
    reinstallation : c'est une piece qu'elle doit pouvoir verifier. L'Agence
    Nationale de l'Environnement, dont le mandat porte sur la conformite
    environnementale, n'y a en revanche pas acces.
    """
    autorises = (
        models.RoleEnum.SPEC_PAR,
        models.RoleEnum.ADMIN,
        models.RoleEnum.BAD,
    )
    if courant.role not in autorises:
        raise HTTPException(status_code=403, detail="Accès réservé au suivi P.A.R")
    return courant


@router.get("", response_model=list[schemas.PlainteOut])
def lister_plaintes(
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(_require_lecture_plainte),
):
    return db.query(models.Plainte).order_by(models.Plainte.cree_le.desc()).all()


@router.post("", response_model=schemas.PlainteOut)
def creer_plainte(
    data: schemas.PlainteCreate,
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(_require_plainte_role),
):
    plainte = models.Plainte(**data.model_dump())
    db.add(plainte)
    db.commit()
    db.refresh(plainte)
    return plainte


@router.patch("/{plainte_id}/statut", response_model=schemas.PlainteOut)
def modifier_statut_plainte(
    plainte_id: int,
    data: schemas.PlainteStatutUpdate,
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(_require_plainte_role),
):
    if data.statut not in {"OUVERTE", "EN_COURS", "RESOLU", "REJETE"}:
        raise HTTPException(status_code=400, detail="Statut de plainte invalide")
    plainte = db.query(models.Plainte).filter(models.Plainte.id == plainte_id).first()
    if not plainte:
        raise HTTPException(status_code=404, detail="Plainte introuvable")
    plainte.statut = data.statut
    db.commit()
    db.refresh(plainte)
    return plainte
