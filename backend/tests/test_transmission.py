"""
test_transmission.py
--------------------
Couvre la remise formelle d'un rapport a un organisme de controle.

L'ANDE et la BAD consultent le dispositif en continu, ce qui pourrait laisser
croire que la transmission d'un rapport n'a plus d'objet. Elle en garde un :
un auditeur ne reclame pas le document, qu'il peut ouvrir quand il veut, il
reclame la preuve de la date a laquelle il lui a ete adresse et de la personne
qui l'a fait. La trace est donc le vrai livrable, l'envoi n'en etant que le
moyen. Les tests portent en consequence autant sur ce qui est enregistre que
sur ce qui est expedie.
"""
import pytest

from app import models


@pytest.fixture(autouse=True)
def messagerie_simulee(monkeypatch):
    """Intercepte l'envoi pour ne pas dependre du reseau pendant les tests.

    La fonction de remplacement conserve ses arguments, ce qui permet de
    verifier que la piece jointe est bien constituee et non simplement
    annoncee.
    """
    envois = []

    def _faux_envoi(destinataire, sujet, html, texte, piece_jointe=None):
        envois.append({
            "destinataire": destinataire,
            "sujet": sujet,
            "html": html,
            "texte": texte,
            "piece_jointe": piece_jointe,
        })
        return True

    monkeypatch.setattr("app.routers.rapports_router.envoyer_email", _faux_envoi)
    return envois


