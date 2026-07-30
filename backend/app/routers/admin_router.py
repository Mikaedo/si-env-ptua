from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/admin", tags=["Administration"])
MODEL_DIR = Path(__file__).resolve().parents[2] / "uploads" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def _admin_only(courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    if courant.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur")
    return courant


def _journal(db: Session, message: str, utilisateur: models.Utilisateur, niveau: str = "INFO"):
    db.add(models.Journal(niveau=niveau, message=message, utilisateur=utilisateur.email))


@router.get("/users", response_model=list[schemas.UtilisateurOut])
def lister_utilisateurs(db: Session = Depends(get_db), _: models.Utilisateur = Depends(_admin_only)):
    return db.query(models.Utilisateur).order_by(models.Utilisateur.cree_le.desc()).all()


@router.get("/logs", response_model=list[schemas.JournalOut])
def lister_journaux(db: Session = Depends(get_db), _: models.Utilisateur = Depends(_admin_only)):
    return db.query(models.Journal).order_by(models.Journal.cree_le.desc()).limit(500).all()


@router.get("/model", response_model=dict)
def statut_modele(_: models.Utilisateur = Depends(_admin_only)):
    models_files = sorted(MODEL_DIR.glob("*.onnx"), key=lambda path: path.stat().st_mtime, reverse=True)
    current = models_files[0] if models_files else None
    return {
        "nom": current.name if current else "Aucun modèle déployé",
        "taille_octets": current.stat().st_size if current else 0,
        "deploye_le": datetime.fromtimestamp(current.stat().st_mtime).isoformat() if current else None,
    }


@router.post("/model", response_model=dict)
def deployer_modele(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(_admin_only),
):
    if not file.filename or not file.filename.lower().endswith(".onnx"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .onnx sont acceptés")
    safe_name = Path(file.filename).name
    destination = MODEL_DIR / safe_name
    destination.write_bytes(file.file.read())
    _journal(db, f"Déploiement du modèle IA {safe_name}", courant)
    db.commit()
    return {
        "message": "Modèle déployé",
        "nom": safe_name,
        "taille_octets": destination.stat().st_size,
        "deploye_le": datetime.fromtimestamp(destination.stat().st_mtime).isoformat(),
    }


@router.get("/seuils", response_model=list[schemas.AlerteSeuilOut])
def lister_seuils(db: Session = Depends(get_db), _: models.Utilisateur = Depends(_admin_only)):
    return db.query(models.AlerteSeuil).order_by(models.AlerteSeuil.indicateur).all()


@router.post("/seuils", response_model=schemas.AlerteSeuilOut)
def creer_seuil(
    data: schemas.AlerteSeuilCreate,
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(_admin_only),
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
    courant: models.Utilisateur = Depends(_admin_only),
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
    courant: models.Utilisateur = Depends(_admin_only),
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
