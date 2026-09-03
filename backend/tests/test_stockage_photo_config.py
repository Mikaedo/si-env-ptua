# -*- coding: utf-8 -*-
"""
Verifie que le stockage Supabase tolere une configuration mal recopiee.

Ce test est ne d'une panne reelle, et c'est ce qui le justifie : en
production, l'envoi d'une photographie echouait avec une erreur 500
tandis que les quatre tests du circuit passaient en local. La table
des erreurs de l'application donnait la cause exacte :

    InvalidURL : Invalid non-printable ASCII character in URL

La variable SUPABASE_URL, saisie dans le tableau de bord de
l'hebergeur, emportait un retour a la ligne final. Le copier-coller
l'avait ajoute sans qu'il se voie, et le `.rstrip("/")` du code ne
retirait que les barres obliques.

Une panne invisible en local et fatale en production merite un test
qui la retienne. Les cas couverts sont ceux que produit un
copier-coller : retour a la ligne, retour chariot, espaces, barre
oblique finale.
"""
import importlib
import os
import sys

import pytest


# Les formes qu'une variable mal recopiee peut prendre, et ce qui doit
# en sortir apres nettoyage.
FORMES = [
    ("https://projet.supabase.co", "propre"),
    ("https://projet.supabase.co\n", "retour a la ligne final"),
    ("https://projet.supabase.co\r\n", "retour chariot et ligne"),
    ("  https://projet.supabase.co  ", "espaces autour"),
    ("https://projet.supabase.co/", "barre oblique finale"),
    ("https://projet.supabase.co/\n", "barre oblique et retour"),
]

ATTENDU = "https://projet.supabase.co"


class _ClientFactice:
    """Un client Supabase de facade, qui retient ce qu'on lui passe.

    Le test ne doit pas joindre Supabase : ce qu'il verifie, c'est la
    valeur transmise au constructeur du client, non le comportement du
    service distant.
    """

    recus = {}

    def __init__(self, url, cle):
        _ClientFactice.recus = {"url": url, "cle": cle}


@pytest.fixture
def stockage(monkeypatch):
    """Charge le module de stockage avec un client Supabase factice."""
    module_factice = type(sys)("supabase")
    module_factice.create_client = _ClientFactice
    monkeypatch.setitem(sys.modules, "supabase", module_factice)

    from app.services import photo_storage
    importlib.reload(photo_storage)
    return photo_storage


@pytest.mark.parametrize("valeur,libelle", FORMES)
def test_url_nettoyee_avant_usage(stockage, monkeypatch, valeur, libelle):
    """L'URL transmise au client ne porte aucun caractere parasite.

    C'est le coeur de la correction : quelle que soit la forme saisie
    dans le tableau de bord de l'hebergeur, le client recoit une URL
    propre, et httpx ne refuse plus la requete.
    """
    monkeypatch.setenv("SUPABASE_URL", valeur)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "eyJcle.de.service")
    monkeypatch.setenv("SUPABASE_BUCKET", "photos")

    backend = stockage._StockageSupabase()

    assert _ClientFactice.recus["url"] == ATTENDU, (
        f"forme « {libelle} » : le client a recu "
        f"{_ClientFactice.recus['url']!r}")
    # Aucun caractere non imprimable ne subsiste : c'est precisement
    # ce que httpx refusait.
    for caractere in _ClientFactice.recus["url"]:
        assert 32 <= ord(caractere) < 127, (
            f"forme « {libelle} » : caractere {caractere!r} dans l'URL")


def test_cle_de_service_nettoyee(stockage, monkeypatch):
    """La cle non plus ne doit pas porter de retour a la ligne.

    Elle voyage en en-tete HTTP. httpx la tolere aujourd'hui, mais une
    en-tete portant un retour a la ligne est un vecteur d'injection
    connu : autant la nettoyer.
    """
    monkeypatch.setenv("SUPABASE_URL", "https://projet.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "  eyJcle.abc\n")
    monkeypatch.setenv("SUPABASE_BUCKET", "photos")

    stockage._StockageSupabase()

    assert _ClientFactice.recus["cle"] == "eyJcle.abc"


def test_nom_du_bucket_nettoye(stockage, monkeypatch):
    """Le nom du bucket entre dans l'URL publique : meme exigence."""
    monkeypatch.setenv("SUPABASE_URL", "https://projet.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "eyJcle.abc")
    monkeypatch.setenv("SUPABASE_BUCKET", "photos\n")

    backend = stockage._StockageSupabase()

    assert backend.bucket == "photos"
    assert backend._url_publique_base == (
        "https://projet.supabase.co/storage/v1/object/public/photos")


def test_url_publique_est_joignable_par_httpx(stockage, monkeypatch):
    """L'URL construite passe la validation d'httpx.

    Le test refait la verification qui echouait en production : httpx
    acceptait-il de construire une requete vers cette URL ? C'est ce
    refus, et lui seul, qui produisait l'erreur 500.
    """
    httpx = pytest.importorskip("httpx")

    monkeypatch.setenv("SUPABASE_URL", "https://projet.supabase.co\n")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "eyJcle.abc")
    monkeypatch.setenv("SUPABASE_BUCKET", "photos")

    backend = stockage._StockageSupabase()
    cible = backend.url_publique("sig_1_20260903_photo.jpg")

    # Sans le nettoyage, cette ligne levait InvalidURL.
    httpx.Request("GET", cible)


def test_stockage_local_par_defaut(stockage, monkeypatch):
    """Sans PHOTO_STORAGE, le disque local reste le choix par defaut.

    La correction ne doit pas changer le comportement en
    developpement : un poste sans variable Supabase continue d'ecrire
    sur son disque.
    """
    monkeypatch.delenv("PHOTO_STORAGE", raising=False)
    assert isinstance(stockage._instancier(), stockage._StockageLocal)
