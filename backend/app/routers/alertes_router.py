"""
alertes_router.py
-----------------
- GET /alertes          : lister les alertes de l'utilisateur
- POST /alertes/{id}/accuser : accuser reception d'une alerte
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/alertes", tags=["Alertes"])


def _serialize_alerte(alerte: models.Alerte, db: Session):
    chantier = db.query(models.Chantier).filter(models.Chantier.id == alerte.chantier_id).first() if alerte.chantier_id else None
    return {
        "id": alerte.id,
        "message": alerte.message,
        "niveau": alerte.niveau,
        "valeur": alerte.valeur,
        "cree_le": alerte.cree_le,
        "chantier_id": alerte.chantier_id,
        "chantier": ({"id": chantier.id, "nom": chantier.nom, "commune": chantier.commune} if chantier else None),
        "recue": alerte.recue,
    }


@router.get("", response_model=list[schemas.AlerteOut])
def lister_alertes(db: Session = Depends(get_db),
                   courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    alertes = db.query(models.Alerte).order_by(models.Alerte.cree_le.desc()).all()
    return [_serialize_alerte(alerte, db) for alerte in alertes]


@router.post("/{alerte_id}/accuser", response_model=schemas.AlerteOut)
def accuser_reception(alerte_id: int,
                      db: Session = Depends(get_db),
                      courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    a = db.query(models.Alerte).filter(models.Alerte.id == alerte_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    a.recue = True
    a.utilisateur_id = courant.id
    db.commit()
    db.refresh(a)
    return _serialize_alerte(a, db)
