"""Le journal de l'administrateur porte les actions des personnes.

Il renvoyait tout, y compris les depassements de seuil declenches par le
systeme. Or l'administrateur y cherche ce que les gens font : qui s'est
connecte, qui a echoue, quel compte a change. Un NO2 au-dessus du seuil
releve du Specialiste et noyait ces lignes-la.
"""

from app import models
from app.services import journal_service


def _poser(db, message, categorie, utilisateur="qui@ageroute.ci"):
    db.add(models.Journal(niveau="INFO", message=message,
                          utilisateur=utilisateur, categorie=categorie))
    db.commit()


class TestCeQueLAdminVoit:
    def test_les_acces_et_les_comptes_remontent(
            self, client, db_session, auth_headers):
        _poser(db_session, "Connexion de X", journal_service.CAT_ACCES)
        _poser(db_session, "Compte créé : Y", journal_service.CAT_COMPTE)

        r = client.get("/admin/logs", headers=auth_headers)
        assert r.status_code == 200
        messages = [e["message"] for e in r.json()]
        assert "Connexion de X" in messages
        assert "Compte créé : Y" in messages

    def test_le_metier_ne_remonte_pas(self, client, db_session, auth_headers):
        """Un depassement de seuil n'est pas une action d'utilisateur."""
        _poser(db_session, "Alerte NO2 dépassé sur Y4",
               journal_service.CAT_METIER, utilisateur="système")

        messages = [e["message"]
                    for e in client.get("/admin/logs",
                                        headers=auth_headers).json()]
        assert "Alerte NO2 dépassé sur Y4" not in messages

    def test_le_parametrage_remonte(self, client, db_session, auth_headers):
        _poser(db_session, "Déploiement du modèle IA",
               journal_service.CAT_SYSTEME)
        messages = [e["message"]
                    for e in client.get("/admin/logs",
                                        headers=auth_headers).json()]
        assert "Déploiement du modèle IA" in messages

    def test_tout_rend_la_vue_complete(self, client, db_session, auth_headers):
        """Rien n'est cache : la vue complete reste accessible."""
        _poser(db_session, "Alerte NDVI bas", journal_service.CAT_METIER)
        messages = [e["message"]
                    for e in client.get("/admin/logs?tout=true",
                                        headers=auth_headers).json()]
        assert "Alerte NDVI bas" in messages

    def test_une_categorie_s_isole(self, client, db_session, auth_headers):
        _poser(db_session, "Connexion de Z", journal_service.CAT_ACCES)
        _poser(db_session, "Compte supprimé : W", journal_service.CAT_COMPTE)

        r = client.get(f"/admin/logs?categorie={journal_service.CAT_ACCES}",
                       headers=auth_headers)
        messages = [e["message"] for e in r.json()]
        assert "Connexion de Z" in messages
        assert "Compte supprimé : W" not in messages


class TestLaConnexionLaisseUneTrace:
    def test_une_connexion_reussie_est_tracee(
            self, client, resp_env_user, auth_headers):
        client.post("/auth/login",
                    data={"username": "agent@test.com", "password": "agent123"})
        entrees = client.get("/admin/logs", headers=auth_headers).json()
        assert any("Connexion" in e["message"]
                   and e["utilisateur"] == "agent@test.com" for e in entrees)

    def test_un_mot_de_passe_errone_est_trace(
            self, client, resp_env_user, auth_headers):
        """C'est le signal qu'un administrateur vient chercher."""
        client.post("/auth/login",
                    data={"username": "agent@test.com", "password": "faux"})
        entrees = client.get("/admin/logs", headers=auth_headers).json()
        assert any("Mot de passe incorrect" in e["message"] for e in entrees)

    def test_un_compte_inconnu_est_trace(self, client, auth_headers):
        client.post("/auth/login",
                    data={"username": "intrus@ailleurs.ci", "password": "x"})
        entrees = client.get("/admin/logs", headers=auth_headers).json()
        assert any("compte inconnu" in e["message"] for e in entrees)


