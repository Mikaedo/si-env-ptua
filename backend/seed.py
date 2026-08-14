"""
seed.py
-------
Script d'INITIALISATION : cree des donnees de depart pour tester l'API.

Deux modes d'utilisation :

    1. Ligne de commande (dev local) :
           python seed.py

    2. Appel programmatique (main.py, sur une base vide) :
           from seed import executer_seed
           executer_seed()

Le seed est idempotent : chaque insertion est gardee par un
`filter_by(...).first()`, on peut donc l'exercer plusieurs fois sans creer
de doublon.
"""
from sqlalchemy import func, text

from app.database import SessionLocal, engine, Base
from app import models, auth


def executer_seed() -> None:
    """Cree les donnees de demonstration si elles n'existent pas encore."""

    # S'assure que PostGIS est actif et que les tables existent.
    # Sur Supabase, l'extension est preinstallee : la commande est un no-op.
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # --- Utilisateurs ---
        users_data = [
            ("Administrateur SI-ENV", "admin@sienv.ci", "admin123", models.RoleEnum.ADMIN, False),
            ("KONANBOUO Georges", "resp.env@ageroute.ci", "env123", models.RoleEnum.RESP_ENV, False),
            ("EXPERT HSE", "expert.hse@ageroute.ci", "expert123", models.RoleEnum.EXPERT_HSE, False),
            ("Spec. Env", "spec.env@ageroute.ci", "spec123", models.RoleEnum.SPEC_ENV, False),
            ("Spec. P.A.R", "spec.par@ageroute.ci", "spec123", models.RoleEnum.SPEC_PAR, False),
            ("Agent nouvelle recrue", "nouveau@ageroute.ci", None, models.RoleEnum.RESP_ENV, True),
            # Organismes de controle, en consultation seule. L'ANDE exerce la
            # tutelle environnementale nationale, la BAD finance le programme
            # et verifie le respect de ses sauvegardes operationnelles.
            ("Contrôleur ANDE", "controle@ande.ci", "ande123", models.RoleEnum.ANDE, False),
            ("Mission BAD", "mission@afdb.org", "bad123", models.RoleEnum.BAD, False),
        ]
        for nom, email, mdp, role, premiere in users_data:
            if not db.query(models.Utilisateur).filter_by(email=email).first():
                db.add(models.Utilisateur(
                    nom=nom, email=email,
                    mot_de_passe_hash=auth.hasher_mot_de_passe(mdp) if mdp else None,
                    role=role, premiere_connexion=premiere,
                ))
                print(f"Utilisateur cree : {email}" + (" (premiere connexion)" if premiere else ""))

        # --- Chantiers ---
        # Les six chantiers PTUA presentes dans le memoire (memes noms et
        # coordonnees que gee_service.py, pour que le tableau de bord, le
        # mobile et l'analyse satellitaire pointent tous vers les memes sites).
        chantiers_data = [
            ("Rocade Y4",           "Yopougon",         -4.048, 5.372),
            ("4e Pont d'Abidjan",   "Plateau/Adjame",   -4.009, 5.356),
            ("Bd Latrille",         "Cocody",           -3.974, 5.348),
            ("Sortie Est",          "Bingerville",      -3.881, 5.338),
            ("Sortie Ouest",        "Yopougon/Songon",  -4.103, 5.341),
            ("Echangeurs CG",       "Plateau",          -4.016, 5.319),
        ]
        for nom, commune, lon, lat in chantiers_data:
            if not db.query(models.Chantier).filter_by(nom=nom).first():
                db.add(models.Chantier(
                    nom=nom, commune=commune,
                    geom=func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
                ))
                print(f"Chantier cree : {nom}")

        # --- Site de demonstration ---
        # L'application citoyenne n'ouvre l'inscription qu'aux riverains, en
        # comparant la position du telephone au rayon d'influence du chantier
        # le plus proche. Cette regle, indispensable en exploitation, rendrait
        # toute demonstration impossible ailleurs qu'au pied des travaux. Ce
        # site couvre donc volontairement un rayon tres large, ce qui permet de
        # derouler le parcours complet depuis une salle de soutenance. Il est
        # identifie comme tel et l'administrateur peut le retirer en une action
        # avant une mise en service reelle.
        if not db.query(models.Chantier).filter_by(nom="Site de démonstration").first():
            db.add(models.Chantier(
                nom="Site de démonstration",
                commune="Abidjan",
                geom=func.ST_SetSRID(func.ST_MakePoint(-4.008, 5.345), 4326),
                rayon_influence_m=500_000,
            ))
            print("Chantier cree : Site de démonstration (rayon elargi)")
        db.commit()

        # --- Signalements de demo ---
        y4       = db.query(models.Chantier).filter_by(nom="Rocade Y4").first()
        latrille = db.query(models.Chantier).filter_by(nom="Bd Latrille").first()
        ouest    = db.query(models.Chantier).filter_by(nom="Sortie Ouest").first()
        pont4    = db.query(models.Chantier).filter_by(nom="4e Pont d'Abidjan").first()
        agent    = db.query(models.Utilisateur).filter_by(email="resp.env@ageroute.ci").first()
        expert   = db.query(models.Utilisateur).filter_by(email="expert.hse@ageroute.ci").first()

        signalements_demo = [
            ("demo-001", agent, y4,       "Dechets de chantier", "Accumulation importante pres du chantier",
             models.CriticiteEnum.ELEVE, models.CriticiteEnum.MODERE, 87.0,
             models.StatutSignalement.NOUVEAU,       -4.048, 5.372),
            ("demo-002", agent, ouest,    "Eaux stagnantes",     "Stagnation apres pluie",
             models.CriticiteEnum.MODERE, None, None,
             models.StatutSignalement.EN_TRAITEMENT, -4.103, 5.341),
            ("demo-003", agent, latrille, "Dechets de chantier", "Dechets evacues",
             models.CriticiteEnum.FAIBLE, None, None,
             models.StatutSignalement.CLOTURE,       -3.974, 5.348),
            ("demo-expert-001", expert, pont4, "Poussieres",
             "Nuisance de poussiere importante sur le terrassement du 4e Pont",
             models.CriticiteEnum.ELEVE, models.CriticiteEnum.ELEVE, 92.0,
             models.StatutSignalement.NOUVEAU,       -4.009, 5.356),
            ("demo-expert-002", expert, ouest, "Eaux stagnantes",
             "Non-conformite : absence de drainage temporaire",
             models.CriticiteEnum.MODERE, None, None,
             models.StatutSignalement.EN_TRAITEMENT, -4.103, 5.341),
        ]
        for uuid_, auteur, chantier, type_, desc, crit, crit_ia, conf, statut, lon, lat in signalements_demo:
            if not auteur or not chantier:
                continue
            if db.query(models.Signalement).filter_by(uuid_mobile=uuid_).first():
                continue
            db.add(models.Signalement(
                uuid_mobile=uuid_, type_nuisance=type_, description=desc,
                criticite=crit, criticite_ia=crit_ia, confiance_ia=conf,
                gps_source="AUTO", statut=statut,
                geom=func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
                auteur_id=auteur.id, chantier_id=chantier.id,
            ))
            print(f"Signalement {uuid_} cree")

        # --- Alerte de demo ---
        if not db.query(models.Alerte).filter_by(message="Seuil qualite air depasse").first():
            db.add(models.Alerte(
                message="Seuil qualite air depasse", niveau="CRITIQUE",
                valeur=72.5, chantier_id=ouest.id if ouest else None,
            ))
            print("Alerte demo creee")

        db.commit()
        print("Initialisation terminee.")
    finally:
        db.close()


if __name__ == "__main__":
    executer_seed()
