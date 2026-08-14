"""
satellite_router.py
-------------------
Module d'analyse satellitaire — SI-ENV / PTUA / AGEROUTE
Intégration réelle Google Earth Engine.

Endpoints :
- GET /satellite/indices         : tous les indices (NO2, NDVI, NDWI, RISQUE_PLUIE)
- GET /satellite/indices/{type}  : indices filtrés par type
- GET /satellite/serie/{type}    : série temporelle mensuelle (avec paramètre chantier_id)
- GET /satellite/resume          : résumé synthétique pour le dashboard
- GET /satellite/chantiers       : liste des chantiers avec coordonnées

Sources :
  - Sentinel-5P / TROPOMI  : NO2 (qualité air)
  - Sentinel-2 MSI         : NDVI (végétation), NDWI (humidité)
  - CHIRPS + SRTM          : Risque pluie/érosion
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from .. import models, auth
from ..gee_service import (
    CHANTIERS, get_no2, get_ndvi, get_ndwi, get_risque_pluie,
    get_cloud_cover_pct,
)
from ..gee_service import get_serie_temporelle as _fetch_serie_temporelle

logger = logging.getLogger("satellite_router")
router = APIRouter(prefix="/satellite", tags=["Satellite"])


# ─────────────────────────────────────────────
# Schémas de réponse
# ─────────────────────────────────────────────

class IndicePoint(BaseModel):
    id: int
    type_indice: str
    valeur: float
    unite: str
    date_calcule: str
    chantier: Optional[dict] = None
    statut: str
    tendance: str
    source: str


class PointSerie(BaseModel):
    mois: str
    valeur: float
    phase: str


class SerieTemporelle(BaseModel):
    type_indice: str
    unite: str
    description: str
    chantier: str
    points: List[PointSerie]


class ResumeSatellite(BaseModel):
    no2_moyen: float
    ndwi_moyen: float
    ndvi_moyen: float
    risque_pluie_max: float
    nb_alertes_qualite: int
    derniere_mise_a_jour: str
    couverture_nuageuse_pct: float


class ChantierInfo(BaseModel):
    id: int
    nom: str
    commune: str
    lon: float
    lat: float


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

UNITES = {
    "NO2": "µmol/m²",
    "NDWI": "[-1 à +1]",
    "NDVI": "[-1 à +1]",
    "RISQUE_PLUIE": "/10",
}

SOURCES = {
    "NO2": "Sentinel-5P / TROPOMI — COPERNICUS",
    "NDWI": "Sentinel-2 MSI — Google Earth Engine",
    "NDVI": "Sentinel-2 MSI — Google Earth Engine",
    "RISQUE_PLUIE": "CHIRPS + SRTM — Google Earth Engine",
}

DESCRIPTIONS = {
    "NO2": "Dioxyde d'azote (NO₂) — Sentinel-5P/TROPOMI. Indicateur principal de pollution atmosphérique liée aux engins de chantier (groupes électrogènes, camions, concasseurs). Seuil : <30 µmol/m² BON, 30-50 MODÉRÉ, >50 MAUVAIS.",
    "NDVI": "Indice de Végétation par Différence Normalisée — Sentinel-2. Mesure la densité et santé du couvert végétal. >0,4 = végétation dense.",
    "NDWI": "Indice d'Eau par Différence Normalisée — Sentinel-2. Évalue l'humidité du sol. >0,3 = végétation bien hydratée.",
    "RISQUE_PLUIE": "Indice composite CHIRPS (précipitations) + SRTM (pente). Évalue le risque d'érosion. Seuil critique : >7/10.",
}


def _statut_no2(v: float) -> str:
    """Seuils NO₂ troposphérique (µmol/m²) — GEE Sentinel-5P/TROPOMI"""
    if v < 30: return "BON"
    if v < 50: return "MODÉRÉ"
    return "MAUVAIS"


def _statut_ndwi(v: float) -> str:
    if v > 0.3: return "BON"
    if v >= 0: return "MODÉRÉ"
    return "MAUVAIS"


def _statut_ndvi(v: float) -> str:
    if v > 0.4: return "BON"
    if v > 0.2: return "MODÉRÉ"
    return "MAUVAIS"


def _statut_risque(v: float) -> str:
    if v < 4: return "BON"
    if v < 7: return "MODÉRÉ"
    return "MAUVAIS"


def _build_statut(type_ind: str, valeur: float) -> str:
    if type_ind == "NO2": return _statut_no2(valeur)
    if type_ind == "NDWI": return _statut_ndwi(valeur)
    if type_ind == "NDVI": return _statut_ndvi(valeur)
    if type_ind == "RISQUE_PLUIE": return _statut_risque(valeur)
    return "INCONNU"


def _tendance_label(t: str) -> str:
    return t if t in ("HAUSSE", "BAISSE", "STABLE") else "STABLE"


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.get("/chantiers", response_model=List[ChantierInfo])
def get_chantiers(
    _: models.Utilisateur = Depends(auth.roles_requis(models.RoleEnum.SPEC_ENV, models.RoleEnum.ADMIN,
                                                     models.RoleEnum.ANDE, models.RoleEnum.BAD))
):
    """Liste des chantiers PTUA avec coordonnées GPS."""
    return [ChantierInfo(**c) for c in CHANTIERS]


@router.get("/indices", response_model=List[IndicePoint])
def get_tous_indices(
    type_indice: Optional[str] = Query(None, description="NO2 | NDWI | NDVI | RISQUE_PLUIE"),
    _: models.Utilisateur = Depends(auth.roles_requis(models.RoleEnum.SPEC_ENV, models.RoleEnum.ADMIN,
                                                     models.RoleEnum.ANDE, models.RoleEnum.BAD))
):
    """Retourne les indices satellitaires courants (GEE temps réel) pour tous les chantiers."""
    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")
    results = []
    idx = 1

    for c in CHANTIERS:
        try:
            if type_indice and type_indice.upper() not in ("NO2", "NDVI", "NDWI", "RISQUE_PLUIE"):
                raise HTTPException(status_code=400, detail=f"Type '{type_indice}' inconnu")

            types_to_fetch = [type_indice.upper()] if type_indice else ["NO2", "NDVI", "NDWI", "RISQUE_PLUIE"]

            for t in types_to_fetch:
                try:
                    if t == "NO2":
                        data = get_no2(c["lon"], c["lat"])
                    elif t == "NDVI":
                        data = get_ndvi(c["lon"], c["lat"])
                    elif t == "NDWI":
                        data = get_ndwi(c["lon"], c["lat"])
                    elif t == "RISQUE_PLUIE":
                        data = get_risque_pluie(c["lon"], c["lat"])
                    else:
                        continue

                    results.append(IndicePoint(
                        id=idx,
                        type_indice=t,
                        valeur=data["valeur"],
                        unite=UNITES.get(t, data.get("unite", "")),
                        date_calcule=today,
                        chantier={"id": c["id"], "nom": c["nom"], "commune": c["commune"]},
                        statut=_build_statut(t, data["valeur"]),
                        tendance="STABLE",
                        source=SOURCES.get(t, "GEE"),
                    ))
                    idx += 1
                except Exception as e:
                    logger.warning(f"Erreur {t} chantier {c['nom']}: {e}")
                    results.append(IndicePoint(
                        id=idx,
                        type_indice=t,
                        valeur=0.0,
                        unite=UNITES.get(t, ""),
                        date_calcule=today,
                        chantier={"id": c["id"], "nom": c["nom"], "commune": c["commune"]},
                        statut="INCONNU",
                        tendance="STABLE",
                        source=SOURCES.get(t, "GEE"),
                    ))
                    idx += 1

        except HTTPException:
            raise

    return results


@router.get("/serie/{type_indice}", response_model=SerieTemporelle)
def get_serie_temporelle(
    type_indice: str,
    chantier_id: int = Query(1, description="ID du chantier (1-6)"),
    _: models.Utilisateur = Depends(auth.roles_requis(models.RoleEnum.SPEC_ENV, models.RoleEnum.ADMIN,
                                                     models.RoleEnum.ANDE, models.RoleEnum.BAD))
):
    """
    Série temporelle mensuelle (2022→2026) pour un chantier donné.
    Données réelles Google Earth Engine.
    """
    t = type_indice.upper()
    if t not in ("NO2", "NDVI", "NDWI", "RISQUE_PLUIE"):
        raise HTTPException(status_code=404, detail=f"Type '{t}' inconnu. Valeurs: NO2, NDVI, NDWI, RISQUE_PLUIE")

    if chantier_id < 1 or chantier_id > len(CHANTIERS):
        raise HTTPException(status_code=400, detail=f"chantier_id doit être entre 1 et {len(CHANTIERS)}")

    chantier = next((c for c in CHANTIERS if c["id"] == chantier_id), CHANTIERS[0])

    try:
        points = _fetch_serie_temporelle(t, chantier_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur série GEE: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur Earth Engine: {type(e).__name__}")

    return SerieTemporelle(
        type_indice=t,
        unite=UNITES.get(t, ""),
        description=DESCRIPTIONS.get(t, ""),
        chantier=f"{chantier['nom']} — {chantier['commune']}",
        points=[PointSerie(**p) for p in points],
    )


@router.get("/resume", response_model=ResumeSatellite)
def get_resume(
    _: models.Utilisateur = Depends(auth.roles_requis(models.RoleEnum.SPEC_ENV, models.RoleEnum.ADMIN,
                                                     models.RoleEnum.ANDE, models.RoleEnum.BAD))
):
    """Résumé synthétique des indicateurs satellitaires (GEE temps réel)."""
    from datetime import datetime

    no2_vals = []
    ndvi_vals = []
    ndwi_vals = []
    risque_vals = []

    for c in CHANTIERS:
        try:
            no2_vals.append(get_no2(c["lon"], c["lat"])["valeur"])
        except: pass
        try:
            ndvi_vals.append(get_ndvi(c["lon"], c["lat"])["valeur"])
        except: pass
        try:
            ndwi_vals.append(get_ndwi(c["lon"], c["lat"])["valeur"])
        except: pass
        try:
            risque_vals.append(get_risque_pluie(c["lon"], c["lat"])["valeur"])
        except: pass

    try:
        cloud = get_cloud_cover_pct()
    except:
        cloud = 18.4

    nb_alertes = sum(1 for v in no2_vals if v > 0.06)

    return ResumeSatellite(
        no2_moyen=round(sum(no2_vals) / len(no2_vals), 4) if no2_vals else 0.0,
        ndwi_moyen=round(sum(ndwi_vals) / len(ndwi_vals), 4) if ndwi_vals else 0.0,
        ndvi_moyen=round(sum(ndvi_vals) / len(ndvi_vals), 4) if ndvi_vals else 0.0,
        risque_pluie_max=round(max(risque_vals), 1) if risque_vals else 0.0,
        nb_alertes_qualite=nb_alertes,
        derniere_mise_a_jour=datetime.utcnow().strftime("%Y-%m-%d"),
        couverture_nuageuse_pct=cloud,
    )