class TestLesGardesDuCrud:
    def test_l_admin_ne_se_retire_pas_son_propre_role(
            self, client, admin_user, auth_headers):
        r = client.patch(f"/admin/users/{admin_user.id}",
                         json={"role": "RESP_ENV"}, headers=auth_headers)
        assert r.status_code == 400
        assert "administrateur" in r.json()["detail"].lower()

    def test_le_dernier_admin_ne_se_supprime_pas(
            self, client, admin_user, resp_env_user, db_session, auth_headers):
        """Deux admins pouvaient se supprimer l'un l'autre.

        Le systeme se retrouvait alors sans aucune administration, et la
        situation ne se reparait plus que dans la base.
        """
        autre = models.Utilisateur(
            nom="Second admin", email="admin2@test.com",
            mot_de_passe_hash="x", role=models.RoleEnum.ADMIN,
            premiere_connexion=False)
        db_session.add(autre)
        db_session.commit()
        db_session.refresh(autre)

        # Deux admins : la suppression du second passe.
        assert client.delete(f"/admin/users/{autre.id}",
                             headers=auth_headers).status_code == 200

        # Il n'en reste qu'un, et c'est celui qui agit : refus des deux
        # cotes, par la garde du compte propre comme par celle du dernier.
        r = client.delete(f"/admin/users/{admin_user.id}",
                          headers=auth_headers)
        assert r.status_code == 400

    def test_le_telephone_devient_modifiable(
            self, client, resp_env_user, auth_headers):
        r = client.patch(f"/admin/users/{resp_env_user.id}",
                         json={"telephone": "+2250700000000"},
                         headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["telephone"] == "+2250700000000"

    def test_le_changement_de_role_dit_d_ou_l_on_vient(
            self, client, resp_env_user, auth_headers):
        client.patch(f"/admin/users/{resp_env_user.id}",
                     json={"role": "EXPERT_HSE"}, headers=auth_headers)
        entrees = client.get("/admin/logs", headers=auth_headers).json()
        assert any("RESP_ENV vers EXPERT_HSE" in e["message"]
                   for e in entrees)


class TestLesRefusLaissentUneTrace:
    """Le memoire annonce que les acces refuses sont consignes.

    Ils ne l'etaient pas : le refus part d'une dependance FastAPI, qui
    leve une exception sans rien ecrire. Un administrateur ne pouvait
    donc pas voir qu'un profil tentait ce que son role ne permet pas.
    """

    def test_un_role_qui_depasse_son_perimetre_est_consigne(
            self, client, resp_env_token, auth_headers):
        # Un agent de terrain n'administre pas les comptes.
        r = client.get("/admin/users",
                       headers={"Authorization": f"Bearer {resp_env_token}"})
        assert r.status_code == 403

        entrees = client.get("/admin/logs", headers=auth_headers).json()
        assert any("Accès refusé" in e["message"]
                   and "/admin/users" in e["message"] for e in entrees)

    def test_une_requete_sans_jeton_est_consignee(self, client, auth_headers):
        r = client.get("/admin/users")
        assert r.status_code in (401, 403)
        entrees = client.get("/admin/logs", headers=auth_headers).json()
        assert any("Accès refusé" in e["message"] for e in entrees)

    def test_le_refus_est_range_dans_les_acces(self, client, resp_env_token,
                                               auth_headers):
        client.get("/admin/users",
                   headers={"Authorization": f"Bearer {resp_env_token}"})
        entrees = client.get(f"/admin/logs?categorie={journal_service.CAT_ACCES}",
                             headers=auth_headers).json()
        assert any("Accès refusé" in e["message"] for e in entrees)


class TestLeDecompteDesFiltres:
    """Un filtre doit dire ce qu'il contient.

    L'ecran en proposait cinq sans le dire : deux renvoyaient les memes
    lignes, deux n'en renvoyaient aucune. Le decompte permet de n'en
    afficher que ce qui existe.
    """

    def test_chaque_nature_est_comptee(self, client, db_session, auth_headers):
        _poser(db_session, "Connexion A", journal_service.CAT_ACCES)
        _poser(db_session, "Connexion B", journal_service.CAT_ACCES)
        _poser(db_session, "Compte créé", journal_service.CAT_COMPTE)

        d = client.get("/admin/logs/decompte", headers=auth_headers).json()
        assert d[journal_service.CAT_ACCES] == 2
        assert d[journal_service.CAT_COMPTE] == 1

    def test_une_nature_absente_vaut_zero_ou_manque(
            self, client, db_session, auth_headers):
        """L'ecran ne doit pas proposer un filtre vide."""
        _poser(db_session, "Connexion seule", journal_service.CAT_ACCES)
        d = client.get("/admin/logs/decompte", headers=auth_headers).json()
        assert d.get(journal_service.CAT_SYSTEME, 0) == 0

    def test_le_total_couvre_tout(self, client, db_session, auth_headers):
        _poser(db_session, "Accès", journal_service.CAT_ACCES)
        _poser(db_session, "Alerte seuil", journal_service.CAT_METIER)
        d = client.get("/admin/logs/decompte", headers=auth_headers).json()
        assert d["TOTAL"] == sum(v for k, v in d.items() if k != "TOTAL")

    def test_une_entree_sans_nature_compte_comme_metier(
            self, client, db_session, auth_headers):
        """Les entrees anterieures a la distinction en relevaient toutes."""
        db_session.add(models.Journal(niveau="INFO", message="Ancienne",
                                      utilisateur="x", categorie=None))
        db_session.commit()
        d = client.get("/admin/logs/decompte", headers=auth_headers).json()
        assert d[journal_service.CAT_METIER] >= 1
