"""
seed.py
-------
Script d'INITIALISATION : cree des donnees de depart pour tester l'API.

Lance-le UNE FOIS apres avoir demarre la base :
    python seed.py
"""
from sqlalchemy import func, text

from app.database import SessionLocal, engine, Base
from app import models, auth

# S'assure que PostGIS est actif et que les tables existent
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    conn.commit()
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# --- Utilisateurs ---
users_data = [
    ("Administrateur SI-ENV", "admin@sienv.ci", "admin123", models.RoleEnum.ADMIN, False),
    ("KONANBOUO Georges", "resp.env@ageroute.ci", "env123", models.RoleEnum.RESP_ENV, False),
    ("EXPERT HSE", "expert.hse@ageroute.ci", "expert123", models.RoleEnum.EXPERT_HSE, False),
    ("Spéc. Env", "spec.env@ageroute.ci", "spec123", models.RoleEnum.SPEC_ENV, False),
    ("Spéc. P.A.R", "spec.par@ageroute.ci", "spec123", models.RoleEnum.SPEC_PAR, False),
    ("Agent nouvelle recrue", "nouveau@ageroute.ci", None, models.RoleEnum.RESP_ENV, True),
]


for nom, email, mdp, role, premiere in users_data:
    if not db.query(models.Utilisateur).filter_by(email=email).first():
        u = models.Utilisateur(
            nom=nom,
            email=email,
            mot_de_passe_hash=auth.hasher_mot_de_passe(mdp) if mdp else None,
            role=role,
            premiere_connexion=premiere,
        )
        db.add(u)
        print(f"Utilisateur cree : {email}" + (" (premiere connexion)" if premiere else ""))

# --- Chantiers ---
chantiers_data = [
    ("4eme Pont", "Yopougon", -4.05, 5.34),
    ("Pont de Bassam · Lot 1", "Bassam", -3.75, 5.15),
    ("Bd Latrille · Lot 3", "Cocody", -4.01, 5.36),
    ("Rocade Marcory · Lot 2", "Marcory", -4.02, 5.30),
]

for nom, commune, lon, lat in chantiers_data:
    if not db.query(models.Chantier).filter_by(nom=nom).first():
        c = models.Chantier(
            nom=nom,
            commune=commune,
            geom=func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
        )
        db.add(c)
        print(f"Chantier cree : {nom}")

db.commit()

# --- Signalements de demo ---
chantier_bassam = db.query(models.Chantier).filter_by(nom="Pont de Bassam · Lot 1").first()
chantier_latrille = db.query(models.Chantier).filter_by(nom="Bd Latrille · Lot 3").first()
chantier_marcory = db.query(models.Chantier).filter_by(nom="Rocade Marcory · Lot 2").first()
agent = db.query(models.Utilisateur).filter_by(email="resp.env@ageroute.ci").first()
expert = db.query(models.Utilisateur).filter_by(email="expert.hse@ageroute.ci").first()

if agent and chantier_bassam and not db.query(models.Signalement).filter_by(uuid_mobile="demo-001").first():
    s = models.Signalement(
        uuid_mobile="demo-001",
        type_nuisance="Dechets de chantier",
        description="Accumulation importante pres du pont",
        criticite=models.CriticiteEnum.ELEVE,
        criticite_ia=models.CriticiteEnum.MODERE,
        confiance_ia=87.0,
        gps_source="AUTO",
        statut=models.StatutSignalement.NOUVEAU,
        geom=func.ST_SetSRID(func.ST_MakePoint(-3.75, 5.15), 4326),
        auteur_id=agent.id,
        chantier_id=chantier_bassam.id,
    )
    db.add(s)
    print("Signalement demo-001 cree")

if agent and chantier_marcory and not db.query(models.Signalement).filter_by(uuid_mobile="demo-002").first():
    s2 = models.Signalement(
        uuid_mobile="demo-002",
        type_nuisance="Eaux stagnantes",
        description="Stagnation apres pluie",
        criticite=models.CriticiteEnum.MODERE,
        gps_source="AUTO",
        statut=models.StatutSignalement.EN_TRAITEMENT,
        geom=func.ST_SetSRID(func.ST_MakePoint(-4.02, 5.30), 4326),
        auteur_id=agent.id,
        chantier_id=chantier_marcory.id,
    )
    db.add(s2)
    print("Signalement demo-002 cree")

if agent and chantier_latrille and not db.query(models.Signalement).filter_by(uuid_mobile="demo-003").first():
    s3 = models.Signalement(
        uuid_mobile="demo-003",
        type_nuisance="Dechets de chantier",
        description="Dechets evacues",
        criticite=models.CriticiteEnum.FAIBLE,
        gps_source="AUTO",
        statut=models.StatutSignalement.CLOTURE,
        geom=func.ST_SetSRID(func.ST_MakePoint(-4.01, 5.36), 4326),
        auteur_id=agent.id,
        chantier_id=chantier_latrille.id,
    )
    db.add(s3)
    print("Signalement demo-003 cree")

# --- Signalements de l'Expert HSE (controle externe) ---
chantier_4eme = db.query(models.Chantier).filter_by(nom="4eme Pont").first()
if expert and chantier_4eme and not db.query(models.Signalement).filter_by(uuid_mobile="demo-expert-001").first():
    se1 = models.Signalement(
        uuid_mobile="demo-expert-001",
        type_nuisance="Poussieres",
        description="Nuisance de poussière importante sur le terrassement du 4eme Pont",
        criticite=models.CriticiteEnum.ELEVE,
        criticite_ia=models.CriticiteEnum.ELEVE,
        confiance_ia=92.0,
        gps_source="AUTO",
        statut=models.StatutSignalement.NOUVEAU,
        geom=func.ST_SetSRID(func.ST_MakePoint(-4.05, 5.34), 4326),
        auteur_id=expert.id,
        chantier_id=chantier_4eme.id,
    )
    db.add(se1)
    print("Signalement demo-expert-001 cree (Expert HSE)")

if expert and chantier_marcory and not db.query(models.Signalement).filter_by(uuid_mobile="demo-expert-002").first():
    se2 = models.Signalement(
        uuid_mobile="demo-expert-002",
        type_nuisance="Eaux stagnantes",
        description="Non-conformité: absence de drainage temporaire",
        criticite=models.CriticiteEnum.MODERE,
        gps_source="AUTO",
        statut=models.StatutSignalement.EN_TRAITEMENT,
        geom=func.ST_SetSRID(func.ST_MakePoint(-4.02, 5.30), 4326),
        auteur_id=expert.id,
        chantier_id=chantier_marcory.id,
    )
    db.add(se2)
    print("Signalement demo-expert-002 cree (Expert HSE)")

# --- Alerte de demo ---
if not db.query(models.Alerte).filter_by(message="Seuil qualite air depasse").first():
    a = models.Alerte(
        message="Seuil qualite air depasse",
        niveau="CRITIQUE",
        valeur=72.5,
        chantier_id=chantier_marcory.id if chantier_marcory else None,
    )
    db.add(a)
    print("Alerte demo creee")

db.commit()
db.close()
print("Initialisation terminee.")
