# -*- coding: utf-8 -*-
"""
Verifie que le riverain reste dans son perimetre, et que les filtres
refusent proprement une valeur inconnue.

Ces deux tests naissent d'une campagne de verification menee sur le
serveur de production, a une semaine de la soutenance. Elle a releve
neuf ecarts sur quatre-vingt-treize appels, dont trois qui comptaient :

  - un riverain inscrit depuis son telephone pouvait lire
    /signalements et /stats. Aucune ecriture ne lui etait ouverte, mais
    la lecture suffisait : il voyait les constats des agents sur tous
    les chantiers du programme, et le bilan environnemental du PTUA.
    Le tableau 4.1 du memoire ne lui accorde rien de tel ;

  - un filtre portant une valeur hors de l'enumere faisait remonter un
    DataError de PostgreSQL, que le gestionnaire d'exceptions
    traduisait en 500. Une faute du client rendue comme une panne du
    serveur : le tableau de bord ne pouvait pas distinguer les deux.

Les tests ci-dessous retiennent ces deux corrections. Le premier
importe : un cloisonnement se verifie, il ne se suppose pas.
"""
import pytest

from app import auth, models


# ─── Les deux profils que ces tests mettent en jeu ───────────────────
# Ils ne figurent pas dans conftest.py, qui ne cree qu'administrateur,
# responsable et expert. Les declarer ici plutot que d'alourdir le
# conftest partage : ils ne servent qu'a ce fichier.
@pytest.fixture
def riverain(db_session):
    """Un riverain inscrit, tel que l'application citoyenne en cree."""
    utilisateur = models.Utilisateur(
        nom="Riverain de test",
        email="riverain@test.ci",
        mot_de_passe_hash=auth.hasher_mot_de_passe("riverain123"),
        role=models.RoleEnum.PLAIGNANT,
        premiere_connexion=False,
    )
    db_session.add(utilisateur)
    db_session.commit()
    db_session.refresh(utilisateur)
    return utilisateur


@pytest.fixture
def riverain_token(riverain):
    return auth.creer_token({"sub": str(riverain.id),
                             "role": riverain.role.value})


@pytest.fixture
def spec_env(db_session):
    """Le Specialiste Suivi Environnemental, qui filtre au quotidien."""
    utilisateur = models.Utilisateur(
        nom="Specialiste de test",
        email="spec.env@test.ci",
        mot_de_passe_hash=auth.hasher_mot_de_passe("spec123"),
        role=models.RoleEnum.SPEC_ENV,
        premiere_connexion=False,
    )
    db_session.add(utilisateur)
    db_session.commit()
    db_session.refresh(utilisateur)
    return utilisateur


@pytest.fixture
def spec_env_token(spec_env):
    return auth.creer_token({"sub": str(spec_env.id),
                             "role": spec_env.role.value})


# ─── Le riverain ─────────────────────────────────────────────────────
def test_riverain_ne_lit_pas_les_signalements(client, riverain_token):
    """Le riverain depose des doleances, il ne lit pas les constats.

    Ouvrir /signalements a un compte cree depuis un telephone
    reviendrait a publier les constats de terrain de tout le programme
    a quiconque s'inscrit.
    """
    reponse = client.get(
        "/signalements",
        headers={"Authorization": f"Bearer {riverain_token}"})
    assert reponse.status_code == 403, reponse.text
    assert "doléances" in reponse.json()["detail"]


def test_riverain_ne_lit_pas_les_statistiques(client, riverain_token):
    """Les statistiques agregent tout le programme : pas pour lui.

    Le taux de resolution et la repartition des nuisances forment le
    bilan environnemental du PTUA. Il se remet a l'ANDE et au
    bailleur, non a un riverain.
    """
    reponse = client.get(
        "/stats",
        headers={"Authorization": f"Bearer {riverain_token}"})
    assert reponse.status_code == 403, reponse.text


def test_riverain_lit_ses_propres_doleances(client, riverain_token):
    """Le cloisonnement ne doit pas l'enfermer.

    Un riverain qui ne pourrait plus rien consulter n'aurait aucune
    raison d'installer l'application : la contrepartie du depot est de
    pouvoir suivre ce qu'il a signale.
    """
    reponse = client.get(
        "/citoyen/doleances",
        headers={"Authorization": f"Bearer {riverain_token}"})
    assert reponse.status_code == 200, reponse.text


# ─── Les filtres ─────────────────────────────────────────────────────
@pytest.mark.parametrize("parametre,valeur", [
    ("criticite", "IMPORTANT"),      # la valeur retenue est ELEVE
    ("criticite", "n_importe_quoi"),
    ("statut", "TERMINE"),           # la valeur retenue est CLOTURE
    ("statut", "1 OR 1=1"),
])
def test_filtre_inconnu_repond_422(client, spec_env_token, parametre,
                                   valeur):
    """Une valeur hors enumere vaut 422, jamais 500.

    Le dernier cas est aussi une verification de sante : une valeur
    portant une tournure d'injection ne doit ni passer, ni faire
    tomber le serveur.
    """
    reponse = client.get(
        f"/signalements?{parametre}={valeur}",
        headers={"Authorization": f"Bearer {spec_env_token}"})
    assert reponse.status_code == 422, reponse.text
    detail = reponse.json()["detail"]
    # Le message nomme les valeurs admises : le client sait quoi
    # corriger sans consulter le code.
    assert "admises" in detail.lower() or "invalide" in detail.lower()


@pytest.mark.parametrize("parametre,valeur", [
    ("criticite", "ELEVE"),
    ("criticite", "FAIBLE"),
    ("criticite", "MODERE"),
    ("statut", "NOUVEAU"),
    ("statut", "CLOTURE"),
])
def test_filtre_valide_passe(client, spec_env_token, parametre,
                             valeur):
    """Les valeurs de l'enumere continuent de fonctionner.

    Une validation trop stricte qui refuserait une valeur legitime
    casserait les filtres du tableau de bord : ce test la retient.
    """
    reponse = client.get(
        f"/signalements?{parametre}={valeur}",
        headers={"Authorization": f"Bearer {spec_env_token}"})
    assert reponse.status_code == 200, reponse.text
    assert isinstance(reponse.json(), list)
