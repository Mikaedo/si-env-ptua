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


@router.post("/{plainte_id}/action", response_model=schemas.ActionCorrectiveOut)
def ajouter_action_plainte(
    plainte_id: int,
    data: schemas.ActionCorrectiveCreate,
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(_require_plainte_role),
):
    """Meme principe que pour un signalement (paragraphe precedent) : la
    plainte disposait d'un statut qui basculait sans laisser de trace de ce
    qui avait ete fait. Enregistrer l'action, avec son echeance, et faire
    passer la plainte « en cours » du meme geste."""
    plainte = db.query(models.Plainte).filter(models.Plainte.id == plainte_id).first()
    if not plainte:
        raise HTTPException(status_code=404, detail="Plainte introuvable")
    action = models.ActionCorrective(
        description=data.description,
        echeance=data.echeance,
        plainte_id=plainte_id,
    )
    db.add(action)
    plainte.statut = "EN_COURS"
    db.commit()
    db.refresh(action)
    return action


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

    # Une plainte se clot sur un traitement, non sur un simple changement
    # de statut. Le mecanisme de gestion des plaintes suppose qu'on puisse
    # dire au plaignant ce qui a ete fait : sans action enregistree, la
    # reponse qu'on lui doit reste introuvable.
    if data.statut == "RESOLU":
        action = (db.query(models.ActionCorrective)
                  .filter(models.ActionCorrective.plainte_id == plainte_id)
                  .first())
        if action is None:
            raise HTTPException(
                status_code=409,
                detail="Enregistrez d'abord le traitement apporté : "
                       "une plainte ne peut être résolue sans réponse au plaignant.")

    plainte.statut = data.statut
    db.commit()
    db.refresh(plainte)
    return plainte
