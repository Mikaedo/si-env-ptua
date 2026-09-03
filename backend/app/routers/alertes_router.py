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
    auteur = (db.query(models.Utilisateur)
              .filter(models.Utilisateur.id == alerte.utilisateur_id).first()
              if alerte.utilisateur_id else None)
    return {
        "id": alerte.id,
        "message": alerte.message,
        "niveau": alerte.niveau,
        "valeur": alerte.valeur,
        "cree_le": alerte.cree_le,
        "chantier_id": alerte.chantier_id,
        "chantier": ({"id": chantier.id, "nom": chantier.nom, "commune": chantier.commune} if chantier else None),
        "recue": alerte.recue,
        "recue_par": auteur.nom if auteur else None,
    }


@router.get("", response_model=list[schemas.AlerteOut])
def lister_alertes(db: Session = Depends(get_db),
                   courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    alertes = db.query(models.Alerte).order_by(models.Alerte.cree_le.desc()).all()

    # Une requete par alerte pour retrouver son chantier rendait cet endpoint
    # tres lent des que la liste grossissait (N+1). Les chantiers necessaires
    # sont desormais recuperes en un seul aller-retour, par lot.
    ids_chantiers = {a.chantier_id for a in alertes if a.chantier_id}
    chantiers_par_id = {
        c.id: c for c in (
            db.query(models.Chantier).filter(models.Chantier.id.in_(ids_chantiers)).all()
            if ids_chantiers else []
        )
    }

    # Les auteurs des accuses de reception sont charges de la meme facon,
    # en un seul aller-retour : les resoudre alerte par alerte aurait
    # ramene la lenteur que le regroupement ci-dessus vient d'ecarter.
    ids_auteurs = {a.utilisateur_id for a in alertes if a.utilisateur_id}
    auteurs_par_id = {
        u.id: u for u in (
            db.query(models.Utilisateur).filter(models.Utilisateur.id.in_(ids_auteurs)).all()
            if ids_auteurs else []
        )
    }

    def serialiser(alerte):
        chantier = chantiers_par_id.get(alerte.chantier_id)
        auteur = auteurs_par_id.get(alerte.utilisateur_id)
        return {
            "id": alerte.id,
            "message": alerte.message,
            "niveau": alerte.niveau,
            "valeur": alerte.valeur,
            "cree_le": alerte.cree_le,
            "chantier_id": alerte.chantier_id,
            "chantier": ({"id": chantier.id, "nom": chantier.nom, "commune": chantier.commune}
                        if chantier else None),
            "recue": alerte.recue,
            "recue_par": auteur.nom if auteur else None,
        }

    return [serialiser(a) for a in alertes]


@router.post("/{alerte_id}/accuser", response_model=schemas.AlerteOut)
def accuser_reception(alerte_id: int,
                      db: Session = Depends(get_db),
                      courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    # « Reception et revue des alertes » est ouverte a tous les profils
    # operationnels : accuser reception retire l'alerte du compteur des
    # non lues, c'est un geste de lecture, non une decision de gestion.
    # L'agence de tutelle et le bailleur, eux, n'y ont que la lecture :
    # toute ecriture emise avec leur jeton doit etre rejetee par le
    # serveur, non simplement masquee dans l'interface. L'endpoint
    # n'imposait jusqu'ici aucune restriction, qu'un appel direct
    # contournait.
    if courant.role in models.ROLES_LECTURE_SEULE:
        raise HTTPException(
            status_code=403,
            detail="Votre profil suit le programme en consultation : "
                   "toute écriture est refusée.")
    a = db.query(models.Alerte).filter(models.Alerte.id == alerte_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    a.recue = True
    a.utilisateur_id = courant.id
    db.commit()
    db.refresh(a)
    return _serialize_alerte(a, db)
