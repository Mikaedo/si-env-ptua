"""
schemas.py
----------
Schemas Pydantic : structure des messages JSON echanges avec le client.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from .models import RoleEnum, StatutSignalement, CriticiteEnum


# ---------- Utilisateur ----------
class UtilisateurCreate(BaseModel):
    nom: Optional[str] = None
    email: EmailStr
    role: RoleEnum = RoleEnum.RESP_ENV
    telephone: Optional[str] = None


class UtilisateurUpdate(BaseModel):
    nom: Optional[str] = None
    role: Optional[RoleEnum] = None


class UtilisateurOut(BaseModel):
    id: int
    nom: Optional[str] = None
    email: EmailStr
    role: RoleEnum
    premiere_connexion: bool
    telephone: Optional[str] = None
    cree_le: datetime

    class Config:
        from_attributes = True


class SetPassword(BaseModel):
    mot_de_passe: str


class FirstLoginComplete(BaseModel):
    nom: str
    telephone: Optional[str] = None
    mot_de_passe: str


class ChangePassword(BaseModel):
    ancien_mot_de_passe: str
    nouveau_mot_de_passe: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyCode(BaseModel):
    email: EmailStr
    code: str


class ResetPassword(BaseModel):
    email: EmailStr
    code: str
    nouveau_mot_de_passe: str


# ---------- Authentification ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    premiere_connexion: bool = False
    role: Optional[str] = None
    # Refresh token opaque : le client le renvoie sur /auth/refresh pour
    # obtenir un nouvel access sans re-saisir le mot de passe.
    refresh_token: Optional[str] = None
    # 2FA : quand le compte a la 2FA activee, /auth/login renvoie ces deux
    # champs sans access_token, et le client doit poster le code sur
    # /auth/2fa/verifier pour obtenir enfin le vrai jeton.
    twofa_requis: bool = False
    twofa_email: Optional[EmailStr] = None


class LoginInput(BaseModel):
    email: EmailStr
    mot_de_passe: str


class RefreshInput(BaseModel):
    refresh_token: str


class TwoFactorVerify(BaseModel):
    email: EmailStr
    code: str


class TwoFactorConfig(BaseModel):
    actif: bool


# ---------- Erreurs applicatives ----------
class ErreurAppOut(BaseModel):
    id: int
    survenue_le: datetime
    methode: Optional[str] = None
    chemin: Optional[str] = None
    utilisateur: Optional[str] = None
    ip_source: Optional[str] = None
    type_erreur: Optional[str] = None
    message: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Pagination ----------
class Page(BaseModel):
    """Enveloppe standard pour les listes paginees."""
    total: int
    page: int
    taille: int
    resultats: list


# ---------- Signalement ----------
class SignalementCreate(BaseModel):
    uuid_mobile: str
    type_nuisance: str
    description: Optional[str] = None
    criticite: CriticiteEnum = CriticiteEnum.FAIBLE
    criticite_ia: Optional[CriticiteEnum] = None
    confiance_ia: Optional[float] = None
    gps_source: str = "AUTO"
    latitude: float
    longitude: float
    chantier_id: Optional[int] = None


class GeoPoint(BaseModel):
    type: str = "Point"
    coordinates: tuple[float, float]


class UtilisateurResume(BaseModel):
    id: int
    nom: Optional[str] = None
    email: EmailStr


class ChantierResume(BaseModel):
    id: int
    nom: str
    commune: Optional[str] = None


class PhotoResume(BaseModel):
    id: int
    chemin: str
    signalement_id: int


class ActionCorrectiveCreate(BaseModel):
    description: str
    echeance: Optional[datetime] = None


class ActionCorrectiveOut(BaseModel):
    id: int
    description: str
    echeance: Optional[datetime]
    cree_le: datetime
    signalement_id: int

    class Config:
        from_attributes = True


class SignalementOut(BaseModel):
    id: int
    uuid_mobile: str
    type_nuisance: str
    description: Optional[str]
    criticite: CriticiteEnum
    criticite_ia: Optional[CriticiteEnum] = None
    confiance_ia: Optional[float] = None
    gps_source: str
    statut: StatutSignalement
    cree_le: datetime
    auteur_id: Optional[int]
    chantier_id: Optional[int]
    geom: Optional[GeoPoint] = None
    auteur: Optional[UtilisateurResume] = None
    chantier: Optional[ChantierResume] = None
    photos: List[PhotoResume] = []
    # Historique des actions correctives engagees, echeance comprise :
    # permet a l'ecran de detail d'afficher ce qui est fait pendant qu'un
    # signalement reste « en cours », pas seulement avant/apres ce statut.
    actions: List[ActionCorrectiveOut] = []

    class Config:
        from_attributes = True


class RetourAgent(BaseModel):
    motif: str


class SignalementStatutUpdate(BaseModel):
    statut: StatutSignalement


# ---------- Chantier ----------
class ChantierCreate(BaseModel):
    nom: str
    commune: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Etendue de la zone d'influence, en metres. Elle conditionne l'acces des
    # riverains a l'application citoyenne. A defaut, 1500 m, ordre de grandeur
    # d'une zone d'influence directe pour des travaux routiers urbains.
    rayon_influence_m: Optional[int] = Field(default=None, ge=100, le=500_000)


class ChantierOut(BaseModel):
    id: int
    nom: str
    commune: Optional[str]
    geom: Optional[GeoPoint] = None
    rayon_influence_m: Optional[int] = None

    class Config:
        from_attributes = True


# ---------- Alerte ----------
class AlerteOut(BaseModel):
    id: int
    message: str
    niveau: str
    valeur: Optional[float] = None
    cree_le: datetime
    chantier_id: Optional[int] = None
    chantier: Optional[ChantierResume] = None
    recue: bool = False

    class Config:
        from_attributes = True


class AlerteSeuilCreate(BaseModel):
    nom: str
    indicateur: str
    seuil: float
    niveau: str = "WARNING"
    actif: bool = True
    # Laisse vide, le seuil vaut pour tous les chantiers. Renseigne, il ne
    # s'applique qu'a celui-ci.
    chantier_id: Optional[int] = None


class AlerteSeuilOut(AlerteSeuilCreate):
    id: int
    cree_le: datetime

    class Config:
        from_attributes = True


# ---------- Plaintes ----------
class PlainteCreate(BaseModel):
    nom_plaignant: str
    contact: Optional[str] = None
    description: str
    chantier_id: Optional[int] = None


class PlainteOut(BaseModel):
    id: int
    nom_plaignant: str
    contact: Optional[str] = None
    description: str
    statut: str
    cree_le: datetime
    chantier_id: Optional[int] = None
    # Provenance et nature du depot. Le specialiste du suivi social a besoin
    # de savoir d'ou vient une doleance : celle qui arrive du telephone d'un
    # riverain n'appelle pas la meme reponse que celle recueillie au guichet,
    # ou un agent a pu preciser les circonstances de vive voix.
    canal: Optional[str] = None
    categorie: Optional[str] = None

    class Config:
        from_attributes = True


class PlainteStatutUpdate(BaseModel):
    statut: str


# ---------- Administration ----------
class JournalOut(BaseModel):
    id: int
    niveau: str
    message: str
    utilisateur: Optional[str] = None
    ip_source: Optional[str] = None
    cree_le: datetime

    class Config:
        from_attributes = True


# ---------- Statistiques ----------
class Statistiques(BaseModel):
    total: int
    traites: int
    en_attente: int
    urgents: int
    taux_traitement: float
    repartition: dict
    evolution: dict


# ---------- Application citoyenne ----------
class PositionGps(BaseModel):
    """Position relevee par le telephone du riverain."""
    latitude: float
    longitude: float


class ZoneVerifiee(BaseModel):
    """Verdict rendu avant l'inscription d'un riverain.

    On renvoie la distance et le rayon en plus du simple verdict : quand
    l'acces est refuse, la personne merite de savoir de combien elle se trouve
    hors du perimetre plutot que de se heurter a un refus sans explication.
    """
    autorise: bool
    chantier_id: int
    chantier_nom: str
    commune: Optional[str] = None
    distance_m: int
    rayon_m: int


class ChantierRattachement(BaseModel):
    """Chantier de rattachement, tel que l'application citoyenne l'affiche.

    Volontairement reduit au strict necessaire : l'ecran de profil montre un
    nom et une commune. Renvoyer la geometrie obligerait a une serialisation
    dediee pour une donnee que personne ne lit.
    """
    id: int
    nom: str
    commune: Optional[str] = None


class InscriptionCitoyen(BaseModel):
    nom: str
    email: EmailStr
    mot_de_passe: str = Field(min_length=8)
    telephone: Optional[str] = None
    latitude: float
    longitude: float


class DoleanceCreate(BaseModel):
    """Depot d'une doleance depuis l'application citoyenne.

    Le vocabulaire des categories est volontairement celui d'un habitant et
    non celui d'un technicien : personne ne se plaint spontanement d'un
    depassement de seuil de particules, on se plaint de poussiere.
    """
    description: str = Field(min_length=5)
    categorie: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DoleanceOut(BaseModel):
    id: int
    description: str
    categorie: Optional[str] = None
    statut: str
    cree_le: datetime
    chantier_id: Optional[int] = None
    canal: Optional[str] = None

    class Config:
        from_attributes = True
