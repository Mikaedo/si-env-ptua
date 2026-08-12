# -*- coding: utf-8 -*-
"""
photo_storage.py
----------------
Stockage des photos de signalements. Deux backends interchangeables :

  - `local`    : ecriture sur disque, servie par StaticFiles (defaut en dev).
  - `supabase` : upload dans un bucket Supabase Storage (defaut en prod).

Le choix se fait par la variable d'environnement PHOTO_STORAGE. Les autres
variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_BUCKET) ne sont
lues que si le backend Supabase est actif ; leur absence en local est donc
sans effet.

Contrat commun : `enregistrer(nom_fichier, donnees)` retourne la valeur qui
sera persistee dans `photos.chemin`. Cote client (mobile, dashboard),
signalement_detail.ts construit l'URL avec `${apiUrl}/uploads/photos/{chemin}`.
Pour que ce contrat continue de tenir sans changer les clients, le backend
Supabase publie ses fichiers via une URL publique et enregistre l'URL absolue
telle quelle. Le mobile et le dashboard detectent une URL absolue et l'utilisent
directement au lieu de la prefixer.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Protocol

logger = logging.getLogger("photo_storage")

PHOTO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "photos"
)


class BackendStockage(Protocol):
    def enregistrer(self, nom_fichier: str, donnees: bytes) -> str: ...
    def url_publique(self, chemin: str) -> str: ...


class _StockageLocal:
    """Ecriture sur le disque du conteneur, sous /app/uploads/photos.

    Le dossier est monte en volume nomme par docker-compose : sans ce volume,
    les photos disparaissaient a chaque reconstruction d'image.
    """

    def __init__(self, dossier: str = PHOTO_DIR):
        self.dossier = dossier
        os.makedirs(self.dossier, exist_ok=True)

    def enregistrer(self, nom_fichier: str, donnees: bytes) -> str:
        chemin_absolu = os.path.join(self.dossier, nom_fichier)
        with open(chemin_absolu, "wb") as f:
            f.write(donnees)
        # Chemin relatif : les clients le prefixent par ${apiUrl}/uploads/photos/.
        return nom_fichier

    def url_publique(self, chemin: str) -> str:
        return f"/uploads/photos/{chemin}"


class _StockageSupabase:
    """Depose l'objet dans un bucket Supabase Storage public.

    Choix du bucket public plutot que d'URL signees : les URL signees expirent,
    or les rapports PGES et les captures de detail doivent rester consultables
    indefiniment. Le bucket public reste protege par les regles Row Level
    Security cote base ; seuls les octets bruts sont accessibles a qui possede
    l'URL, ce qui est le contrat attendu pour une photo de terrain.

    Requiert les variables : SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_BUCKET (defaut : « photos »).
    """

    def __init__(self):
        # Import differe : la librairie n'est necessaire qu'en prod.
        try:
            from supabase import create_client  # type: ignore
        except ImportError as e:  # pragma: no cover - dependance conditionnelle
            raise RuntimeError(
                "PHOTO_STORAGE=supabase mais la librairie 'supabase' n'est pas installee. "
                "Ajouter 'supabase' a requirements.txt."
            ) from e

        url = os.environ["SUPABASE_URL"]
        cle = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        self.bucket = os.getenv("SUPABASE_BUCKET", "photos")
        self._client = create_client(url, cle)
        self._url_publique_base = f"{url.rstrip('/')}/storage/v1/object/public/{self.bucket}"

    def enregistrer(self, nom_fichier: str, donnees: bytes) -> str:
        # Le client Supabase leve si l'objet existe deja. On retente en
        # upsertant, car pytest peut rejouer le meme nom pendant un test.
        self._client.storage.from_(self.bucket).upload(
            nom_fichier, donnees, {"content-type": "image/jpeg", "upsert": "true"}
        )
        # On enregistre l'URL publique absolue, pour que les clients puissent
        # la reutiliser sans connaitre l'URL du projet Supabase.
        return f"{self._url_publique_base}/{nom_fichier}"

    def url_publique(self, chemin: str) -> str:
        if chemin.startswith("http://") or chemin.startswith("https://"):
            return chemin
        return f"{self._url_publique_base}/{chemin}"


def _instancier() -> BackendStockage:
    choix = os.getenv("PHOTO_STORAGE", "local").lower()
    if choix == "supabase":
        logger.info("Stockage photos : Supabase Storage")
        return _StockageSupabase()
    logger.info("Stockage photos : disque local (%s)", PHOTO_DIR)
    return _StockageLocal()


# Instance unique du backend. Le processus ne change pas de mode a chaud.
backend: BackendStockage = _instancier()


def nom_unique(signalement_id: int, nom_original: str) -> str:
    """Prefixe temporel et identifiant : evite les collisions et facilite le
    tri par ordre chronologique dans un explorateur d'objets."""
    horodatage = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"sig_{signalement_id}_{horodatage}_{nom_original}"
