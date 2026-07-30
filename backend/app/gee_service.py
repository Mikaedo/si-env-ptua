"""
gee_service.py
--------------
Service d'intégration Google Earth Engine pour SI-ENV.
Extrait les vraies données satellites (Sentinel-5P, Sentinel-2, CHIRPS, SRTM)
sur les chantiers PTUA d'Abidjan.

Sources :
  - NO2  : COPERNICUS/S5P/NRTI/L3_NO2 (Sentinel-5P/TROPOMI)
  - NDVI : COPERNICUS/S2_SR_HARMONIZED (Sentinel-2, bands B8/B4)
  - NDWI : COPERNICUS/S2_SR_HARMONIZED (Sentinel-2, bands B8/B11)
  - Risque pluie : UCSB-CHG/CHIRPS_DAILY + USGS/SRTMGL1_003 (pente)
"""
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional

import ee

logger = logging.getLogger("gee_service")

# ─── Authentification ─────────────────────────────────────
_SERVICE_ACCOUNT_KEY = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gee-service-account.json")
_initialized = False


def _init_ee():
    global _initialized
    if _initialized:
        return
    try:
        if os.path.exists(_SERVICE_ACCOUNT_KEY):
            credentials = ee.ServiceAccountCredentials(None, _SERVICE_ACCOUNT_KEY)
            ee.Initialize(credentials)
            logger.info("GEE initialisé avec service account")
        else:
            ee.Initialize()
            logger.info("GEE initialisé avec credentials par défaut")
        _initialized = True
    except Exception as e:
        logger.error(f"Erreur init GEE: {e}")
        raise


# ─── Cache simple (en mémoire) ────────────────────────────
_cache: dict = {}
_CACHE_TTL = 3600  # 1 heure


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(key: str, data):
    _cache[key] = {"ts": time.time(), "data": data}


# ─── Chantiers PTUA ───────────────────────────────────────
CHANTIERS = [
    {"id": 1, "nom": "Rocade Y4",           "commune": "Yopougon",        "lon": -4.048, "lat": 5.372},
    {"id": 2, "nom": "4e Pont d'Abidjan",   "commune": "Plateau/Adjamé",  "lon": -4.009, "lat": 5.356},
    {"id": 3, "nom": "Bd Latrille",          "commune": "Cocody",          "lon": -3.974, "lat": 5.348},
    {"id": 4, "nom": "Sortie Est",           "commune": "Bingerville",     "lon": -3.881, "lat": 5.338},
    {"id": 5, "nom": "Sortie Ouest",         "commune": "Yopougon/Songon", "lon": -4.103, "lat": 5.341},
    {"id": 6, "nom": "Échangeurs CG",        "commune": "Plateau",         "lon": -4.016, "lat": 5.319},
]

BUFFER_M = 2500  # 2.5 km autour de chaque chantier


def _buffer_point(lon: float, lat: float, meters: int = BUFFER_M) -> ee.Geometry:
    return ee.Geometry.Point([lon, lat]).buffer(meters)


# ─── NO2 (Sentinel-5P/TROPOMI) ────────────────────────────
def get_no2(lon: float, lat: float, days: int = 30) -> dict:
    """Retourne la moyenne NO2 troposphérique (µmol/m²) sur les N derniers jours."""
    cache_key = f"no2_{lon}_{lat}_{days}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    _init_ee()
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    roi = _buffer_point(lon, lat)

    collection = (
        ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_NO2")
        .select("tropospheric_NO2_column_number_density")
        .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        .filterBounds(roi)
    )

    image = collection.mean().clip(roi)
    val = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=roi,
        scale=7000,
        maxPixels=1e9,
    ).getInfo()

    raw = val.get("tropospheric_NO2_column_number_density")
    # Conversion: mol/m² → µmol/m² (x1e6)
    valeur = round((raw or 0) * 1e6, 4) if raw is not None else 0.0

    # Couverture nuageuse (%)
    cloud = collection.size().getInfo()
    result = {"valeur": valeur, "unite": "µmol/m²", "scenes": cloud}
    _cache_set(cache_key, result)
    return result


