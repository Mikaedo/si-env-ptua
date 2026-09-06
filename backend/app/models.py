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
    """Les huit profils du dispositif de suivi environnemental du PTUA.

    Les cinq premiers correspondent aux intervenants operationnels du projet,
    ceux qui produisent ou traitent l'information. Les trois derniers ont ete
    ajoutes pour refleter la gouvernance reelle du programme : le regulateur
    national et le bailleur consultent sans jamais ecrire, et les riverains
    alimentent le mecanisme de gestion des plaintes depuis leur telephone.
    """
    RESP_ENV = "RESP_ENV"
    EXPERT_HSE = "EXPERT_HSE"
    SPEC_ENV = "SPEC_ENV"
    SPEC_PAR = "SPEC_PAR"
    ADMIN = "ADMIN"
    ANDE = "ANDE"              # Agence Nationale de l'Environnement
    BAD = "BAD"                # Banque Africaine de Developpement
    PLAIGNANT = "PLAIGNANT"    # Riverain d'un chantier


#: Profils autorises a lire sans jamais pouvoir modifier quoi que ce soit.
#: La restriction est appliquee par une dependance FastAPI, donc elle tient
#: meme si une requete est forgee en dehors du tableau de bord.
ROLES_LECTURE_SEULE = {RoleEnum.ANDE, RoleEnum.BAD}

#: Profils qui accedent au tableau de bord web.
ROLES_WEB = {
    RoleEnum.ADMIN, RoleEnum.SPEC_ENV, RoleEnum.SPEC_PAR,
    RoleEnum.ANDE, RoleEnum.BAD,
}

#: Profils qui accedent a l'application mobile des agents AGEROUTE.
ROLES_MOBILE_AGENT = {RoleEnum.RESP_ENV, RoleEnum.EXPERT_HSE}

#: Profil unique de l'application mobile citoyenne.
ROLES_MOBILE_CITOYEN = {RoleEnum.PLAIGNANT}


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
    # Chantier de rattachement, renseigne uniquement pour les riverains. Il est
    # determine automatiquement a l'inscription, a partir de la position GPS du
    # telephone, et fige le perimetre dont la personne peut se plaindre.
    chantier_rattachement_id = Column(Integer, ForeignKey("chantiers.id"), nullable=True)

    signalements = relationship("Signalement", back_populates="auteur")
    chantier_rattachement = relationship("Chantier", foreign_keys=[chantier_rattachement_id])


class Chantier(Base):
    __tablename__ = "chantiers"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(150), nullable=False)
    commune = Column(String(100))
    geom = Column(Geometry(geometry_type="POINT", srid=4326))
    # Rayon de la zone d'influence, en metres. Il traduit une notion que tout
    # PGES manipule : l'aire autour du chantier dans laquelle les nuisances
    # sont ressenties. Elle conditionne l'acces a l'application citoyenne, un
    # riverain ne pouvant deposer de doleance que s'il se trouve a l'interieur.
    # La valeur varie d'un chantier a l'autre : un terrassement lourd derange
    # plus loin qu'une simple reprise de chaussee.
    rayon_influence_m = Column(Integer, nullable=False, default=1500)

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
    """Action engagee pour traiter un signalement ou une plainte.

    Rattachee a l'un ou l'autre (jamais force a choisir un objet generique
    plus difficile a interroger) : signalement_id pour le suivi
    environnemental, plainte_id pour le suivi du P.A.R. Les deux colonnes
    restent facultatives individuellement, une seule doit etre renseignee.
    """
    __tablename__ = "actions_correctives"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    echeance = Column(DateTime)
    cree_le = Column(DateTime, default=datetime.utcnow)
    signalement_id = Column(Integer, ForeignKey("signalements.id"), nullable=True)
    plainte_id = Column(Integer, ForeignKey("plaintes.id"), nullable=True)

    signalement = relationship("Signalement", back_populates="actions")
    plainte = relationship("Plainte", back_populates="actions")


class NonConformite(Base):
    __tablename__ = "non_conformites"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    severite = Column(String(20), default="MOYENNE")
    resolue = Column(Boolean, default=False)
    cree_le = Column(DateTime, default=datetime.utcnow)
    signalement_id = Column(Integer, ForeignKey("signalements.id"))


class Plainte(Base):
    """Doleance enregistree au titre du Mecanisme de Gestion des Plaintes.

    L'objet metier existait deja pour les plaintes recueillies au guichet ou
    lors des reunions de riverains. Plutot que d'ouvrir une seconde table pour
    les depots faits depuis l'application citoyenne, ce qui aurait introduit
    deux representations concurrentes d'une meme realite, le telephone est
    traite comme un canal de saisie supplementaire. Le specialiste du suivi
    du P.A.R conserve ainsi une file unique, quelle que soit la provenance.
    """
    __tablename__ = "plaintes"

    id = Column(Integer, primary_key=True, index=True)
    nom_plaignant = Column(String(120), nullable=False)
    contact = Column(String(60))
    description = Column(Text, nullable=False)
    statut = Column(String(20), default="OUVERTE")
    cree_le = Column(DateTime, default=datetime.utcnow)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"))

    # ── Champs propres au canal mobile ────────────────────────────────────
    # Auteur du depot. Reste vide pour les plaintes saisies au guichet par un
    # agent, ce qui preserve l'historique anterieur a l'application.
    plaignant_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    # Nature de la nuisance, choisie dans une liste courte pensee pour un
    # habitant et non pour un technicien : bruit, poussiere, circulation, eau.
    categorie = Column(String(40), nullable=True)
    # Position relevee au moment du depot. Elle situe la nuisance elle-meme,
    # qui n'est pas necessairement au domicile de la personne.
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    photo_chemin = Column(String(255), nullable=True)
    # Provenance : GUICHET pour la saisie par un agent, MOBILE pour un depot
    # citoyen. Permet de mesurer l'apport reel de l'application dans le rapport
    # de sauvegardes remis au bailleur.
    canal = Column(String(20), default="GUICHET")

    plaignant = relationship("Utilisateur", foreign_keys=[plaignant_id])
    actions = relationship("ActionCorrective", back_populates="plainte", cascade="all, delete-orphan")


