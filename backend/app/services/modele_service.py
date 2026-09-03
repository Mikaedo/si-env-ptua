# -*- coding: utf-8 -*-
"""
modele_service.py
------------------
Stockage et suivi de version des deux modeles d'inference embarquee
(detection YOLOv8n, classification MobileNetV2) que l'administrateur peut
redeployer sans passer par le Play Store.

Le fichier deploye est ecrit sur le disque du conteneur, comme les photos en
mode local (`photo_storage.py`) : sur Render, ce disque ne survit pas a un
redeploiement declenche par un push sur main, seulement aux redemarrages du
meme conteneur. Suffisant pour la demonstration ; un passage en production
reprendrait le meme bucket Supabase que les photos.

La version exposee au mobile est l'horodatage de derniere ecriture du
fichier : un entier croissant, trivial a comparer cote client sans avoir a
gerer un numero de version explicite.
"""
from datetime import datetime
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parents[2] / "uploads" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

NOMS_FICHIERS = {
    "detection": "detection.onnx",
    "classification": "classification.onnx",
}


def chemin_modele(type_modele: str) -> Path:
    return MODEL_DIR / NOMS_FICHIERS[type_modele]


def info_modele(type_modele: str) -> dict:
    chemin = chemin_modele(type_modele)
    if not chemin.exists():
        return {"disponible": False, "version": 0, "taille_octets": 0, "deploye_le": None}
    mtime = chemin.stat().st_mtime
    return {
        "disponible": True,
        "version": int(mtime),
        "taille_octets": chemin.stat().st_size,
        "deploye_le": datetime.fromtimestamp(mtime).isoformat(),
    }


def toutes_les_infos() -> dict:
    return {t: info_modele(t) for t in NOMS_FICHIERS}
