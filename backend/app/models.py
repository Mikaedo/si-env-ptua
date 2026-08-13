"""
models.py
---------
Tables de la base de donnees (ORM SQLAlchemy).
Correspond au chapitre 6 (MCD/MLD) du memoire.
"""
import enum
from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, Enum, Text, Float, Boolean)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from .database import Base


class RoleEnum(str, enum.Enum):
    RESP_ENV = "RESP_ENV"
    EXPERT_HSE = "EXPERT_HSE"
    SPEC_ENV = "SPEC_ENV"
    SPEC_PAR = "SPEC_PAR"
    ADMIN = "ADMIN"


class StatutSignalement(str, enum.Enum):
    NOUVEAU = "NOUVEAU"
    EN_TRAITEMENT = "EN_TRAITEMENT"
    CLOTURE = "CLOTURE"
    REJETE = "REJETE"


class CriticiteEnum(str, enum.Enum):
    FAIBLE = "FAIBLE"
    MODERE = "MODERE"
    ELEVE = "ELEVE"


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(120), nullable=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    mot_de_passe_hash = Column(String(255), nullable=True)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.RESP_ENV)
    premiere_connexion = Column(Boolean, default=True)
    telephone = Column(String(30))
    cree_le = Column(DateTime, default=datetime.utcnow)
    # Authentification a deux facteurs par email. Optionnelle par utilisateur.
    twofa_email_actif = Column(Boolean, default=False, nullable=False)

    signalements = relationship("Signalement", back_populates="auteur")


class Chantier(Base):
    __tablename__ = "chantiers"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(150), nullable=False)
    commune = Column(String(100))
    geom = Column(Geometry(geometry_type="POINT", srid=4326))

    signalements = relationship("Signalement", back_populates="chantier")


class Signalement(Base):
    __tablename__ = "signalements"

    id = Column(Integer, primary_key=True, index=True)
    uuid_mobile = Column(String(64), unique=True, index=True)
    type_nuisance = Column(String(100), nullable=False)
    description = Column(Text)
    criticite = Column(Enum(CriticiteEnum), default=CriticiteEnum.FAIBLE)
    criticite_ia = Column(Enum(CriticiteEnum), nullable=True)
    confiance_ia = Column(Float, nullable=True)
    gps_source = Column(String(20), default="AUTO")
    statut = Column(Enum(StatutSignalement), default=StatutSignalement.NOUVEAU)
    geom = Column(Geometry(geometry_type="POINT", srid=4326))
    cree_le = Column(DateTime, default=datetime.utcnow)

    auteur_id = Column(Integer, ForeignKey("utilisateurs.id"))
    chantier_id = Column(Integer, ForeignKey("chantiers.id"))

    auteur = relationship("Utilisateur", back_populates="signalements")
    chantier = relationship("Chantier", back_populates="signalements")
    photos = relationship("Photo", back_populates="signalement", cascade="all, delete-orphan")
    actions = relationship("ActionCorrective", back_populates="signalement", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    chemin = Column(String(255), nullable=False)
    signalement_id = Column(Integer, ForeignKey("signalements.id"))

    signalement = relationship("Signalement", back_populates="photos")


class Alerte(Base):
    __tablename__ = "alertes"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String(255), nullable=False)
    niveau = Column(String(20), default="INFO")
    valeur = Column(Float)
    cree_le = Column(DateTime, default=datetime.utcnow)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"))
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    recue = Column(Boolean, default=False)


class ActionCorrective(Base):
    __tablename__ = "actions_correctives"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    echeance = Column(DateTime)
    cree_le = Column(DateTime, default=datetime.utcnow)
    signalement_id = Column(Integer, ForeignKey("signalements.id"))

    signalement = relationship("Signalement", back_populates="actions")


class NonConformite(Base):
    __tablename__ = "non_conformites"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    severite = Column(String(20), default="MOYENNE")
    resolue = Column(Boolean, default=False)
    cree_le = Column(DateTime, default=datetime.utcnow)
    signalement_id = Column(Integer, ForeignKey("signalements.id"))


class Plainte(Base):
    __tablename__ = "plaintes"

    id = Column(Integer, primary_key=True, index=True)
    nom_plaignant = Column(String(120), nullable=False)
    contact = Column(String(60))
    description = Column(Text, nullable=False)
    statut = Column(String(20), default="OUVERTE")
    cree_le = Column(DateTime, default=datetime.utcnow)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"))


class AlerteSeuil(Base):
    __tablename__ = "alertes_seuils"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(120), nullable=False)
    indicateur = Column(String(80), nullable=False)
    seuil = Column(Float, nullable=False)
    niveau = Column(String(20), default="WARNING")
    actif = Column(Boolean, default=True)
    cree_le = Column(DateTime, default=datetime.utcnow)


class Journal(Base):
    __tablename__ = "journaux"

    id = Column(Integer, primary_key=True, index=True)
    niveau = Column(String(20), default="INFO")
    message = Column(Text, nullable=False)
    utilisateur = Column(String(120), nullable=True)
    ip_source = Column(String(64), nullable=True)
    cree_le = Column(DateTime, default=datetime.utcnow)


# ═════════════════════════════════════════════════════════════════════════
# Ajouts pro pour rapprocher le SI-ENV d'une application moderne
# ═════════════════════════════════════════════════════════════════════════

class OtpCode(Base):
    """Codes a usage unique pour reinitialisation de mot de passe et 2FA.

    Remplace le dictionnaire en memoire du prototype, qui perdait ses codes
    au redemarrage du service. Chaque code a un motif ('reset' ou 'twofa'),
    une date d'expiration, et est marque consomme apres verification.
    """
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), index=True, nullable=False)
    code = Column(String(12), nullable=False)
    motif = Column(String(20), default="reset")  # reset | twofa
    expire_le = Column(DateTime, nullable=False)
    consomme_le = Column(DateTime, nullable=True)
    cree_le = Column(DateTime, default=datetime.utcnow)


class ErreurApp(Base):
    """Erreur applicative capturee par le middleware.

    Sert de Sentry embarque : chaque exception non geree est stockee ici
    pour consultation par l'administrateur, sans dependre d'un service tiers.
    """
    __tablename__ = "erreurs_app"

    id = Column(Integer, primary_key=True, index=True)
    survenue_le = Column(DateTime, default=datetime.utcnow, index=True)
    methode = Column(String(10))
    chemin = Column(String(255))
    utilisateur = Column(String(120), nullable=True)
    ip_source = Column(String(64), nullable=True)
    type_erreur = Column(String(120))
    message = Column(Text)
    trace = Column(Text, nullable=True)


class RefreshToken(Base):
    """Jeton de rafraichissement stocke en base pour permettre la revocation.

    Le JWT d'acces est court (15 min) pour limiter l'impact d'un vol ; le
    refresh dure 7 jours et peut etre revoque a la deconnexion ou en cas de
    compromission. Chaque refresh emet un nouvel access token sans nouvelle
    saisie de mot de passe.
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    jeton = Column(String(255), unique=True, index=True, nullable=False)
    expire_le = Column(DateTime, nullable=False)
    revoque = Column(Boolean, default=False)
    cree_le = Column(DateTime, default=datetime.utcnow)


