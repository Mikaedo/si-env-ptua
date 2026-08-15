"""
test_citoyen.py
---------------
Couvre le parcours du riverain : verification de la zone, inscription,
depot d'une doleance et consultation de son propre historique.

Le point sensible est la condition de proximite. Elle protege le dispositif de
depots emis depuis n'importe ou, mais elle doit rester juste : quelqu'un qui
subit reellement les travaux ne doit jamais se voir refuser l'acces, et
quelqu'un qui se trouve a l'autre bout de la ville ne doit jamais l'obtenir.
Les tests encadrent donc les deux cotes de la frontiere, ainsi que le cas d'un
chantier dont le rayon d'influence a ete elargi.
"""
import pytest

from app import models, auth


# Coordonnees reelles d'un chantier du PTUA, le boulevard Latrille a Cocody.
LAT_CHANTIER, LON_CHANTIER = 5.348, -3.974

# Environ 400 metres au nord : un riverain immediat.
LAT_PROCHE, LON_PROCHE = 5.3516, -3.974

# Yopougon, a une quinzaine de kilometres : hors de toute zone d'influence.
LAT_LOIN, LON_LOIN = 5.341, -4.103


@pytest.fixture
def chantier_positionne(db_session):
    """Chantier dote d'une position et du rayon d'influence par defaut."""
    c = models.Chantier(
        nom="Bd Latrille",
        commune="Cocody",
        geom=f"SRID=4326;POINT({LON_CHANTIER} {LAT_CHANTIER})",
        rayon_influence_m=1500,
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


@pytest.fixture
def riverain(db_session, chantier_positionne):
    u = models.Utilisateur(
        nom="Riverain Test",
        email="riverain@exemple.ci",
        mot_de_passe_hash=auth.hasher_mot_de_passe("riverain123"),
        role=models.RoleEnum.PLAIGNANT,
        premiere_connexion=False,
        chantier_rattachement_id=chantier_positionne.id,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def riverain_headers(riverain):
    jeton = auth.creer_token({"sub": str(riverain.id), "role": riverain.role.value})
    return {"Authorization": f"Bearer {jeton}"}


class TestCalculDistance:
    """La formule de haversine, socle de toute la condition de proximite."""

    def test_distance_nulle_sur_le_meme_point(self):
        from app.routers.citoyen_router import distance_metres
        assert distance_metres(LAT_CHANTIER, LON_CHANTIER, LAT_CHANTIER, LON_CHANTIER) < 1

    def test_distance_coherente_a_l_echelle_du_quartier(self):
        from app.routers.citoyen_router import distance_metres
        d = distance_metres(LAT_CHANTIER, LON_CHANTIER, LAT_PROCHE, LON_PROCHE)
        assert 350 < d < 450

    def test_distance_coherente_a_l_echelle_de_la_ville(self):
        from app.routers.citoyen_router import distance_metres
        d = distance_metres(LAT_CHANTIER, LON_CHANTIER, LAT_LOIN, LON_LOIN)
        assert 13_000 < d < 16_000


class TestVerificationZone:
    """Le verdict rendu avant l'inscription."""

    def test_riverain_immediat_autorise(self, client, chantier_positionne):
        reponse = client.post(
            "/citoyen/verifier-zone",
            json={"latitude": LAT_PROCHE, "longitude": LON_PROCHE},
        )
        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["autorise"] is True
        assert corps["chantier_nom"] == "Bd Latrille"

    def test_position_eloignee_refusee(self, client, chantier_positionne):
        reponse = client.post(
            "/citoyen/verifier-zone",
            json={"latitude": LAT_LOIN, "longitude": LON_LOIN},
        )
        assert reponse.status_code == 200
        assert reponse.json()["autorise"] is False

    def test_le_refus_indique_la_distance(self, client, chantier_positionne):
        """Un refus muet laisserait la personne sans moyen de comprendre."""
        corps = client.post(
            "/citoyen/verifier-zone",
            json={"latitude": LAT_LOIN, "longitude": LON_LOIN},
        ).json()
        assert corps["distance_m"] > corps["rayon_m"]

    def test_un_chantier_lointain_mais_couvrant_l_emporte(
        self, client, db_session, chantier_positionne
    ):
        """Le chantier retenu doit etre celui qui couvre, pas le plus proche.

        Ce cas s'est presente en conditions reelles : un site a l'emprise tres
        large englobait une position, mais un autre chantier, marginalement
        plus proche et au perimetre etroit, etait selectionne le premier, ce
        qui aboutissait a un refus alors qu'une zone valide existait.
        """
        db_session.add(models.Chantier(
            nom="Site à emprise étendue",
            commune="Abidjan",
            geom=f"SRID=4326;POINT({LON_CHANTIER - 0.01} {LAT_CHANTIER})",
            rayon_influence_m=50_000,
        ))
        db_session.commit()

        reponse = client.post(
            "/citoyen/verifier-zone",
            json={"latitude": LAT_LOIN, "longitude": LON_LOIN},
        )
        corps = reponse.json()
        assert corps["autorise"] is True
        assert corps["chantier_nom"] == "Site à emprise étendue"

    def test_un_rayon_elargi_change_le_verdict(self, client, db_session, chantier_positionne):
        """Le perimetre depend du chantier, comme dans un PGES.

        Un ouvrage dont l'emprise derange loin justifie une zone plus large,
        et le meme point peut donc etre accepte ici et refuse ailleurs.
        """
        chantier_positionne.rayon_influence_m = 20_000
        db_session.commit()

        reponse = client.post(
            "/citoyen/verifier-zone",
            json={"latitude": LAT_LOIN, "longitude": LON_LOIN},
        )
        assert reponse.json()["autorise"] is True


class TestInscription:
    """Auto-inscription du riverain, conditionnee a sa position."""

    def test_inscription_d_un_riverain_proche(self, client, chantier_positionne):
        reponse = client.post("/citoyen/inscription", json={
            "nom": "Kouassi Adjoua",
            "email": "kouassi.adjoua@exemple.ci",
            "mot_de_passe": "Riverain@2026",
            "latitude": LAT_PROCHE,
            "longitude": LON_PROCHE,
        })
        assert reponse.status_code == 200
        assert reponse.json()["role"] == "PLAIGNANT"
        assert reponse.json()["access_token"]

    def test_inscription_refusee_hors_zone(self, client, chantier_positionne):
        reponse = client.post("/citoyen/inscription", json={
            "nom": "Trop Loin",
            "email": "trop.loin@exemple.ci",
            "mot_de_passe": "Riverain@2026",
            "latitude": LAT_LOIN,
            "longitude": LON_LOIN,
        })
        assert reponse.status_code == 403
        assert "riverains" in reponse.json()["detail"].lower()

    def test_le_rattachement_est_deduit_de_la_position(
        self, client, db_session, chantier_positionne
    ):
        """Le riverain ne choisit pas son chantier, il en herite."""
        client.post("/citoyen/inscription", json={
            "nom": "Yao Beatrice",
            "email": "yao.beatrice@exemple.ci",
            "mot_de_passe": "Riverain@2026",
            "latitude": LAT_PROCHE,
            "longitude": LON_PROCHE,
        })
        cree = db_session.query(models.Utilisateur).filter_by(
            email="yao.beatrice@exemple.ci"
        ).first()
        assert cree.chantier_rattachement_id == chantier_positionne.id

    def test_adresse_deja_utilisee_refusee(self, client, chantier_positionne, riverain):
        reponse = client.post("/citoyen/inscription", json={
            "nom": "Doublon",
            "email": riverain.email,
            "mot_de_passe": "Riverain@2026",
            "latitude": LAT_PROCHE,
            "longitude": LON_PROCHE,
        })
        assert reponse.status_code == 400


class TestDoleances:
    """Depot et suivi des doleances par le riverain."""

    def test_depot_d_une_doleance(self, client, riverain_headers, chantier_positionne):
        reponse = client.post("/citoyen/doleances", headers=riverain_headers, json={
            "description": "Poussiere importante devant l'ecole depuis une semaine.",
            "categorie": "poussiere",
            "latitude": LAT_PROCHE,
            "longitude": LON_PROCHE,
        })
        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["statut"] == "OUVERTE"
        assert corps["canal"] == "MOBILE"

    def test_la_doleance_rejoint_la_file_du_suivi_social(
        self, client, riverain_headers, chantier_positionne, db_session
    ):
        """Le depot mobile alimente le meme registre que le guichet."""
        client.post("/citoyen/doleances", headers=riverain_headers, json={
            "description": "Bruit nocturne des engins apres vingt-deux heures.",
            "categorie": "bruit",
        })
        enregistree = db_session.query(models.Plainte).first()
        assert enregistree is not None
        assert enregistree.canal == "MOBILE"
        assert enregistree.chantier_id == chantier_positionne.id

    def test_le_riverain_ne_voit_que_ses_propres_doleances(
        self, client, riverain_headers, riverain, chantier_positionne, db_session
    ):
        db_session.add(models.Plainte(
            nom_plaignant="Quelqu'un d'autre",
            description="Doleance d'un tiers, deposee au guichet.",
            statut="OUVERTE",
            chantier_id=chantier_positionne.id,
            canal="GUICHET",
        ))
        db_session.commit()

        client.post("/citoyen/doleances", headers=riverain_headers, json={
            "description": "Eaux stagnantes au carrefour depuis les pluies.",
            "categorie": "eau",
        })

        mes = client.get("/citoyen/doleances", headers=riverain_headers).json()
        assert len(mes) == 1
        assert "Eaux stagnantes" in mes[0]["description"]

    def test_un_agent_ageroute_n_accede_pas_a_l_espace_citoyen(
        self, client, agent_headers
    ):
        """Les deux applications restent cloisonnees."""
        reponse = client.get("/citoyen/doleances", headers=agent_headers)
        assert reponse.status_code == 403


class TestChantierDeRattachement:
    """Consultation du chantier auquel le riverain est rattache.

    Ce point etait le seul du parcours a n'avoir aucune couverture, et c'est
    precisement la qu'un defaut s'est manifeste en production : l'endpoint
    renvoyait l'objet complet du chantier, geometrie PostGIS comprise, que la
    serialisation ne savait pas convertir. L'ecran de profil affichait donc une
    erreur alors que l'inscription et le depot fonctionnaient.
    """

    def test_le_riverain_consulte_son_rattachement(
        self, client, riverain_headers, chantier_positionne
    ):
        reponse = client.get("/citoyen/mon-chantier", headers=riverain_headers)
        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["nom"] == "Bd Latrille"
        assert corps["commune"] == "Cocody"

    def test_la_reponse_se_limite_a_ce_qui_est_affiche(
        self, client, riverain_headers, chantier_positionne
    ):
        """La geometrie n'a pas a figurer dans une reponse que personne ne lit."""
        corps = client.get("/citoyen/mon-chantier", headers=riverain_headers).json()
        assert set(corps.keys()) == {"id", "nom", "commune"}

    def test_un_agent_n_accede_pas_a_cet_espace(self, client, agent_headers):
        reponse = client.get("/citoyen/mon-chantier", headers=agent_headers)
        assert reponse.status_code == 403
