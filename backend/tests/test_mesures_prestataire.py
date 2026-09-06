"""
test_mesures_prestataire.py
---------------------------
Verifie la saisie des mesures du prestataire agree, le besoin BF-08.

Ce besoin est le dernier des quatorze a avoir ete realise, et il comble
un manque que le memoire signale lui-meme : l'observation de l'agent et
le releve satellitaire ne valent pas mesure. Le bruit s'evaluait a
l'oreille faute de sonometre, les poussieres ne se mesuraient pas.

Un laboratoire accredite intervient pourtant sur les chantiers, et ses
resultats sont ce que la Banque africaine de developpement reconnait.
Ils restaient sur papier, hors du dispositif.

Les tests portent sur ce qui rend une mesure opposable : le bon
parametre, la bonne unite, une date de prelevement plausible, un
laboratoire nomme, et le verdict de conformite au regard de la valeur
limite reglementaire. Une mesure fausse dans un rapport de conformite
est pire qu'une mesure absente : elle se compare, se moyenne, et fonde
une conclusion.
"""
from datetime import datetime, timedelta


def _mesure(chantier, parametre="BRUIT", valeur=72.5, jours=3, **extra):
    """Le corps d'une mesure, avec des valeurs plausibles par defaut."""
    corps = {
        "parametre": parametre,
        "valeur": valeur,
        "date_prelevement": (datetime.utcnow()
                             - timedelta(days=jours)).isoformat(),
        "laboratoire": "CIAPOL, laboratoire central",
        "chantier_id": chantier.id,
    }
    corps.update(extra)
    return corps


class TestVerserUneMesure:
    """Le cas central du BF-08 : le specialiste verse un resultat."""

    def test_specialiste_verse_une_mesure(
            self, client, spec_env_headers, chantier):
        reponse = client.post("/mesures", headers=spec_env_headers,
                              json=_mesure(chantier))
        assert reponse.status_code == 200, reponse.text
        mesure = reponse.json()
        assert mesure["parametre"] == "BRUIT"
        assert mesure["valeur"] == 72.5
        assert mesure["laboratoire"] == "CIAPOL, laboratoire central"
        assert mesure["chantier_id"] == chantier.id

    def test_l_unite_decoule_du_parametre(
            self, client, spec_env_headers, chantier):
        """L'unite n'est pas demandee a la saisie.

        La laisser libre permettrait de verser des decibels bruts a cote
        de dB(A), que le rapport additionnerait sans le savoir.
        """
        for parametre, unite in (("BRUIT", "dB(A)"),
                                 ("PM25", "µg/m³"),
                                 ("PM10", "µg/m³"),
                                 ("TURBIDITE", "NTU")):
            reponse = client.post(
                "/mesures", headers=spec_env_headers,
                json=_mesure(chantier, parametre=parametre, valeur=1.0))
            assert reponse.status_code == 200, reponse.text
            assert reponse.json()["unite"] == unite

    def test_l_administrateur_peut_saisir(
            self, client, auth_headers, chantier):
        """Le BF-08 associe l'administrateur au specialiste."""
        reponse = client.post("/mesures", headers=auth_headers,
                              json=_mesure(chantier))
        assert reponse.status_code == 200

    def test_les_observations_sont_conservees(
            self, client, spec_env_headers, chantier):
        reponse = client.post(
            "/mesures", headers=spec_env_headers,
            json=_mesure(chantier,
                         observations="Mesure prise à 15 m de la base vie, "
                                      "engins en fonctionnement."))
        assert "base vie" in reponse.json()["observations"]


class TestQuiPeutSaisir:
    """La saisie revient au profil qui rend compte au bailleur."""

    def test_agent_ne_saisit_pas(self, client, agent_headers, chantier):
        """Le Responsable Environnement appartient a l'entreprise.

        Lui laisser verser les mesures qui la controlent viderait le
        dispositif de son sens.
        """
        reponse = client.post("/mesures", headers=agent_headers,
                              json=_mesure(chantier))
        assert reponse.status_code == 403

    def test_expert_hse_ne_saisit_pas(
            self, client, expert_headers, chantier):
        """Le BF-08 ne nomme que le Specialiste Environnement."""
        reponse = client.post("/mesures", headers=expert_headers,
                              json=_mesure(chantier))
        assert reponse.status_code == 403

    def test_ande_ne_saisit_pas(self, client, ande_headers, chantier):
        """Le regulateur controle la mesure, il ne la produit pas."""
        reponse = client.post("/mesures", headers=ande_headers,
                              json=_mesure(chantier))
        assert reponse.status_code == 403

    def test_bad_ne_saisit_pas(self, client, bad_headers, chantier):
        reponse = client.post("/mesures", headers=bad_headers,
                              json=_mesure(chantier))
        assert reponse.status_code == 403


