"""
test_non_conformites.py
-----------------------
Verifie le suivi des non-conformites, le besoin BF-09 du memoire.

Ce besoin confie au Specialiste Suivi Environnemental et a l'Expert HSE le
soin de « suivre les non-conformites », et le tableau 3.2 precise que
l'Expert HSE « consigne les non-conformites relevees lors du controle
contradictoire ». La table existait pourtant sans qu'aucune route ne
permette d'y inscrire quoi que ce soit : le besoin etait declare, modelise,
et jamais realise.

L'ecart se distingue de l'action corrective, et c'est ce qui justifie une
entite propre. L'action dit ce qu'il faut faire et sous quel delai ; la
non-conformite dit ce qui n'est pas conforme, et se leve quand la mise en
conformite est constatee. Un signalement peut porter plusieurs ecarts, de
severites differentes.

Les tests portent donc sur trois choses : qui peut consigner un ecart, qui
peut seulement le lire, et la regle qui interdit de clore un dossier dont
un ecart subsiste. Cette derniere est la plus importante : un rapport
transmis au bailleur declarerait resolu ce qui ne l'est pas.
"""


def _signalement(client, entetes, chantier):
    """Cree un signalement et renvoie son identifiant."""
    reponse = client.post(
        "/signalements",
        headers=entetes,
        json={
            "uuid_mobile": "nc-test-0001",
            "type_nuisance": "Déchets de chantier",
            "description": "Dépôt constaté en bordure de voie.",
            "criticite": "ELEVE",
            "gps_source": "AUTO",
            "latitude": 5.3547,
            "longitude": -3.8853,
            "chantier_id": chantier.id,
        },
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


class TestConsignerUnEcart:
    """Qui peut inscrire une non-conformite, et sous quelle forme."""

    def test_expert_hse_consigne_un_ecart(
            self, client, expert_headers, agent_headers, chantier):
        """Le cas central du BF-09 : l'Expert HSE constate et consigne."""
        sid = _signalement(client, agent_headers, chantier)
        reponse = client.post(
            f"/signalements/{sid}/non-conformites",
            headers=expert_headers,
            json={"description": "Absence de benne de chantier sur le site.",
                  "severite": "ELEVEE"},
        )
        assert reponse.status_code == 200, reponse.text
        ecart = reponse.json()
        assert ecart["severite"] == "ELEVEE"
        assert ecart["resolue"] is False
        assert ecart["signalement_id"] == sid

    def test_un_ecart_ouvre_le_traitement(
            self, client, expert_headers, agent_headers, chantier):
        """Un controle a eu lieu : le dossier ne peut plus etre « nouveau »."""
        sid = _signalement(client, agent_headers, chantier)
        client.post(
            f"/signalements/{sid}/non-conformites",
            headers=expert_headers,
            json={"description": "Stockage de sacs de ciment à l'air libre."},
        )
        detail = client.get(f"/signalements/{sid}",
                            headers=expert_headers).json()
        assert detail["statut"] == "EN_TRAITEMENT"

    def test_severite_par_defaut(
            self, client, expert_headers, agent_headers, chantier):
        sid = _signalement(client, agent_headers, chantier)
        reponse = client.post(
            f"/signalements/{sid}/non-conformites",
            headers=expert_headers,
            json={"description": "Signalisation de chantier incomplète."},
        )
        assert reponse.json()["severite"] == "MOYENNE"

    def test_severite_invalide_refusee(
            self, client, expert_headers, agent_headers, chantier):
        """Une valeur hors nomenclature doit etre refusee, non enregistree.

        Sans ce controle, une severite libre se retrouverait dans le
        rapport du bailleur, ou elle ne se compare a rien.
        """
        sid = _signalement(client, agent_headers, chantier)
        reponse = client.post(
            f"/signalements/{sid}/non-conformites",
            headers=expert_headers,
            json={"description": "Écart constaté sur le site.",
                  "severite": "CATASTROPHIQUE"},
        )
        assert reponse.status_code == 422
        assert "Sévérité invalide" in reponse.json()["detail"]

    def test_description_trop_courte_refusee(
            self, client, expert_headers, agent_headers, chantier):
        sid = _signalement(client, agent_headers, chantier)
        reponse = client.post(
            f"/signalements/{sid}/non-conformites",
            headers=expert_headers,
            json={"description": "RAS"},
        )
        assert reponse.status_code == 422

    def test_signalement_inexistant(self, client, expert_headers):
        reponse = client.post(
            "/signalements/999999/non-conformites",
            headers=expert_headers,
            json={"description": "Écart sur un dossier qui n'existe pas."},
        )
        assert reponse.status_code == 404


class TestQuiPeutConsigner:
    """Le BF-09 reserve le constat a deux profils."""

    def test_agent_ne_consigne_pas(
            self, client, agent_headers, chantier):
        """Le Responsable Environnement signale, il ne constate pas d'ecart.

        Il appartient a l'entreprise de travaux : lui laisser consigner
        ses propres non-conformites viderait le controle de son sens.
        """
        sid = _signalement(client, agent_headers, chantier)
        reponse = client.post(
            f"/signalements/{sid}/non-conformites",
            headers=agent_headers,
            json={"description": "Écart que l'agent voudrait consigner."},
        )
        assert reponse.status_code == 403

    def test_ande_ne_consigne_pas(
            self, client, ande_headers, agent_headers, chantier):
        """L'ANDE controle sans ecrire : la restriction tient au serveur."""
        sid = _signalement(client, agent_headers, chantier)
        reponse = client.post(
            f"/signalements/{sid}/non-conformites",
            headers=ande_headers,
            json={"description": "Écart relevé par le régulateur."},
        )
        assert reponse.status_code == 403

    def test_bad_ne_consigne_pas(
            self, client, bad_headers, agent_headers, chantier):
        sid = _signalement(client, agent_headers, chantier)
        reponse = client.post(
            f"/signalements/{sid}/non-conformites",
            headers=bad_headers,
            json={"description": "Écart relevé par le bailleur."},
        )
        assert reponse.status_code == 403


class TestLireLesEcarts:
    """La lecture est ouverte a ceux qui accedent au dossier."""

    def test_ande_lit_les_ecarts(
            self, client, ande_headers, expert_headers, agent_headers,
            chantier):
        """Un ecart consigne est precisement ce que le regulateur controle."""
        sid = _signalement(client, agent_headers, chantier)
        client.post(
            f"/signalements/{sid}/non-conformites",
            headers=expert_headers,
            json={"description": "Absence de bâchage des camions."},
        )
        reponse = client.get(f"/signalements/{sid}/non-conformites",
                             headers=ande_headers)
        assert reponse.status_code == 200
        assert len(reponse.json()) == 1

    def test_plusieurs_ecarts_du_plus_recent(
            self, client, expert_headers, agent_headers, chantier):
        sid = _signalement(client, agent_headers, chantier)
        for texte in ("Premier écart constaté sur le site.",
                      "Second écart constaté sur le site."):
            client.post(f"/signalements/{sid}/non-conformites",
                        headers=expert_headers,
                        json={"description": texte})
        liste = client.get(f"/signalements/{sid}/non-conformites",
                           headers=expert_headers).json()
        assert len(liste) == 2

    def test_aucun_ecart_renvoie_une_liste_vide(
            self, client, expert_headers, agent_headers, chantier):
        sid = _signalement(client, agent_headers, chantier)
        reponse = client.get(f"/signalements/{sid}/non-conformites",
                             headers=expert_headers)
        assert reponse.status_code == 200
        assert reponse.json() == []


class TestLeverUnEcart:
    """La mise en conformite se constate, elle ne se suppose pas."""

    def test_expert_leve_un_ecart(
            self, client, expert_headers, agent_headers, chantier):
        sid = _signalement(client, agent_headers, chantier)
        ecart = client.post(
            f"/signalements/{sid}/non-conformites",
            headers=expert_headers,
            json={"description": "Benne absente du site."},
        ).json()

        reponse = client.patch(
            f"/signalements/non-conformites/{ecart['id']}/resoudre",
            headers=expert_headers)
        assert reponse.status_code == 200
        assert reponse.json()["resolue"] is True

    def test_agent_ne_leve_pas(
            self, client, expert_headers, agent_headers, chantier):
        sid = _signalement(client, agent_headers, chantier)
        ecart = client.post(
            f"/signalements/{sid}/non-conformites",
            headers=expert_headers,
            json={"description": "Écart en attente de levée."},
        ).json()
        reponse = client.patch(
            f"/signalements/non-conformites/{ecart['id']}/resoudre",
            headers=agent_headers)
        assert reponse.status_code == 403

    def test_ecart_inexistant(self, client, expert_headers):
        reponse = client.patch(
            "/signalements/non-conformites/999999/resoudre",
            headers=expert_headers)
        assert reponse.status_code == 404


class TestClotureEtEcartsOuverts:
    """La regle qui protege le rapport transmis au bailleur."""

    def _avec_action(self, client, entetes, sid):
        """Une action corrective, sans quoi la cloture echoue deja."""
        client.post(f"/signalements/{sid}/action", headers=entetes,
                    json={"description": "Injonction notifiée à l'entreprise."})

    def test_cloture_refusee_si_un_ecart_reste_ouvert(
            self, client, expert_headers, agent_headers, chantier):
        """Le cas qui compte.

        Cloturer un dossier dont une non-conformite subsiste ferait
        mentir le rapport : il declarerait resolu ce qui ne l'est pas.
        """
        sid = _signalement(client, agent_headers, chantier)
        self._avec_action(client, expert_headers, sid)
        client.post(f"/signalements/{sid}/non-conformites",
                    headers=expert_headers,
                    json={"description": "Écart non encore levé."})

        reponse = client.patch(f"/signalements/{sid}/statut",
                               headers=expert_headers,
                               json={"statut": "CLOTURE"})
        assert reponse.status_code == 409
        assert "non-conformité" in reponse.json()["detail"].lower()

    def test_cloture_admise_une_fois_les_ecarts_leves(
            self, client, expert_headers, agent_headers, chantier):
        sid = _signalement(client, agent_headers, chantier)
        self._avec_action(client, expert_headers, sid)
        ecart = client.post(
            f"/signalements/{sid}/non-conformites",
            headers=expert_headers,
            json={"description": "Écart à lever avant clôture."},
        ).json()

        client.patch(
            f"/signalements/non-conformites/{ecart['id']}/resoudre",
            headers=expert_headers)

        reponse = client.patch(f"/signalements/{sid}/statut",
                               headers=expert_headers,
                               json={"statut": "CLOTURE"})
        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["statut"] == "CLOTURE"

    def test_cloture_admise_sans_aucun_ecart(
            self, client, expert_headers, agent_headers, chantier):
        """La regle ajoutee ne doit pas bloquer un dossier sans ecart."""
        sid = _signalement(client, agent_headers, chantier)
        self._avec_action(client, expert_headers, sid)
        reponse = client.patch(f"/signalements/{sid}/statut",
                               headers=expert_headers,
                               json={"statut": "CLOTURE"})
        assert reponse.status_code == 200, reponse.text
