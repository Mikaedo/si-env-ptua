from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services import modele_service

router = APIRouter(prefix="/admin", tags=["Administration"])


def _admin_only(courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    if courant.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur")
    return courant


def _parametrage_metier(courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    """Profils habilites a definir les seuils de surveillance.

    Fixer la valeur a partir de laquelle une concentration de dioxyde d'azote
    devient preoccupante releve d'une appreciation environnementale, pas d'une
    competence d'exploitation informatique. Ce parametrage revient donc au
    specialiste du suivi environnemental, qui en repond devant l'ANDE et le
    bailleur. L'administrateur conserve l'acces au titre de la continuite de
    service, mais il n'est plus le seul, ni le destinataire naturel de cette
    responsabilite.
    """
    autorises = (models.RoleEnum.SPEC_ENV, models.RoleEnum.ADMIN)
    if courant.role not in autorises:
        raise HTTPException(
            status_code=403,
            detail="Le paramétrage environnemental relève du spécialiste du suivi environnemental.",
        )
    return courant


def _journal(db: Session, message: str, utilisateur: models.Utilisateur, niveau: str = "INFO"):
    db.add(models.Journal(niveau=niveau, message=message, utilisateur=utilisateur.email))


@router.get("/users", response_model=list[schemas.UtilisateurOut])
def lister_utilisateurs(
    db: Session = Depends(get_db),
    _: models.Utilisateur = Depends(_admin_only),
    page: int = 1, taille: int = 50,
):
    """Liste paginee des utilisateurs. Pagination simple offset/limite ;
    convient a l'echelle du PTUA (quelques centaines de comptes max)."""
    page = max(1, page); taille = min(max(1, taille), 200)
    return (
        db.query(models.Utilisateur)
        .order_by(models.Utilisateur.cree_le.desc())
        .offset((page - 1) * taille).limit(taille).all()
    )


@router.get("/logs", response_model=list[schemas.JournalOut])
def lister_journaux(
    db: Session = Depends(get_db),
    _: models.Utilisateur = Depends(_admin_only),
    page: int = 1, taille: int = 100,
):
    page = max(1, page); taille = min(max(1, taille), 500)
    return (
        db.query(models.Journal)
        .order_by(models.Journal.cree_le.desc())
        .offset((page - 1) * taille).limit(taille).all()
    )


@router.get("/erreurs", response_model=list[schemas.ErreurAppOut])
def lister_erreurs(
    db: Session = Depends(get_db),
    _: models.Utilisateur = Depends(_admin_only),
    page: int = 1, taille: int = 50,
):
    """Historique des exceptions applicatives capturees par le middleware.
    Utile pour identifier les problemes en production sans passer par les
    logs Render (equivalent Sentry embarque)."""
    page = max(1, page); taille = min(max(1, taille), 200)
    return (
        db.query(models.ErreurApp)
        .order_by(models.ErreurApp.survenue_le.desc())
        .offset((page - 1) * taille).limit(taille).all()
    )


@router.get("/model", response_model=dict)
def statut_modele(_: models.Utilisateur = Depends(_admin_only)):
    return modele_service.toutes_les_infos()


@router.post("/model", response_model=dict)
def deployer_modele(
    type_modele: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(_admin_only),
):
    if type_modele not in modele_service.NOMS_FICHIERS:
        raise HTTPException(status_code=400, detail="type_modele doit être 'detection' ou 'classification'")
    if not file.filename or not file.filename.lower().endswith(".onnx"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .onnx sont acceptés")
    destination = modele_service.chemin_modele(type_modele)
    destination.write_bytes(file.file.read())
    _journal(db, f"Déploiement du modèle IA ({type_modele}) : {file.filename}", courant)
    db.commit()
    return {"message": "Modèle déployé", "type_modele": type_modele, **modele_service.info_modele(type_modele)}


@router.get("/seuils", response_model=list[schemas.AlerteSeuilOut])
def lister_seuils(db: Session = Depends(get_db), _: models.Utilisateur = Depends(_parametrage_metier)):
    return db.query(models.AlerteSeuil).order_by(models.AlerteSeuil.indicateur).all()


@router.post("/seuils", response_model=schemas.AlerteSeuilOut)
def creer_seuil(
    data: schemas.AlerteSeuilCreate,
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(_parametrage_metier),
):
    seuil = models.AlerteSeuil(**data.model_dump())
    db.add(seuil)
    _journal(db, f"Création du seuil {data.indicateur} à {data.seuil}", courant)
    db.commit()
    db.refresh(seuil)
    return seuil


@router.patch("/seuils/{seuil_id}", response_model=schemas.AlerteSeuilOut)
def modifier_seuil(
    seuil_id: int,
    data: schemas.AlerteSeuilCreate,
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(_parametrage_metier),
):
    seuil = db.query(models.AlerteSeuil).filter(models.AlerteSeuil.id == seuil_id).first()
    if not seuil:
        raise HTTPException(status_code=404, detail="Seuil introuvable")
    for key, value in data.model_dump().items():
        setattr(seuil, key, value)
    _journal(db, f"Modification du seuil {seuil.indicateur}", courant)
    db.commit()
    db.refresh(seuil)
    return seuil


@router.delete("/seuils/{seuil_id}")
def supprimer_seuil(
    seuil_id: int,
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(_parametrage_metier),
):
    seuil = db.query(models.AlerteSeuil).filter(models.AlerteSeuil.id == seuil_id).first()
    if not seuil:
        raise HTTPException(status_code=404, detail="Seuil introuvable")
    _journal(db, f"Suppression du seuil {seuil.indicateur}", courant)
    db.delete(seuil)
    db.commit()
    return {"message": "Seuil supprimé"}


@router.patch("/users/{user_id}", response_model=schemas.UtilisateurOut)
def modifier_utilisateur(
    user_id: int,
    data: schemas.UtilisateurUpdate,
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(_admin_only),
):
    user = db.query(models.Utilisateur).filter(models.Utilisateur.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if data.role:
        user.role = data.role
    if data.nom is not None:
        user.nom = data.nom
    _journal(db, f"Modification de l'utilisateur {user.email} (rôle: {user.role.value})", courant)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def supprimer_utilisateur(
    user_id: int,
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(_admin_only),
):
    user = db.query(models.Utilisateur).filter(models.Utilisateur.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if user.id == courant.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte")
    _journal(db, f"Suppression de l'utilisateur {user.email}", courant)
    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé"}
