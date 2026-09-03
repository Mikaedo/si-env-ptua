"""
seed_rbac.py
------------
Script de seed RBAC conforme à la mémoire SI-ENV v56.

5 profils :
  1. Responsable Environnement  → MOBILE (autocontrôle chantier)
  2. Expert HSE                 → MOBILE (contrôle externe)
  3. Spécialiste Suivi Env.     → WEB   (dashboard, alertes, satellite, rapports)
  4. Spécialiste Suivi P.A.R    → WEB   (plaintes MGP)
  5. Administrateur             → WEB   (comptes, chantiers, seuils, IA, consultation)

Usage:
  docker exec sienv_backend python /app/seed_rbac.py
"""
from sqlalchemy import func, text
from app.database import SessionLocal, engine, Base
from app import models, auth

with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    conn.commit()
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ─── Utilisateurs (RBAC) ───
users_data = [
    # (nom, email, mot_de_passe, rôle, première_connexion, plateforme)
    ("KOFFI Marc", "resp.env@ageroute.ci", "Env2025!", models.RoleEnum.RESP_ENV, False),
    ("DIABATE Salif", "expert.hse@ageroute.ci", "Hse2025!", models.RoleEnum.EXPERT_HSE, False),
    ("KONAN Aya", "spec.env@ageroute.ci", "Spec2025!", models.RoleEnum.SPEC_ENV, False),
    ("BAMBA Moussa", "spec.par@ageroute.ci", "Par2025!", models.RoleEnum.SPEC_PAR, False),
    ("TRAORE Ismael", "admin@sienv.ci", "Admin2025!", models.RoleEnum.ADMIN, False),
    ("Agent Nouveau", "nouveau@ageroute.ci", None, models.RoleEnum.RESP_ENV, True),
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
        print(f"  ✓ {email} | {role.value} | {'MOBILE' if role in (models.RoleEnum.RESP_ENV, models.RoleEnum.EXPERT_HSE) else 'WEB'} | {'1ère connexion' if premiere else 'actif'}")

# ─── Chantiers ───
#
# Les six ouvrages du Programme de Transport Urbain d'Abidjan, avec leur
# denomination officielle et le point median de leur trace. Le jeu de
# demonstration comportait auparavant des chantiers inventes (Pont de
# Bassam, Rocade Marcory) etrangers au programme : ils apparaissaient
# dans la liste deroulante de l'application mobile, ou l'agent devait
# choisir entre des ouvrages qui n'existent pas et ceux qu'il connait.
chantiers_data = [
    ("4e Pont", "Yopougon/Attécoubé/Adjamé", -4.0280, 5.3680),
    ("Rocade Y4", "Cocody/Abobo/Anyama", -3.9700, 5.4300),
    ("Bd Latrille - Prolongement", "Cocody", -3.9820, 5.3550),
    ("Sortie Est", "Bingerville/Agboville", -3.9100, 5.4000),
    ("Sortie Ouest", "Yopougon/Songon", -4.1400, 5.3120),
    ("Échangeurs Bd Coffi Gadeau", "Plateau", -4.0000, 5.3580),
]

for nom, commune, lon, lat in chantiers_data:
    if not db.query(models.Chantier).filter_by(nom=nom).first():
        c = models.Chantier(
            nom=nom,
            commune=commune,
            geom=func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
        )
        db.add(c)
        print(f"  ✓ Chantier: {nom}")

db.commit()

# ─── Signalements de démo ───
# Les signalements de demonstration couvrent les cinq types de nuisance
# du referentiel et les six ouvrages du programme. Le jeu precedent n'en
# renseignait que trois : la repartition par nuisance, sur le tableau de
# bord mobile, laissait croire que le bruit et la degradation de la
# vegetation n'etaient pas suivis.
def chantier(nom):
    return db.query(models.Chantier).filter_by(nom=nom).first()

agent = db.query(models.Utilisateur).filter_by(email="resp.env@ageroute.ci").first()
expert = db.query(models.Utilisateur).filter_by(email="expert.hse@ageroute.ci").first()

DEMOS = [
    # (uuid, auteur, chantier, type, description, criticite, statut, lon, lat,
    #  criticite_ia, confiance_ia)
    ("demo-001", "agent", "4e Pont", "Déchets de chantier",
     "Accumulation importante en bordure d'emprise",
     "ELEVE", "NOUVEAU", -4.0280, 5.3680, "MODERE", 87.0),
    ("demo-002", "agent", "Sortie Ouest", "Eaux stagnantes",
     "Stagnation apres pluie au droit du terrassement",
     "MODERE", "EN_TRAITEMENT", -4.1400, 5.3120, None, None),
    ("demo-003", "agent", "Bd Latrille - Prolongement", "Déchets de chantier",
     "Gravats evacues apres intervention",
     "FAIBLE", "CLOTURE", -3.9820, 5.3550, None, None),
    ("demo-004", "agent", "Rocade Y4", "Bruit",
     "Engins de compactage en activite au-dela de 18 h",
     "MODERE", "EN_TRAITEMENT", -3.9700, 5.4300, None, None),
    ("demo-005", "agent", "Sortie Est", "Dégradation végétation",
     "Abattage non signale en limite d'emprise",
     "ELEVE", "NOUVEAU", -3.9100, 5.4000, None, None),
    ("demo-expert-001", "expert", "4e Pont", "Poussières",
     "Nuisance de poussiere importante sur le terrassement",
     "ELEVE", "NOUVEAU", -4.0280, 5.3680, "ELEVE", 92.0),
    ("demo-expert-002", "expert", "Échangeurs Bd Coffi Gadeau", "Eaux stagnantes",
     "Non-conformite : absence de drainage temporaire",
     "MODERE", "EN_TRAITEMENT", -4.0000, 5.3580, None, None),
    ("demo-expert-003", "expert", "Rocade Y4", "Poussières",
     "Arrosage des pistes interrompu depuis deux jours",
     "MODERE", "NOUVEAU", -3.9700, 5.4300, None, None),
]

for (uid, qui, nom_chantier, type_n, desc, crit, statut,
     lon, lat, crit_ia, conf_ia) in DEMOS:
    auteur = agent if qui == "agent" else expert
    site = chantier(nom_chantier)
    if not auteur or not site:
        continue
    if db.query(models.Signalement).filter_by(uuid_mobile=uid).first():
        continue
    db.add(models.Signalement(
        uuid_mobile=uid,
        type_nuisance=type_n,
        description=desc,
        criticite=models.CriticiteEnum[crit],
        criticite_ia=models.CriticiteEnum[crit_ia] if crit_ia else None,
        confiance_ia=conf_ia,
        gps_source="AUTO",
        statut=models.StatutSignalement[statut],
        geom=func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
        auteur_id=auteur.id,
        chantier_id=site.id,
    ))
    print(f"  ✓ Signalement {uid} ({type_n})")

chantier_alerte = chantier("Rocade Y4")

# ─── Alerte de démo ───
if not db.query(models.Alerte).filter_by(message="Seuil qualite air depasse").first():
    a = models.Alerte(
        message="Seuil qualite air depasse",
        niveau="CRITIQUE",
        valeur=72.5,
        chantier_id=chantier_alerte.id if chantier_alerte else None,
    )
    db.add(a)
    print("  ✓ Alerte demo (CRITIQUE)")

db.commit()
db.close()
print("\n=== Seed RBAC terminé ===")