class TestSaisiesRefusees:
    """Ce qu'une mesure ne peut pas etre."""

    def test_parametre_inconnu(self, client, spec_env_headers, chantier):
        reponse = client.post(
            "/mesures", headers=spec_env_headers,
            json=_mesure(chantier, parametre="RADIOACTIVITE"))
        assert reponse.status_code == 422
        assert "Paramètre inconnu" in reponse.json()["detail"]

    def test_valeur_negative(self, client, spec_env_headers, chantier):
        """Aucune des grandeurs suivies ne prend de valeur negative."""
        reponse = client.post("/mesures", headers=spec_env_headers,
                              json=_mesure(chantier, valeur=-3.0))
        assert reponse.status_code == 422

    def test_date_dans_le_futur(self, client, spec_env_headers, chantier):
        """Une mesure datee du futur n'a pas pu etre prelevee."""
        reponse = client.post(
            "/mesures", headers=spec_env_headers,
            json=_mesure(chantier, jours=-5))
        assert reponse.status_code == 422
        assert "postérieure" in reponse.json()["detail"]

    def test_laboratoire_absent(self, client, spec_env_headers, chantier):
        """Une mesure sans auteur ne vaut rien devant un bailleur."""
        reponse = client.post("/mesures", headers=spec_env_headers,
                              json=_mesure(chantier, laboratoire=""))
        assert reponse.status_code == 422

    def test_chantier_inexistant(self, client, spec_env_headers, chantier):
        corps = _mesure(chantier)
        corps["chantier_id"] = 999999
        reponse = client.post("/mesures", headers=spec_env_headers,
                              json=corps)
        assert reponse.status_code == 404


class TestVerdictDeConformite:
    """Le rapprochement avec la valeur limite reglementaire.

    Ces seuils ne sont pas de meme nature que ceux des indices
    satellitaires, calibres empiriquement : ils viennent de l'arrete
    MINEEF et des lignes directrices de l'OMS, et un depassement
    s'oppose a l'entreprise.
    """

    def test_bruit_au_dela_du_seuil_mineef(
            self, client, spec_env_headers, chantier):
        reponse = client.post("/mesures", headers=spec_env_headers,
                              json=_mesure(chantier, valeur=78.0))
        mesure = reponse.json()
        assert mesure["etat"] == "DEPASSEMENT"
        assert mesure["limite"] == 70.0
        assert "MINEEF" in mesure["source_limite"]

    def test_bruit_conforme(self, client, spec_env_headers, chantier):
        reponse = client.post("/mesures", headers=spec_env_headers,
                              json=_mesure(chantier, valeur=55.0))
        assert reponse.json()["etat"] == "CONFORME"

    def test_bruit_en_vigilance(self, client, spec_env_headers, chantier):
        """Entre vigilance et limite : pas encore un depassement."""
        reponse = client.post("/mesures", headers=spec_env_headers,
                              json=_mesure(chantier, valeur=65.0))
        assert reponse.json()["etat"] == "VIGILANCE"

    def test_pm25_au_dela_de_la_valeur_oms(
            self, client, spec_env_headers, chantier):
        reponse = client.post(
            "/mesures", headers=spec_env_headers,
            json=_mesure(chantier, parametre="PM25", valeur=22.0))
        mesure = reponse.json()
        assert mesure["etat"] == "DEPASSEMENT"
        assert mesure["limite"] == 15.0
        assert "OMS" in mesure["source_limite"]

    def test_pm10_conforme(self, client, spec_env_headers, chantier):
        reponse = client.post(
            "/mesures", headers=spec_env_headers,
            json=_mesure(chantier, parametre="PM10", valeur=20.0))
        assert reponse.json()["etat"] == "CONFORME"


