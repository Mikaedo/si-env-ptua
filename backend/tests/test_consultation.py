"""
test_consultation.py
--------------------
Verifie que les profils de consultation, l'ANDE et la BAD, peuvent lire le
dispositif sans jamais pouvoir le modifier.

Cette separation n'est pas cosmetique. Le regulateur national et le bailleur
doivent pouvoir verifier ce que le maitre d'ouvrage declare, mais un rapport
de conformite perdrait toute valeur si celui qui le controle pouvait retoucher
les donnees qu'il examine. Les tests ci-dessous s'attachent donc a prouver que
la restriction tient au niveau du serveur, et pas seulement dans l'interface :
les requetes sont emises directement contre l'API, comme le ferait quelqu'un
qui contournerait le tableau de bord.
"""


class TestConsultationLecture:
    """Ce que l'ANDE et la BAD doivent pouvoir consulter."""

    def test_ande_consulte_les_signalements(self, client, ande_headers):
        reponse = client.get("/signalements", headers=ande_headers)
        assert reponse.status_code == 200
        assert isinstance(reponse.json(), list)

    def test_ande_consulte_les_chantiers(self, client, ande_headers, chantier):
        reponse = client.get("/chantiers", headers=ande_headers)
        assert reponse.status_code == 200
        noms = [c["nom"] for c in reponse.json()]
        assert chantier.nom in noms

    def test_bad_consulte_les_statistiques(self, client, bad_headers):
        reponse = client.get("/stats", headers=bad_headers)
        assert reponse.status_code == 200

    def test_bad_consulte_les_plaintes(self, client, bad_headers):
        """Le volet social releve de la sauvegarde operationnelle 2 du bailleur."""
        reponse = client.get("/plaintes", headers=bad_headers)
        assert reponse.status_code == 200


class TestConsultationEcritureRefusee:
    """Toute tentative d'ecriture doit etre repoussee, quel que soit le chemin."""

    def test_ande_ne_peut_pas_creer_de_chantier(self, client, ande_headers):
        reponse = client.post(
            "/chantiers",
            headers=ande_headers,
            json={"nom": "Chantier fantome", "commune": "Cocody"},
        )
        assert reponse.status_code == 403

    def test_bad_ne_peut_pas_creer_de_signalement(self, client, bad_headers, chantier):
        reponse = client.post(
            "/signalements",
            headers=bad_headers,
            json={
                "uuid_mobile": "tentative-001",
                "type_nuisance": "Poussiere",
                "description": "Depuis un profil de consultation",
                "criticite": "MODERE",
                "chantier_id": chantier.id,
            },
        )
        assert reponse.status_code == 403

    def test_ande_ne_peut_pas_supprimer(self, client, ande_headers, chantier):
        reponse = client.delete(f"/chantiers/{chantier.id}", headers=ande_headers)
        assert reponse.status_code == 403

    def test_bad_ne_peut_pas_modifier_un_statut(self, client, bad_headers):
        reponse = client.patch(
            "/plaintes/1/statut",
            headers=bad_headers,
            json={"statut": "RESOLU"},
        )
        assert reponse.status_code == 403

    def test_le_refus_est_explicite(self, client, ande_headers):
        """Le message doit orienter la personne, pas la laisser devant un mur."""
        reponse = client.post(
            "/chantiers",
            headers=ande_headers,
            json={"nom": "Test", "commune": "Test"},
        )
        assert "consultation" in reponse.json()["detail"].lower()


class TestConsultationNAffectePasLesAutres:
    """La restriction ne doit peser que sur les deux profils concernes."""

    def test_admin_cree_toujours_un_chantier(self, client, auth_headers):
        reponse = client.post(
            "/chantiers",
            headers=auth_headers,
            json={"nom": "Echangeur Riviera", "commune": "Cocody"},
        )
        assert reponse.status_code in (200, 201)

    def test_un_consultant_change_son_propre_mot_de_passe(self, client, ande_headers):
        """Le verrou porte sur les donnees du projet, pas sur le compte lui-meme.

        Interdire cette operation enfermerait un consultant hors de sa propre
        session des lors qu'on lui demanderait de renouveler son mot de passe.
        """
        reponse = client.post(
            "/auth/change-password",
            headers=ande_headers,
            json={
                "ancien_mot_de_passe": "ande123",
                "nouveau_mot_de_passe": "NouveauMdp@2026",
            },
        )
        assert reponse.status_code == 200
