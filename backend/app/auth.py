"""
auth.py
-------
Gestion de la SECURITE : mots de passe et jetons JWT.

Notions simples :
- Hachage (bcrypt) : on transforme le mot de passe en une empreinte illisible.
  On ne peut pas revenir en arriere. Pour verifier, on re-hache et on compare.
- JWT (JSON Web Token) : une "carte d'acces" signee que le serveur remet apres
  une connexion reussie. Le client la presente a chaque requete pour prouver son identite.
"""
from datetime import datetime, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from . import models

# Contexte de hachage bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Indique a FastAPI ou le client obtient son jeton (endpoint /auth/login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hasher_mot_de_passe(mot_de_passe: str) -> str:
    """Transforme un mot de passe en empreinte securisee."""
    return pwd_context.hash(mot_de_passe)


def verifier_mot_de_passe(clair: str, hash_stocke: str) -> bool:
    """Verifie qu'un mot de passe correspond a l'empreinte enregistree."""
    return pwd_context.verify(clair, hash_stocke)


def creer_token(donnees: dict) -> str:
    """Cree un jeton JWT contenant l'identite de l'utilisateur et une date d'expiration."""
    a_encoder = donnees.copy()
    expiration = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    a_encoder.update({"exp": expiration})
    return jwt.encode(a_encoder, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def utilisateur_courant(token: str = Depends(oauth2_scheme),
                        db: Session = Depends(get_db)) -> models.Utilisateur:
    """
    Dependance de securite : lit le jeton envoye, le verifie, et retrouve l'utilisateur.
    Si le jeton est invalide ou expire, l'acces est refuse (401).
    A utiliser dans tout endpoint qui doit etre protege.
    """
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou session expiree",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        charge = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = charge.get("sub")
        if user_id is None:
            raise exception
    except JWTError:
        raise exception

    utilisateur = db.query(models.Utilisateur).filter(models.Utilisateur.id == int(user_id)).first()
    if utilisateur is None:
        raise exception
    return utilisateur


def roles_requis(*roles: models.RoleEnum):
    def verifier_role(courant: models.Utilisateur = Depends(utilisateur_courant)) -> models.Utilisateur:
        if courant.role not in roles:
            raise HTTPException(status_code=403, detail="Permissions insuffisantes pour ce profil")
        return courant

    return verifier_role