class TestLireLesMesures:
    """La lecture est ouverte a ceux qui controlent."""

    def test_ande_lit_les_mesures(
            self, client, ande_headers, spec_env_headers, chantier):
        """Ces mesures sont precisement ce que le regulateur controle."""
        client.post("/mesures", headers=spec_env_headers,
                    json=_mesure(chantier))
        reponse = client.get("/mesures", headers=ande_headers)
        assert reponse.status_code == 200
        assert len(reponse.json()) == 1

    def test_bad_lit_les_mesures(
            self, client, bad_headers, spec_env_headers, chantier):
        client.post("/mesures", headers=spec_env_headers,
                    json=_mesure(chantier))
        assert client.get("/mesures", headers=bad_headers).status_code == 200

    def test_filtre_par_parametre(
            self, client, spec_env_headers, chantier):
        client.post("/mesures", headers=spec_env_headers,
                    json=_mesure(chantier, parametre="BRUIT"))
        client.post("/mesures", headers=spec_env_headers,
                    json=_mesure(chantier, parametre="PM10", valeur=30.0))
        liste = client.get("/mesures?parametre=PM10",
                           headers=spec_env_headers).json()
        assert len(liste) == 1
        assert liste[0]["parametre"] == "PM10"

    def test_filtre_par_parametre_inconnu(
            self, client, spec_env_headers):
        reponse = client.get("/mesures?parametre=INCONNU",
                             headers=spec_env_headers)
        assert reponse.status_code == 422

    def test_la_plus_recente_en_tete(
            self, client, spec_env_headers, chantier):
        """Le tri suit la date de prelevement, non celle de saisie.

        Un rapport de laboratoire peut arriver des semaines apres le
        terrain, et c'est le moment du prelevement qui situe la mesure.
        """
        client.post("/mesures", headers=spec_env_headers,
                    json=_mesure(chantier, valeur=50.0, jours=30))
        client.post("/mesures", headers=spec_env_headers,
                    json=_mesure(chantier, valeur=60.0, jours=2))
        liste = client.get("/mesures", headers=spec_env_headers).json()
        assert liste[0]["valeur"] == 60.0

    def test_le_nom_du_chantier_accompagne_la_mesure(
            self, client, spec_env_headers, chantier):
        client.post("/mesures", headers=spec_env_headers,
                    json=_mesure(chantier))
        liste = client.get("/mesures", headers=spec_env_headers).json()
        assert liste[0]["chantier_nom"] == chantier.nom


class TestReferentiel:
    """Les grandeurs mesurables, exposees a l'ecran de saisie."""

    def test_les_quatre_parametres_sont_publies(
            self, client, spec_env_headers):
        reponse = client.get("/mesures/parametres",
                             headers=spec_env_headers)
        assert reponse.status_code == 200
        codes = {p["code"] for p in reponse.json()}
        assert codes == {"BRUIT", "PM25", "PM10", "TURBIDITE"}

    def test_chaque_limite_porte_sa_source(
            self, client, spec_env_headers):
        """Un rapport doit pouvoir dire d'ou vient le nombre.

        C'est ce qui distingue ces seuils de ceux des indices
        satellitaires, que le memoire qualifie de seuils de vigilance et
        non de conformite.
        """
        for parametre in client.get("/mesures/parametres",
                                    headers=spec_env_headers).json():
            assert parametre["source"], parametre["code"]
            assert parametre["limite"] > 0


class TestCorrigerUneMesure:
    """Une mesure fausse doit pouvoir etre retiree."""

    def test_specialiste_retire_une_mesure(
            self, client, spec_env_headers, chantier):
        mesure = client.post("/mesures", headers=spec_env_headers,
                             json=_mesure(chantier)).json()
        reponse = client.delete(f"/mesures/{mesure['id']}",
                                headers=spec_env_headers)
        assert reponse.status_code == 200
        assert client.get("/mesures",
                          headers=spec_env_headers).json() == []

    def test_agent_ne_retire_pas(
            self, client, agent_headers, spec_env_headers, chantier):
        mesure = client.post("/mesures", headers=spec_env_headers,
                             json=_mesure(chantier)).json()
        reponse = client.delete(f"/mesures/{mesure['id']}",
                                headers=agent_headers)
        assert reponse.status_code == 403

    def test_mesure_inexistante(self, client, spec_env_headers):
        assert client.delete("/mesures/999999",
                             headers=spec_env_headers).status_code == 404
