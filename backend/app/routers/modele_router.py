# -*- coding: utf-8 -*-
"""
modele_router.py
-----------------
Cote mobile de la mise a jour des modeles embarques : contrairement a
`/admin/model`, ces routes sont ouvertes a tout utilisateur authentifie
(Responsable Environnement, Expert HSE compris), puisque ce sont eux qui
declenchent le telechargement depuis leur telephone.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from .. import auth, models
from ..services import modele_service

router = APIRouter(prefix="/model", tags=["Modèle IA"])


@router.get("/versions", response_model=dict)
def versions_modeles(_: models.Utilisateur = Depends(auth.utilisateur_courant)):
    return modele_service.toutes_les_infos()


@router.get("/download/{type_modele}")
def telecharger_modele(
    type_modele: str,
    _: models.Utilisateur = Depends(auth.utilisateur_courant),
):
    if type_modele not in modele_service.NOMS_FICHIERS:
        raise HTTPException(status_code=404, detail="Type de modèle inconnu")
    chemin = modele_service.chemin_modele(type_modele)
    if not chemin.exists():
        raise HTTPException(status_code=404, detail="Aucun modèle déployé pour ce type")
    return FileResponse(chemin, media_type="application/octet-stream", filename=chemin.name)
