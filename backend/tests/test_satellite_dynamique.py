"""
test_satellite_dynamique.py
---------------------------
Verifie que l'analyse satellitaire suit le referentiel des chantiers tenu en
base, et non une liste figee dans le code.

Le suivi environnemental d'un programme routier n'a rien de fige : des
tranches s'ouvrent, d'autres s'achevent, et le perimetre evolue sur la duree
du projet. Une liste ecrite en dur dans le code obligeait a redeployer
l'application pour en tenir compte, et le specialiste environnemental ne
pouvait donc pas exercer sa propre responsabilite sans intervention technique.
Les tests ci-dessous portent sur ce lien : ce qui est configure doit etre ce
qui est analyse.

Les appels a Earth Engine ne sont pas sollicites ici. On verifie le
referentiel et le controle des identifiants, pas l'extraction des indices, qui
supposerait un acces reseau et des identifiants Google.
"""
from app.services.geo_service import (
    chantiers_geolocalises,
    chantier_geolocalise,
    coordonnees_de,
)
from app import models


class TestReferentielGeographique:
    """Lecture des chantiers depuis la base."""

    def test_un_chantier_positionne_est_retourne(self, db_session):
        db_session.add(models.Chantier(
            nom="Rocade Y4", commune="Yopougon",
            geom="SRID=4326;POINT(-4.048 5.372)",
        ))
        db_session.commit()

        liste = chantiers_geolocalises(db_session)
        assert len(liste) == 1
        assert liste[0]["nom"] == "Rocade Y4"
        assert abs(liste[0]["lat"] - 5.372) < 0.001
        assert abs(liste[0]["lon"] - (-4.048)) < 0.001

    def test_un_chantier_sans_position_est_ecarte(self, db_session):
        """Interroger Earth Engine sans emprise n'aurait aucun sens."""
        db_session.add(models.Chantier(nom="Chantier non localisé", commune="Abidjan"))
        db_session.commit()
        assert chantiers_geolocalises(db_session) == []

    def test_un_chantier_ajoute_apparait_aussitot(self, db_session):
        """Le reproche d'origine : un ajout restait invisible de l'analyse."""
        db_session.add(models.Chantier(
            nom="Rocade Y4", commune="Yopougon",
            geom="SRID=4326;POINT(-4.048 5.372)",
        ))
        db_session.commit()
        assert len(chantiers_geolocalises(db_session)) == 1

        db_session.add(models.Chantier(
            nom="Nouvelle tranche", commune="Abobo",
            geom="SRID=4326;POINT(-4.020 5.420)",
        ))
        db_session.commit()

        noms = [c["nom"] for c in chantiers_geolocalises(db_session)]
        assert "Nouvelle tranche" in noms

    def test_un_chantier_retire_cesse_d_etre_suivi(self, db_session):
        chantier = models.Chantier(
            nom="Tranche achevée", commune="Cocody",
            geom="SRID=4326;POINT(-3.974 5.348)",
        )
        db_session.add(chantier)
        db_session.commit()
        assert len(chantiers_geolocalises(db_session)) == 1

        db_session.delete(chantier)
        db_session.commit()
        assert chantiers_geolocalises(db_session) == []

    def test_les_identifiants_ne_sont_pas_supposes_contigus(self, db_session):
        """L'ancienne validation bornait les identifiants entre un et six.

        Elle devenait fausse des la premiere suppression, un identifiant
        PostgreSQL n'etant jamais reattribue.
        """
        premier = models.Chantier(
            nom="Premier", commune="A", geom="SRID=4326;POINT(-4.0 5.3)",
        )
        second = models.Chantier(
            nom="Second", commune="B", geom="SRID=4326;POINT(-4.1 5.4)",
        )
        db_session.add_all([premier, second])
        db_session.commit()

        identifiant_conserve = second.id
        db_session.delete(premier)
        db_session.commit()

        trouve = chantier_geolocalise(db_session, identifiant_conserve)
        assert trouve is not None
        assert trouve["nom"] == "Second"

    def test_chantier_inconnu_retourne_none(self, db_session):
        assert chantier_geolocalise(db_session, 9999) is None


class TestExtractionCoordonnees:
    """Lecture de la geometrie, quel que soit le moteur de base."""

    def test_position_absente(self, db_session):
        assert coordonnees_de(models.Chantier(nom="Sans position")) is None

    def test_ordre_latitude_longitude_respecte(self, db_session):
        """Abidjan se situe au nord de l'equateur et a l'ouest de Greenwich.

        Une inversion des deux valeurs placerait les chantiers au large du
        Ghana sans qu'aucune erreur ne soit levee, d'ou ce controle explicite.
        """
        chantier = models.Chantier(
            nom="Bd Latrille", geom="SRID=4326;POINT(-3.974 5.348)",
        )
        latitude, longitude = coordonnees_de(chantier)
        assert latitude > 0      # hemisphere nord
        assert longitude < 0     # hemisphere ouest


class TestAccesApi:
    """Habilitations sur le referentiel expose par l'API satellitaire."""

    def test_le_specialiste_environnemental_accede(self, client, db_session, spec_env_headers):
        db_session.add(models.Chantier(
            nom="Rocade Y4", commune="Yopougon",
            geom="SRID=4326;POINT(-4.048 5.372)",
        ))
        db_session.commit()

        reponse = client.get("/satellite/chantiers", headers=spec_env_headers)
        assert reponse.status_code == 200
        assert reponse.json()[0]["nom"] == "Rocade Y4"

    def test_les_consultants_accedent_aussi(self, client, db_session, ande_headers):
        db_session.add(models.Chantier(
            nom="Rocade Y4", commune="Yopougon",
            geom="SRID=4326;POINT(-4.048 5.372)",
        ))
        db_session.commit()

        reponse = client.get("/satellite/chantiers", headers=ande_headers)
        assert reponse.status_code == 200

    def test_un_agent_de_terrain_n_y_accede_pas(self, client, agent_headers):
        reponse = client.get("/satellite/chantiers", headers=agent_headers)
        assert reponse.status_code == 403
