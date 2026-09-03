"""
signalements_router.py
----------------------
Endpoints pour gerer les SIGNALEMENTS terrain :
- POST   /signalements              : creer/synchroniser un signalement
- GET    /signalements              : lister avec filtres (statut, criticite, type, chantier, periode)
- GET    /signalements/{id}         : detail d'un signalement
- PATCH  /signalements/{id}/statut  : changer le statut
- POST   /signalements/{id}/action  : ajouter une action corrective
- POST   /signalements/{id}/retour  : retourner un signalement incomplet a l'agent
- POST   /signalements/{id}/photos  : uploader une photo
- GET    /signalements/{id}/photos  : lister les photos d'un signalement
"""
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.shape import to_shape

from .. import models, schemas, auth
from ..database import get_db
from ..services import photo_storage

router = APIRouter(prefix="/signalements", tags=["Signalements"])


def _geom_payload(geom):
    if not geom:
        return None
    try:
        point = to_shape(geom)
        return {"type": "Point", "coordinates": (point.x, point.y)}
    except Exception:
        value = str(geom)
        if value.upper().startswith("POINT"):
            coords = value[value.find("(") + 1:value.rfind(")")].split()
            if len(coords) == 2:
                return {"type": "Point", "coordinates": (float(coords[0]), float(coords[1]))}
    return None


def _serialize_signalement(signalement: models.Signalement):
    return {
        "id": signalement.id,
        "uuid_mobile": signalement.uuid_mobile,
        "type_nuisance": signalement.type_nuisance,
        "description": signalement.description,
        "criticite": signalement.criticite,
        "criticite_ia": signalement.criticite_ia,
        "confiance_ia": signalement.confiance_ia,
        "gps_source": signalement.gps_source,
        "statut": signalement.statut,
        "cree_le": signalement.cree_le,
        "auteur_id": signalement.auteur_id,
        "chantier_id": signalement.chantier_id,
        "geom": _geom_payload(signalement.geom),
        "auteur": ({"id": signalement.auteur.id, "nom": signalement.auteur.nom, "email": signalement.auteur.email}
                   if signalement.auteur else None),
        "chantier": ({"id": signalement.chantier.id, "nom": signalement.chantier.nom, "commune": signalement.chantier.commune}
                     if signalement.chantier else None),
        "photos": [{"id": photo.id, "chemin": photo.chemin, "signalement_id": photo.signalement_id}
                   for photo in signalement.photos],
        "actions": [{"id": a.id, "description": a.description, "echeance": a.echeance,
                    "cree_le": a.cree_le, "signalement_id": a.signalement_id}
                   for a in signalement.actions],
    }