# ─── NDVI (Sentinel-2) ────────────────────────────────────
def get_ndvi(lon: float, lat: float, days: int = 30) -> dict:
    """NDVI = (B8 - B4) / (B8 + B4) — Sentinel-2."""
    cache_key = f"ndvi_{lon}_{lat}_{days}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    _init_ee()
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    roi = _buffer_point(lon, lat)

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        .filterBounds(roi)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
    )

    def _ndvi(img):
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        return img.addBands(ndvi)

    image = collection.map(_ndvi).select("NDVI").mean().clip(roi)
    val = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=roi,
        scale=20,
        maxPixels=1e9,
    ).getInfo()

    raw = val.get("NDVI")
    valeur = round(raw, 4) if raw is not None else 0.0
    scenes = collection.size().getInfo()

    result = {"valeur": valeur, "unite": "[-1 à +1]", "scenes": scenes}
    _cache_set(cache_key, result)
    return result


# ─── NDWI (Sentinel-2) ────────────────────────────────────
def get_ndwi(lon: float, lat: float, days: int = 30) -> dict:
    """NDWI = (B8 - B11) / (B8 + B11) — Sentinel-2."""
    cache_key = f"ndwi_{lon}_{lat}_{days}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    _init_ee()
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    roi = _buffer_point(lon, lat)

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        .filterBounds(roi)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
    )

    def _ndwi(img):
        ndwi = img.normalizedDifference(["B8", "B11"]).rename("NDWI")
        return img.addBands(ndwi)

    image = collection.map(_ndwi).select("NDWI").mean().clip(roi)
    val = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=roi,
        scale=20,
        maxPixels=1e9,
    ).getInfo()

    raw = val.get("NDWI")
    valeur = round(raw, 4) if raw is not None else 0.0
    scenes = collection.size().getInfo()

    result = {"valeur": valeur, "unite": "[-1 à +1]", "scenes": scenes}
    _cache_set(cache_key, result)
    return result


# ─── Risque pluie/érosion (CHIRPS + SRTM) ─────────────────
def get_risque_pluie(lon: float, lat: float, days: int = 30) -> dict:
    """
    Indice composite (0-10) basé sur:
    - Précipitations cumulées (CHIRPS)
    - Pente du terrain (SRTM)
    """
    cache_key = f"risque_{lon}_{lat}_{days}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    _init_ee()
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    roi = _buffer_point(lon, lat)

    # Précipitations cumulées
    chirps = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        .filterBounds(roi)
        .sum()
        .clip(roi)
    )

    precip_val = chirps.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=roi,
        scale=5000,
        maxPixels=1e9,
    ).getInfo()

    precip = precip_val.get("precipitation") or 0.0

    # Pente (SRTM)
    srtm = ee.Image("USGS/SRTMGL1_003")
    slope = ee.Terrain.slope(srtm).clip(roi)
    slope_val = slope.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=roi,
        scale=30,
        maxPixels=1e9,
    ).getInfo()

    pente = slope_val.get("slope") or 0.0

    # Indice composite normalisé 0-10
    # Précip: >200mm = fort, <50mm = faible
    # Pente: >15° = fort, <5° = faible
    precip_score = min(10, (precip / 200) * 10) if precip > 0 else 0
    slope_score = min(10, (pente / 15) * 10) if pente > 0 else 0
    risque = round((precip_score * 0.6 + slope_score * 0.4), 1)

    result = {
        "valeur": risque,
        "unite": "/10",
        "precip_mm": round(precip, 1),
        "pente_deg": round(pente, 1),
    }
    _cache_set(cache_key, result)
    return result


# ─── Série temporelle (historique) ────────────────────────
def get_serie_temporelle(
    type_indice: str,
    chantier_id: int,
    start_date: str = "2022-01-01",
    end_date: str = "2026-07-31",
) -> list:
    """
    Série temporelle mensuelle pour un chantier donné.
    Retourne une liste de {mois, valeur, phase}.
    """
    # 1) Vérifier le cache d'abord (pré-calculé dans gee_series_cache.json)
    cache_key = f"serie_{type_indice}_{chantier_id}_{start_date}_{end_date}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    # 2) Types valides
    types_valides = ("NO2", "NDVI", "NDWI", "RISQUE_PLUIE")
    if type_indice not in types_valides:
        raise ValueError(f"Type '{type_indice}' inconnu. Valeurs: {', '.join(types_valides)}")

    # 3) Initialiser GEE et préparer les données communes
    _init_ee()
    chantier = next((c for c in CHANTIERS if c["id"] == chantier_id), CHANTIERS[0])
    roi = _buffer_point(chantier["lon"], chantier["lat"])

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    def _phase(mois_str: str) -> str:
        y = int(mois_str[:4])
        m = int(mois_str[5:7])
        if y < 2023 or (y == 2023 and m <= 6):
            return "AVANT"
        elif y < 2025 or (y == 2025 and m <= 6):
            return "TRAVAUX"
        else:
            return "APRES"

    def _build_months(start, end):
        months = []
        current = start.replace(day=1)
        while current <= end:
            months.append(current)
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        return months

    months_list = _build_months(start_dt, end_dt)

    # 4) RISQUE_PLUIE : échantillonnage mensuel (55 points)
    if type_indice == "RISQUE_PLUIE":
        points = _compute_risque_pluie_series(roi, months_list, start_date, end_date, _phase)
        _cache_set(cache_key, points)
        return points

    # 5) NO2, NDVI, NDWI : échantillonnage semestriel (10 points)
    points = _compute_satellite_series(type_indice, roi, months_list, start_date, end_date, _phase)
    _cache_set(cache_key, points)
    return points


