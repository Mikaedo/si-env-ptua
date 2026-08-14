"""
precompute_gee.py
-----------------
Script standalone pour pré-calculer toutes les séries temporelles GEE
et les sauvegarder dans gee_series_cache.json.

Usage: docker exec sienv_backend python precompute_gee.py
"""
import json
import time
import sys
import os

# Initialiser GEE
import ee
key_path = os.path.join(os.path.dirname(__file__), "gee-service-account.json")
ee.Initialize(ee.ServiceAccountCredentials(None, key_path))

sys.path.insert(0, os.path.dirname(__file__))
from app.gee_service import get_serie_temporelle, _cache_get
from app.database import SessionLocal
from app.services.geo_service import chantiers_geolocalises

# Le referentiel des chantiers est lu en base : ce script suit donc
# automatiquement les ajouts et retraits faits par le specialiste
# environnemental, sans qu'il faille le remettre a jour a la main.
_session = SessionLocal()
CHANTIERS = chantiers_geolocalises(_session)
_session.close()

TYPES = ["NO2", "NDVI", "NDWI", "RISQUE_PLUIE"]
CACHE_FILE = os.path.join(os.path.dirname(__file__), "gee_series_cache.json")

cache_data = {}

for t in TYPES:
    for chantier in CHANTIERS:
        cid = chantier["id"]
        cache_key = f"serie_{t}_{cid}_2022-01-01_2026-07-31"
        print(f"Calculating {t} pour {chantier['nom']}...", end=" ", flush=True)
        try:
            pts = get_serie_temporelle(t, cid, lon=chantier["lon"], lat=chantier["lat"])
            cache_data[cache_key] = pts
            print(f"OK ({len(pts)} points)")
        except Exception as e:
            print(f"ERROR: {str(e)[:100]}")
        time.sleep(3)  # Pause entre chaque pour éviter le rate limiting

# Sauvegarder
with open(CACHE_FILE, "w") as f:
    json.dump(cache_data, f, ensure_ascii=False, indent=2)

print(f"\nCache saved to {CACHE_FILE} ({len(cache_data)} entries)")