@router.post("", response_model=schemas.SignalementOut)
def creer_signalement(data: schemas.SignalementCreate,
                      db: Session = Depends(get_db),
                      courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    existant = db.query(models.Signalement).filter(
        models.Signalement.uuid_mobile == data.uuid_mobile).first()
    if existant:
        return _serialize_signalement(existant)

    if db.bind.dialect.name == "sqlite":
        geom_value = f"POINT({data.longitude} {data.latitude})"
    else:
        geom_value = func.ST_SetSRID(func.ST_MakePoint(data.longitude, data.latitude), 4326)

    signalement = models.Signalement(
        uuid_mobile=data.uuid_mobile,
        type_nuisance=data.type_nuisance,
        description=data.description,
        criticite=data.criticite,
        criticite_ia=data.criticite_ia,
        confiance_ia=data.confiance_ia,
        gps_source=data.gps_source,
        geom=geom_value,
        auteur_id=courant.id,
        chantier_id=data.chantier_id,
    )
    db.add(signalement)
    db.commit()
    db.refresh(signalement)
    return _serialize_signalement(signalement)


def _valider_enumere(valeur: str, enumere, libelle: str) -> str:
    """Refuse une valeur de filtre hors de l'enumere, avec un 422.

    Sans cette verification, une valeur inconnue partait telle quelle
    dans la clause WHERE et PostgreSQL levait un DataError, que le
    gestionnaire d'exceptions traduisait en 500. Un filtre errone est
    une faute du client, non une panne du serveur : il merite un 422
    qui nomme les valeurs admises.
    """
    admises = {membre.value for membre in enumere}
    if valeur not in admises:
        raise HTTPException(
            status_code=422,
            detail=f"{libelle} invalide : « {valeur} ». "
                   f"Valeurs admises : {', '.join(sorted(admises))}.")
    return valeur


@router.get("", response_model=list[schemas.SignalementOut])
def lister_signalements(
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(auth.utilisateur_courant),
    statut: str = Query(None),
    criticite: str = Query(None),
    type_nuisance: str = Query(None),
    chantier_id: int = Query(None),
    periode_jours: int = Query(None),
):
    # Le riverain n'a pas a voir les signalements de terrain : il ne
    # depose que des doleances, et les consulte sur /citoyen/doleances.
    # Lui ouvrir cette liste lui montrerait les constats des agents sur
    # tous les chantiers du programme.
    if courant.role == models.RoleEnum.PLAIGNANT:
        raise HTTPException(
            status_code=403,
            detail="Consultez vos doléances sur /citoyen/doleances.")

    q = db.query(models.Signalement)
    # RBAC: RESP_ENV only sees their own signalements
    if courant.role == models.RoleEnum.RESP_ENV:
        q = q.filter(models.Signalement.auteur_id == courant.id)
    if statut:
        _valider_enumere(statut, models.StatutSignalement, "Statut")
        q = q.filter(models.Signalement.statut == statut)
    if criticite:
        _valider_enumere(criticite, models.CriticiteEnum, "Criticité")
        q = q.filter(models.Signalement.criticite == criticite)
    if type_nuisance:
        q = q.filter(models.Signalement.type_nuisance.ilike(f"%{type_nuisance}%"))
    if chantier_id:
        q = q.filter(models.Signalement.chantier_id == chantier_id)
    if periode_jours:
        date_limite = datetime.utcnow() - timedelta(days=periode_jours)
        q = q.filter(models.Signalement.cree_le >= date_limite)
    return [_serialize_signalement(s) for s in q.order_by(models.Signalement.cree_le.desc()).all()]


@router.get("/{signalement_id}", response_model=schemas.SignalementOut)
def detail_signalement(signalement_id: int,
                       db: Session = Depends(get_db),
                       courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    s = db.query(models.Signalement).filter(models.Signalement.id == signalement_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Signalement introuvable")
    return _serialize_signalement(s)


@router.patch("/{signalement_id}/statut", response_model=schemas.SignalementOut)
def changer_statut(signalement_id: int,
                   data: schemas.SignalementStatutUpdate | None = None,
                   nouveau_statut: models.StatutSignalement | None = Query(None),
                   db: Session = Depends(get_db),
                   courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    if courant.role not in (models.RoleEnum.SPEC_ENV, models.RoleEnum.EXPERT_HSE):
        raise HTTPException(status_code=403, detail="Traitement réservé aux profils habilités")
    s = db.query(models.Signalement).filter(models.Signalement.id == signalement_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Signalement introuvable")
    statut = data.statut if data else nouveau_statut
    if statut is None:
        raise HTTPException(status_code=422, detail="Le nouveau statut est obligatoire")

    # Un signalement ne se cloture pas sans qu'on sache ce qui a ete fait
    # pour le resoudre. La procedure decrite au chapitre de la conception
    # va du constat a la cloture en passant par une action corrective :
    # sans ce controle, l'ecran permettait de sauter cette etape et le
    # dossier ne gardait aucune trace du traitement.
    if statut == models.StatutSignalement.CLOTURE:
        # Un motif de rejet est lui aussi consigne comme action : il ne
        # vaut pas traitement et ne doit donc pas ouvrir la cloture.
        action = (db.query(models.ActionCorrective)
                  .filter(models.ActionCorrective.signalement_id == signalement_id)
                  .filter(~models.ActionCorrective.description.like(
                      "Signalement retourné à l'agent.%"))
                  .first())
        if action is None:
            raise HTTPException(
                status_code=409,
                detail="Enregistrez d'abord l'action corrective menée : "
                       "un signalement ne peut être clôturé sans elle.")

    s.statut = statut
    db.commit()
    db.refresh(s)
    return _serialize_signalement(s)


@router.post("/{signalement_id}/action", response_model=schemas.ActionCorrectiveOut)
def ajouter_action(signalement_id: int,
                   data: schemas.ActionCorrectiveCreate,
                   db: Session = Depends(get_db),
                   courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    if courant.role not in (models.RoleEnum.SPEC_ENV, models.RoleEnum.EXPERT_HSE):
        raise HTTPException(status_code=403, detail="Action réservée aux profils habilités")
    s = db.query(models.Signalement).filter(models.Signalement.id == signalement_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Signalement introuvable")
    action = models.ActionCorrective(
        description=data.description,
        echeance=data.echeance,
        signalement_id=signalement_id,
    )
    db.add(action)
    s.statut = models.StatutSignalement.EN_TRAITEMENT
    db.commit()
    db.refresh(action)
    return action


@router.post("/{signalement_id}/retour", response_model=schemas.SignalementOut)
def retourner_agent(signalement_id: int,
                    data: schemas.RetourAgent,
                    db: Session = Depends(get_db),
                    courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    if courant.role not in (models.RoleEnum.SPEC_ENV, models.RoleEnum.EXPERT_HSE):
        raise HTTPException(status_code=403, detail="Retour réservé aux profils habilités")
    s = db.query(models.Signalement).filter(models.Signalement.id == signalement_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Signalement introuvable")
    # Le motif etait jusqu'ici prefixe a la description, ce qui alterait
    # le constat ecrit par l'agent sur le terrain et s'empilait a chaque
    # rejet. Il est desormais consigne comme une decision datee, au meme
    # titre qu'une action corrective : la description reste intacte et le
    # dossier garde l'historique de ce qui a ete decide.
    db.add(models.ActionCorrective(
        description=f"Signalement retourné à l'agent. Motif : {data.motif}",
        signalement_id=signalement_id,
    ))
    s.statut = models.StatutSignalement.REJETE
    db.commit()
    db.refresh(s)
    return _serialize_signalement(s)


@router.post("/{signalement_id}/photos")
def upload_photo(signalement_id: int,
                 file: UploadFile = File(...),
                 db: Session = Depends(get_db),
                 courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    s = db.query(models.Signalement).filter(models.Signalement.id == signalement_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Signalement introuvable")

    nom = photo_storage.nom_unique(signalement_id, file.filename or "photo.jpg")
    chemin = photo_storage.backend.enregistrer(nom, file.file.read())

    photo = models.Photo(chemin=chemin, signalement_id=signalement_id)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return {"id": photo.id, "chemin": chemin, "signalement_id": signalement_id}


@router.get("/{signalement_id}/photos")
def lister_photos(signalement_id: int,
                  db: Session = Depends(get_db),
                  courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    photos = db.query(models.Photo).filter(models.Photo.signalement_id == signalement_id).all()
    return [{"id": p.id, "chemin": p.chemin, "signalement_id": p.signalement_id} for p in photos]