def _compute_risque_pluie_series(roi, months_list, start_date, end_date, phase_fn):
    """Calcule la série RISQUE_PLUIE avec CHIRPS + SRTM."""
    chirps_col = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterDate(start_date, end_date)
        .filterBounds(roi)
    )
    srtm = ee.Image("USGS/SRTMGL1_003")
    slope = ee.Terrain.slope(srtm).clip(roi)
    slope_val = slope.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=30, maxPixels=1e9).getInfo()
    pente = slope_val.get("slope") or 0.0
    slope_score = min(10, (pente / 15) * 10) if pente > 0 else 0

    points = []
    for m_dt in months_list:
        mois_str = m_dt.strftime("%Y-%m")
        if m_dt.month == 12:
            next_dt = m_dt.replace(year=m_dt.year + 1, month=1)
        else:
            next_dt = m_dt.replace(month=m_dt.month + 1)

        try:
            monthly_chirps = chirps_col.filterDate(
                m_dt.strftime("%Y-%m-%d"), next_dt.strftime("%Y-%m-%d")
            ).sum().clip(roi)
            precip_val = monthly_chirps.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=roi, scale=5000, maxPixels=1e9
            ).getInfo()
            precip = precip_val.get("precipitation") or 0.0
            precip_score = min(10, (precip / 200) * 10) if precip > 0 else 0
            risque = round(precip_score * 0.6 + slope_score * 0.4, 1)

            points.append({
                "mois": mois_str,
                "valeur": risque,
                "phase": phase_fn(mois_str),
            })
        except Exception as e:
            logger.warning(f"Erreur série RISQUE_PLUIE {mois_str}: {e}")

    return points


def _compute_satellite_series(type_indice, roi, months_list, start_date, end_date, phase_fn):
    """Calcule la série NO2/NDVI/NDWI avec échantillonnage semestriel."""
    if type_indice == "NO2":
        col = (
            ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_NO2")
            .select("tropospheric_NO2_column_number_density")
            .filterDate(start_date, end_date)
            .filterBounds(roi)
        )
        scale = 7000
        band = "tropospheric_NO2_column_number_density"
        multiplier = 1e6
    elif type_indice == "NDVI":
        col = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterDate(start_date, end_date)
            .filterBounds(roi)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
        )
        def _add_ndvi(img):
            return img.addBands(img.normalizedDifference(["B8", "B4"]).rename("NDVI"))
        col = col.map(_add_ndvi).select("NDVI")
        scale = 20
        band = "NDVI"
        multiplier = 1
    elif type_indice == "NDWI":
        col = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterDate(start_date, end_date)
            .filterBounds(roi)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
        )
        def _add_ndwi(img):
            return img.addBands(img.normalizedDifference(["B8", "B11"]).rename("NDWI"))
        col = col.map(_add_ndwi).select("NDWI")
        scale = 20
        band = "NDWI"
        multiplier = 1
    else:
        return []

    # Échantillonnage semestriel : Jan et Jul de chaque année
    semi_annual_months = months_list[::6]

    points = []
    for m_dt in semi_annual_months:
        mois_str = m_dt.strftime("%Y-%m")
        if m_dt.month <= 6:
            window_end = m_dt.replace(month=m_dt.month + 6)
        else:
            window_end = m_dt.replace(year=m_dt.year + 1, month=(m_dt.month + 6) % 12 or 12)

        try:
            monthly_col = col.filterDate(
                m_dt.strftime("%Y-%m-%d"), window_end.strftime("%Y-%m-%d")
            )
            img = monthly_col.mean().clip(roi)
            val = img.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=roi, scale=scale, maxPixels=1e9
            ).getInfo()
            raw = val.get(band)
            if raw is not None:
                valeur = round(raw * multiplier, 4)
                points.append({
                    "mois": mois_str,
                    "valeur": valeur,
                    "phase": phase_fn(mois_str),
                })
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Erreur série {type_indice} {mois_str}: {e}")
            time.sleep(2)

    return points