@pytest.fixture
def chantier_suivi(db_session):
    c = models.Chantier(
        nom="Rocade Y4", commune="Yopougon",
        geom="SRID=4326;POINT(-4.048 5.372)",
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


class TestTransmission:
    """Remise du rapport et constitution de la trace."""

    def test_le_specialiste_transmet_a_l_agence(
        self, client, spec_env_headers, chantier_suivi, messagerie_simulee
    ):
        reponse = client.post("/rapports/transmettre", headers=spec_env_headers, json={
            "chantier_ids": [chantier_suivi.id],
            "date_debut": "2026-01-01",
            "date_fin": "2026-06-30",
            "entreprise_destinataire": "ANDE",
        })
        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["succes"] is True
        assert corps["organisme"] == "ANDE"
        assert len(messagerie_simulee) == 1

    def test_l_adresse_institutionnelle_est_retenue_par_defaut(
        self, client, spec_env_headers, chantier_suivi, messagerie_simulee
    ):
        """L'utilisateur n'a pas a connaitre par coeur l'adresse du bailleur."""
        client.post("/rapports/transmettre", headers=spec_env_headers, json={
            "chantier_ids": [chantier_suivi.id],
            "entreprise_destinataire": "BAD",
        })
        assert messagerie_simulee[0]["destinataire"] == "mission@afdb.org"

    def test_une_adresse_explicite_prime(
        self, client, spec_env_headers, chantier_suivi, messagerie_simulee
    ):
        client.post("/rapports/transmettre", headers=spec_env_headers, json={
            "chantier_ids": [chantier_suivi.id],
            "entreprise_destinataire": "ANDE",
            "destinataire_email": "Inspecteur.Terrain@ANDE.CI",
        })
        # Normalisee en minuscules, plusieurs services de messagerie refusant
        # les adresses comportant des majuscules.
        assert messagerie_simulee[0]["destinataire"] == "inspecteur.terrain@ande.ci"

    def test_le_rapport_part_en_piece_jointe(
        self, client, spec_env_headers, chantier_suivi, messagerie_simulee
    ):
        """Un rapport se remet, il ne s'annonce pas par un lien a suivre."""
        client.post("/rapports/transmettre", headers=spec_env_headers, json={
            "chantier_ids": [chantier_suivi.id],
            "entreprise_destinataire": "ANDE",
        })
        nom, contenu = messagerie_simulee[0]["piece_jointe"]
        assert nom.endswith(".pdf")
        assert contenu.startswith(b"%PDF")

    def test_le_courriel_recapitule_les_chiffres(
        self, client, spec_env_headers, chantier_suivi, messagerie_simulee
    ):
        """Le destinataire doit saisir l'essentiel sans ouvrir la piece jointe."""
        client.post("/rapports/transmettre", headers=spec_env_headers, json={
            "chantier_ids": [chantier_suivi.id],
            "entreprise_destinataire": "ANDE",
        })
        assert "Rocade Y4" in messagerie_simulee[0]["html"]
        assert "Rocade Y4" in messagerie_simulee[0]["texte"]

    def test_sans_chantier_la_transmission_est_refusee(
        self, client, spec_env_headers, messagerie_simulee
    ):
        reponse = client.post("/rapports/transmettre", headers=spec_env_headers, json={
            "chantier_ids": [],
            "entreprise_destinataire": "ANDE",
        })
        assert reponse.status_code == 400
        assert messagerie_simulee == []


class TestTraceConservee:
    """Ce que l'historique doit retenir."""

    def test_la_trace_est_enregistree(
        self, client, spec_env_headers, chantier_suivi, db_session, messagerie_simulee
    ):
        client.post("/rapports/transmettre", headers=spec_env_headers, json={
            "chantier_ids": [chantier_suivi.id],
            "date_debut": "2026-01-01",
            "date_fin": "2026-06-30",
            "entreprise_destinataire": "ANDE",
        })
        trace = db_session.query(models.TransmissionRapport).first()
        assert trace is not None
        assert trace.emetteur_email == "spec.env@test.com"
        assert trace.destinataire_email == "controle@ande.ci"
        assert trace.periode_debut == "2026-01-01"
        assert trace.taille_octets > 0

    def test_un_echec_laisse_aussi_une_trace(
        self, client, spec_env_headers, chantier_suivi, db_session, monkeypatch
    ):
        """Sans cet enregistrement, une remise perdue en route passerait pour
        n'avoir jamais ete tentee, ce qui est precisement le contraire de ce
        qu'un dispositif de tracabilite doit garantir."""
        monkeypatch.setattr(
            "app.routers.rapports_router.envoyer_email",
            lambda *a, **k: False,
        )
        reponse = client.post("/rapports/transmettre", headers=spec_env_headers, json={
            "chantier_ids": [chantier_suivi.id],
            "entreprise_destinataire": "ANDE",
        })
        assert reponse.status_code == 502

        trace = db_session.query(models.TransmissionRapport).first()
        assert trace is not None
        assert trace.succes is False
        assert trace.detail_erreur

    def test_l_historique_est_consultable(
        self, client, spec_env_headers, chantier_suivi, messagerie_simulee
    ):
        client.post("/rapports/transmettre", headers=spec_env_headers, json={
            "chantier_ids": [chantier_suivi.id],
            "entreprise_destinataire": "ANDE",
        })
        reponse = client.get("/rapports/transmissions", headers=spec_env_headers)
        assert reponse.status_code == 200
        assert len(reponse.json()) == 1

    def test_les_organismes_consultent_l_historique(
        self, client, ande_headers, spec_env_headers, chantier_suivi, messagerie_simulee
    ):
        """Verifier ce qui leur a ete adresse fait partie de leur mission."""
        client.post("/rapports/transmettre", headers=spec_env_headers, json={
            "chantier_ids": [chantier_suivi.id],
            "entreprise_destinataire": "ANDE",
        })
        reponse = client.get("/rapports/transmissions", headers=ande_headers)
        assert reponse.status_code == 200
        assert len(reponse.json()) == 1


class TestHabilitations:
    """Qui peut transmettre, et qui ne le peut pas."""

    def test_un_organisme_ne_transmet_pas_a_lui_meme(
        self, client, ande_headers, chantier_suivi, messagerie_simulee
    ):
        """Transmettre engage l'AGEROUTE devant son regulateur.

        Laisser le destinataire produire lui-meme la remise qu'il est cense
        recevoir vaudrait un blanc-seing, et la trace perdrait toute portee.
        """
        reponse = client.post("/rapports/transmettre", headers=ande_headers, json={
            "chantier_ids": [chantier_suivi.id],
            "entreprise_destinataire": "ANDE",
        })
        assert reponse.status_code == 403
        assert messagerie_simulee == []

    def test_un_agent_de_terrain_ne_transmet_pas(
        self, client, agent_headers, chantier_suivi, messagerie_simulee
    ):
        reponse = client.post("/rapports/transmettre", headers=agent_headers, json={
            "chantier_ids": [chantier_suivi.id],
            "entreprise_destinataire": "ANDE",
        })
        assert reponse.status_code == 403
