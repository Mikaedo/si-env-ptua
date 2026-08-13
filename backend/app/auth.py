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
import secrets
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

# Duree du refresh token en jours. Un refresh permet d'obtenir un nouveau
# access sans re-saisir le mot de passe, tant qu'il n'est pas revoque.
REFRESH_TOKEN_DUREE_JOURS = 7


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


def emettre_refresh_token(db: Session, utilisateur: models.Utilisateur) -> str:
    """Emet un refresh token opaque, le persiste et le retourne au client.

    Le token est un secret aleatoire (pas un JWT), stocke en clair : sa
    presence en base est necessaire pour verification et permet la revocation
    immediate a la deconnexion. La table est purgee des entrees expirees.
    """
    _purger_refresh_tokens(db)
    jeton = secrets.token_urlsafe(48)
    expire_le = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_DUREE_JOURS)
    db.add(models.RefreshToken(
        utilisateur_id=utilisateur.id, jeton=jeton, expire_le=expire_le
    ))
    db.commit()
    return jeton


def echanger_refresh_token(db: Session, jeton: str) -> tuple[str, models.Utilisateur]:
    """Valide un refresh token et retourne un nouveau access token.

    Le refresh reste actif jusqu'a expiration ou revocation explicite. Une
    strategie plus stricte serait de le remplacer a chaque echange (rotation),
    mais elle complique le mobile hors ligne : on garde l'approche simple.
    """
    entree = db.query(models.RefreshToken).filter(
        models.RefreshToken.jeton == jeton,
        models.RefreshToken.revoque.is_(False),
        models.RefreshToken.expire_le >= datetime.utcnow(),
    ).first()
    if not entree:
        raise HTTPException(status_code=401, detail="Refresh token invalide ou expire")
    utilisateur = db.query(models.Utilisateur).filter(
        models.Utilisateur.id == entree.utilisateur_id
    ).first()
    if not utilisateur:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    access = creer_token({"sub": str(utilisateur.id), "role": utilisateur.role.value})
    return access, utilisateur


def revoquer_refresh_token(db: Session, jeton: str) -> None:
    """Marque un refresh token comme revoque (deconnexion)."""
    db.query(models.RefreshToken).filter(
        models.RefreshToken.jeton == jeton
    ).update({"revoque": True})
    db.commit()


def _purger_refresh_tokens(db: Session) -> None:
    """Supprime les tokens expires depuis plus de 24 h."""
    limite = datetime.utcnow() - timedelta(hours=24)
    db.query(models.RefreshToken).filter(
        models.RefreshToken.expire_le < limite
    ).delete()
    db.commit()


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
