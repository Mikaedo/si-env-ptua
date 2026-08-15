"""
test_seed.py
------------
Verifie que le jeu de donnees initial couvre tout ce que le systeme sait
representer.

Ces tests repondent a un oubli concret : le profil riverain a ete ajoute au
modele sans que le seed ne suive, si bien que sept profils sur huit disposaient
d'un compte de demonstration et que le huitieme n'existait nulle part. Le
Mecanisme de Gestion des Plaintes se trouvait dans le meme cas, aucune doleance
n'etant creee, ce qui laissait l'ecran du specialiste du suivi social vide sur
une base neuve.

Le principe retenu ici est simple : le seed doit se deduire du modele, et non
etre tenu a jour de memoire. Le premier test parcourt donc l'enumeration des
roles plutot qu'une liste ecrite a la main, si bien qu'un neuvieme profil
ajoute demain ferait echouer la verification tant qu'il n'aurait pas de compte.
"""
import pytest

from app import models


@pytest.fixture
def base_semee(db_session, monkeypatch):
    """Execute le seed sur la base de test."""
    import seed as module_seed

    # Le seed ouvre sa propre session et cree les extensions PostGIS. Sous
    # SQLite, on lui substitue la session de test et on neutralise ce qui
    # suppose PostgreSQL.
    monkeypatch.setattr(module_seed, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)

    def _point(lon, lat):
        return f"SRID=4326;POINT({lon} {lat})"

    class _FauxFunc:
        @staticmethod
        def ST_SetSRID(point, srid):
            return point

        @staticmethod
        def ST_MakePoint(lon, lat):
            return _point(lon, lat)

    monkeypatch.setattr(module_seed, "func", _FauxFunc)
    monkeypatch.setattr(module_seed, "engine", None, raising=False)

    module_seed.executer_seed(creer_extensions=False)
    return db_session


class TestCouvertureDesProfils:
    """Chaque profil du modele doit exister dans le jeu de demonstration."""

    def test_tous_les_roles_ont_un_compte(self, base_semee):
        """Parcourt l'enumeration, pas une liste tenue a la main.

        Un profil ajoute au modele sans compte correspondant fera echouer ce
        test, ce qui est precisement ce qui a manque lors de l'ajout du profil
        riverain.
        """
        presents = {u.role for u in base_semee.query(models.Utilisateur).all()}
        manquants = sorted(r.value for r in models.RoleEnum if r not in presents)
        assert not manquants, f"Profils sans compte de demonstration : {manquants}"

    def test_le_riverain_est_rattache_a_un_chantier(self, base_semee):
        """Sans rattachement, ses doleances n'auraient nulle part ou aller."""
        riverain = base_semee.query(models.Utilisateur).filter_by(
            role=models.RoleEnum.PLAIGNANT
        ).first()
        assert riverain is not None
        assert riverain.chantier_rattachement_id is not None

    def test_les_organismes_de_controle_sont_representes(self, base_semee):
        adresses = {u.email for u in base_semee.query(models.Utilisateur).all()}
        assert "controle@ande.ci" in adresses
        assert "mission@afdb.org" in adresses


class TestJeuDeDoleances:
    """Le Mecanisme de Gestion des Plaintes doit avoir de quoi se montrer."""

    def test_des_doleances_existent(self, base_semee):
        assert base_semee.query(models.Plainte).count() > 0

    def test_les_deux_canaux_de_saisie_sont_representes(self, base_semee):
        """L'application citoyenne s'ajoute au guichet, elle ne le remplace pas.

        Le rapport remis au bailleur mesure l'apport du canal mobile : encore
        faut-il que les deux coexistent dans le jeu de demonstration.
        """
        canaux = {p.canal for p in base_semee.query(models.Plainte).all()}
        assert "MOBILE" in canaux
        assert "GUICHET" in canaux

    def test_les_etats_de_traitement_sont_varies(self, base_semee):
        """Une file ou tout porte le meme statut ne montre aucun traitement."""
        statuts = {p.statut for p in base_semee.query(models.Plainte).all()}
        assert len(statuts) >= 2

    def test_les_doleances_mobiles_ont_un_auteur(self, base_semee):
        """Un depot par telephone suppose un compte ; le guichet non."""
        for plainte in base_semee.query(models.Plainte).filter_by(canal="MOBILE").all():
            assert plainte.plaignant_id is not None

    def test_les_doleances_sont_rattachees_a_un_chantier(self, base_semee):
        for plainte in base_semee.query(models.Plainte).all():
            assert plainte.chantier_id is not None


class TestIdempotence:
    """Le seed est rejoue a chaque demarrage lorsqu'il est active."""

    def test_une_seconde_execution_ne_duplique_rien(self, base_semee, monkeypatch):
        import seed as module_seed

        avant_utilisateurs = base_semee.query(models.Utilisateur).count()
        avant_doleances = base_semee.query(models.Plainte).count()

        module_seed.executer_seed(creer_extensions=False)

        assert base_semee.query(models.Utilisateur).count() == avant_utilisateurs
        assert base_semee.query(models.Plainte).count() == avant_doleances