def _get_monthly_no2(roi, start, end):
    col = (
        ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_NO2")
        .select("tropospheric_NO2_column_number_density")
        .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        .filterBounds(roi)
        .mean()
        .clip(roi)
    )
    val = col.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=7000, maxPixels=1e9).getInfo()
    raw = val.get("tropospheric_NO2_column_number_density")
    return round(raw * 1e6, 4) if raw is not None else None


def _get_monthly_ndvi(roi, start, end):
    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        .filterBounds(roi)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
    )
    def _ndvi(img):
        return img.addBands(img.normalizedDifference(["B8", "B4"]).rename("NDVI"))
    img = col.map(_ndvi).select("NDVI").mean().clip(roi)
    val = img.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=20, maxPixels=1e9).getInfo()
    raw = val.get("NDVI")
    return round(raw, 4) if raw is not None else None


def _get_monthly_ndwi(roi, start, end):
    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        .filterBounds(roi)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
    )
    def _ndwi(img):
        return img.addBands(img.normalizedDifference(["B8", "B11"]).rename("NDWI"))
    img = col.map(_ndwi).select("NDWI").mean().clip(roi)
    val = img.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=20, maxPixels=1e9).getInfo()
    raw = val.get("NDWI")
    return round(raw, 4) if raw is not None else None


def _get_monthly_risque(roi, start, end):
    chirps = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        .filterBounds(roi)
        .sum()
        .clip(roi)
    )
    precip_val = chirps.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=5000, maxPixels=1e9).getInfo()
    precip = precip_val.get("precipitation") or 0.0

    srtm = ee.Image("USGS/SRTMGL1_003")
    slope = ee.Terrain.slope(srtm).clip(roi)
    slope_val = slope.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=30, maxPixels=1e9).getInfo()
    pente = slope_val.get("slope") or 0.0

    precip_score = min(10, (precip / 200) * 10) if precip > 0 else 0
    slope_score = min(10, (pente / 15) * 10) if pente > 0 else 0
    return round(precip_score * 0.6 + slope_score * 0.4, 1)


# ─── Couverture nuageuse ──────────────────────────────────
def get_cloud_cover_pct() -> float:
    """Retourne le % moyen de couverture nuageuse sur Abidjan (Sentinel-2)."""
    cache_key = "cloud_cover_pct"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    _init_ee()
    end = datetime.utcnow()
    start = end - timedelta(days=7)
    roi = ee.Geometry.Point([-4.008, 5.355]).buffer(10000)

    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        .filterBounds(roi)
    )

    cloud = col.aggregate_mean("CLOUDY_PIXEL_PERCENTAGE").getInfo()
    pct = round(cloud, 1) if cloud is not None else 18.4

    _cache_set(cache_key, pct)
    return pct


# ─── Pre-computation au démarrage ─────────────────────────
import json as _json

_SERIES_CACHE_FILE = os.environ.get("GEE_CACHE_FILE", os.path.join(os.path.dirname(os.path.dirname(__file__)), "gee_series_cache.json"))


def _load_series_cache():
    """Charge les series pre-calculees depuis le fichier JSON."""
    try:
        cache_file = os.environ.get("GEE_CACHE_FILE", _SERIES_CACHE_FILE)
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                data = _json.load(f)
                for key, value in data.items():
                    _cache_set(key, value)
                logger.info(f"Cache series GEE charge: {len(data)} entrees")
        else:
            logger.warning(f"Fichier cache series introuvable: {cache_file}")
    except Exception as e:
        logger.warning(f"Erreur chargement cache series: {e}")


def precompute_series():
    """Charge les series pre-calculees depuis le fichier JSON au demarrage."""
    _load_series_cache()


# Charger le cache au moment de l'import du module
_load_series_cache()
