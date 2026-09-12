"""L'heure du constat terrain prime sur l'heure de reception.

Le serveur horodatait a la reception. Un agent relevant une nuisance a
7h dans une zone sans couverture, et la transmettant a 18h en rentrant,
la voyait s'afficher a 18h : donc apres le constat d'un collegue releve
a 8h avec du reseau. Le tableau de bord inversait l'ordre des faits, ce
qui n'est pas tenable pour un suivi environnemental ou la chronologie
des constats est justement ce qu'on documente.

Les deux dates sont desormais conservees : saisi_le dit quand la
nuisance a ete vue, cree_le quand le systeme l'a su.
"""

from datetime import datetime, timedelta


def _corps(uuid, saisi_le=None, **extra):
    corps = {
        "uuid_mobile": uuid,
        "type_nuisance": "Déchets de chantier",
        "criticite": "FAIBLE",
        "latitude": 5.35,
        "longitude": -4.02,
    }
    if saisi_le is not None:
        corps["saisi_le"] = saisi_le.isoformat()
    corps.update(extra)
    return corps


class TestHeureDuConstat:
    def test_l_heure_de_saisie_est_conservee(self, client, agent_headers):
        sept_heures = datetime(2026, 9, 12, 7, 0, 0)
        r = client.post("/signalements",
                        json=_corps("u-7h", saisi_le=sept_heures),
                        headers=agent_headers)
        assert r.status_code == 200
        assert r.json()["saisi_le"].startswith("2026-09-12T07:00")

    def test_l_heure_de_reception_reste_distincte(self, client, agent_headers):
        """Les deux dates coexistent : le systeme sait quand il a su."""
        hier = datetime.utcnow() - timedelta(days=1)
        r = client.post("/signalements",
                        json=_corps("u-hier", saisi_le=hier),
                        headers=agent_headers)
        corps = r.json()
        assert corps["saisi_le"] != corps["cree_le"]
        # La reception est d'aujourd'hui, le constat d'hier.
        assert corps["cree_le"] > corps["saisi_le"]

    def test_le_constat_hors_ligne_precede_celui_transmis_apres(
            self, client, agent_headers):
        """Le cas rapporte : 7h sans reseau contre 8h avec reseau.

        Le constat de 7h est transmis en dernier, mais il doit rester
        devant celui de 8h dans la liste.
        """
        client.post("/signalements",
                    json=_corps("u-8h", saisi_le=datetime(2026, 9, 12, 8, 0)),
                    headers=agent_headers)
        # Transmis apres, mais releve avant.
        client.post("/signalements",
                    json=_corps("u-7h", saisi_le=datetime(2026, 9, 12, 7, 0)),
                    headers=agent_headers)

        liste = client.get("/signalements", headers=agent_headers).json()
        uuids = [s["uuid_mobile"] for s in liste
                 if s["uuid_mobile"] in ("u-7h", "u-8h")]
        # Tri decroissant : le plus recent d'abord, donc 8h avant 7h.
        assert uuids == ["u-8h", "u-7h"]

    def test_sans_date_envoyee_le_serveur_horodate(self, client, agent_headers):
        """Une version anterieure de l'application n'envoie pas la date.

        Le constat ne doit pas pour autant arriver sans date : on retient
        l'heure de reception, faute de mieux.
        """
        r = client.post("/signalements", json=_corps("u-sans-date"),
                        headers=agent_headers)
        assert r.status_code == 200
        assert r.json()["saisi_le"] is not None

    def test_le_renvoi_du_meme_constat_ne_change_pas_sa_date(
            self, client, agent_headers):
        """L'idempotence porte aussi sur la date.

        Une synchronisation rejouee ne doit pas redater le constat a
        l'heure du rejeu, sans quoi la chronologie se deplacerait a
        chaque tentative d'envoi.
        """
        sept = datetime(2026, 9, 12, 7, 0)
        premier = client.post("/signalements",
                              json=_corps("u-rejeu", saisi_le=sept),
                              headers=agent_headers).json()
        second = client.post("/signalements",
                             json=_corps("u-rejeu", saisi_le=datetime.utcnow()),
                             headers=agent_headers).json()
        assert second["id"] == premier["id"]
        assert second["saisi_le"] == premier["saisi_le"]