class AlerteSeuil(Base):
    __tablename__ = "alertes_seuils"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(120), nullable=False)
    indicateur = Column(String(80), nullable=False)
    seuil = Column(Float, nullable=False)
    niveau = Column(String(20), default="WARNING")
    actif = Column(Boolean, default=True)
    cree_le = Column(DateTime, default=datetime.utcnow)
    # Portee du seuil. Laisse vide, il vaut pour l'ensemble des chantiers, ce
    # qui etait le seul comportement possible auparavant. Renseigne, il ne
    # s'applique qu'au chantier designe : deux chantiers voisins n'ont pas
    # forcement la meme sensibilite, un ouvrage proche d'une zone humide
    # justifie par exemple un seuil de turbidite plus severe.
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=True)

    chantier = relationship("Chantier")


class MesurePrestataire(Base):
    """Mesure instrumentee realisee par un laboratoire agree (BF-08).

    Le systeme reposait jusqu'ici sur l'observation, celle de l'agent sur
    le terrain et celle du satellite. Aucune des deux ne vaut mesure : le
    memoire le dit du volet satellitaire, qui « oriente les priorites de
    terrain, il ne remplace pas la mesure instrumentee exigee par la BAD
    et l'ANDE ». Le bruit s'evalue a l'oreille faute de sonometre, et les
    poussieres ne se mesurent pas du tout.

    Ces mesures existent pourtant : un laboratoire accredite intervient
    sur les chantiers, et ses resultats sont ce que le bailleur reconnait
    officiellement. Ils vivaient sur papier, hors du dispositif, et le
    rapport de suivi ne pouvait donc pas les porter.

    La table les accueille avec ce qui les rend opposables : la grandeur
    mesuree, sa valeur, la date du prelevement et le laboratoire qui l'a
    signee. Sans ces deux derniers, une mesure n'est qu'un nombre.
    """
    __tablename__ = "mesures_prestataire"

    id = Column(Integer, primary_key=True, index=True)
    #: BRUIT, PM25, PM10 ou TURBIDITE.
    parametre = Column(String(20), nullable=False)
    valeur = Column(Float, nullable=False)
    #: dB(A), µg/m³ ou NTU, selon le parametre.
    unite = Column(String(16), nullable=False)
    #: Quand le prelevement a ete fait, non quand il a ete saisi : c'est
    #: la date du terrain qui compte pour le rapport.
    date_prelevement = Column(DateTime, nullable=False)
    #: Le laboratoire agree qui signe la mesure. Une mesure sans auteur
    #: ne vaut rien devant un bailleur.
    laboratoire = Column(String(160), nullable=False)
    #: Point de mesure, methode, conditions : ce qu'un rapport de
    #: laboratoire precise et qu'un nombre seul ne dit pas.
    observations = Column(Text, nullable=True)
    cree_le = Column(DateTime, default=datetime.utcnow)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=False)
    #: Qui l'a versee au dossier, le specialiste du suivi.
    saisie_par_id = Column(Integer, ForeignKey("utilisateurs.id"),
                           nullable=True)

    chantier = relationship("Chantier")
    saisie_par = relationship("Utilisateur")


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




class TransmissionRapport(Base):
    """Trace d'un rapport adresse a un organisme de controle.

    Consulter le tableau de bord et recevoir officiellement un rapport sont
    deux actes distincts. L'ANDE et la BAD suivent le programme au fil de
    l'eau depuis leur acces en consultation, mais la remise periodique du
    rapport de conformite reste une formalite dont il faut pouvoir rendre
    compte. C'est precisement ce qu'un auditeur reclame : non pas le document,
    qu'il possede deja, mais la preuve de la date a laquelle il lui a ete
    adresse, et par qui.

    L'enregistrement subsiste meme lorsque l'acheminement echoue, faute de quoi
    une transmission perdue en route ne laisserait aucune trace et passerait
    pour n'avoir jamais ete tentee.
    """
    __tablename__ = "transmissions_rapports"

    id = Column(Integer, primary_key=True, index=True)
    transmis_le = Column(DateTime, default=datetime.utcnow, index=True)
    # Auteur de la transmission, conserve sous forme d'adresse : la trace doit
    # survivre a la suppression du compte qui l'a produite.
    emetteur_email = Column(String(120), nullable=False)
    destinataire_email = Column(String(120), nullable=False)
    # Organisme vise, tel que choisi dans le formulaire (ANDE, BAD, etc.).
    organisme = Column(String(40), nullable=True)
    periode_debut = Column(String(20), nullable=True)
    periode_fin = Column(String(20), nullable=True)
    # Chantiers couverts, enregistres sous forme de liste d'identifiants
    # separes par des virgules pour rester lisible sans jointure.
    chantiers = Column(String(255), nullable=True)
    nom_fichier = Column(String(160), nullable=True)
    taille_octets = Column(Integer, nullable=True)
    succes = Column(Boolean, default=False, nullable=False)
    detail_erreur = Column(Text, nullable=True)
