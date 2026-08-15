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


def executer_seed(creer_extensions: bool = True) -> None:
    """Cree les donnees de demonstration si elles n'existent pas encore.

    `creer_extensions` permet de sauter la preparation du schema spatial, qui
    suppose PostgreSQL. Les tests s'executent sous SQLite, ou l'extension
    n'existe pas et ou les tables sont deja creees par le harnais : sans cette
    porte de sortie, le jeu de donnees initial resterait invérifiable, alors
    qu'il conditionne tout ce qu'une demonstration peut montrer.
    """
    if creer_extensions:
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

        # --- Riverain de demonstration ---
        # Le profil PLAIGNANT etait le seul des huit a n'avoir aucun compte au
        # seed, alors que les riverains s'inscrivent d'ordinaire eux-memes
        # depuis l'application citoyenne. Un compte pre-existant reste utile :
        # il permet d'ouvrir directement la file des doleances sans avoir a
        # derouler l'inscription, et il porte l'historique ci-dessous.
        riverain = db.query(models.Utilisateur).filter_by(
            email="riverain@yopougon.ci"
        ).first()
        if not riverain and y4:
            riverain = models.Utilisateur(
                nom="Kouassi Adjoua",
                email="riverain@yopougon.ci",
                mot_de_passe_hash=auth.hasher_mot_de_passe("riverain123"),
                role=models.RoleEnum.PLAIGNANT,
                premiere_connexion=False,
                chantier_rattachement_id=y4.id,
            )
            db.add(riverain)
            db.commit()
            db.refresh(riverain)
            print("Utilisateur cree : riverain@yopougon.ci (riverain Rocade Y4)")

        # --- Doleances de demonstration ---
        # Le Mecanisme de Gestion des Plaintes n'avait aucune donnee de
        # demonstration, si bien que l'ecran du specialiste du suivi social
        # s'ouvrait vide. Les entrees ci-dessous couvrent les deux canaux de
        # saisie, le guichet et le telephone, et les trois etats du traitement.
        # Cette mixite est le point que le rapport doit pouvoir montrer :
        # l'application citoyenne ne remplace pas le recueil classique, elle
        # s'y ajoute.
        doleances_demo = [
            # Depuis l'application citoyenne, par le riverain de demonstration.
            ("Kouassi Adjoua", riverain, y4, "bruit", "MOBILE", "OUVERTE",
             "Les engins travaillent apres vingt-deux heures depuis une semaine, "
             "impossible de dormir avec les enfants."),
            ("Kouassi Adjoua", riverain, y4, "poussiere", "MOBILE", "EN_COURS",
             "La poussiere du terrassement recouvre la cour de l'ecole voisine, "
             "les enfants toussent en sortant de classe."),
            ("Kouassi Adjoua", riverain, y4, "circulation", "MOBILE", "RESOLU",
             "La deviation obligeait les taxis a passer devant le marche aux "
             "heures de pointe. Un itineraire a ete revu depuis."),
            # Recueillies au guichet ou en reunion de quartier, sans compte.
            ("Yao Beatrice", None, ouest, None, "GUICHET", "OUVERTE",
             "Les eaux stagnantes derriere la palissade attirent les moustiques "
             "depuis le debut des pluies."),
            ("Traore Ibrahim", None, latrille, None, "GUICHET", "RESOLU",
             "Fissures apparues sur le mur de cloture apres le passage des "
             "engins lourds. Reparation constatee."),
        ]
        for nom_p, auteur, chantier, categorie, canal, statut, description in doleances_demo:
            if not chantier:
                continue
            if db.query(models.Plainte).filter_by(description=description).first():
                continue
            db.add(models.Plainte(
                nom_plaignant=nom_p,
                contact=auteur.email if auteur else None,
                description=description,
                statut=statut,
                chantier_id=chantier.id,
                plaignant_id=auteur.id if auteur else None,
                categorie=categorie,
                canal=canal,
            ))
            print(f"Doleance creee : {nom_p} ({canal}, {statut})")

        db.commit()
        print("Initialisation terminee.")
    finally:
        db.close()


if __name__ == "__main__":
    executer_seed()
