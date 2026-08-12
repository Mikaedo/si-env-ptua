"""
main.py
-------
Point d'ENTREE de l'application. C'est le fichier que uvicorn lance.

Il fait 3 choses :
1. Cree l'application FastAPI.
2. Active PostGIS et cree les tables si elles n'existent pas.
3. Branche les routers (auth, signalements) et autorise le dashboard (CORS).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
import os

from .database import Base, engine
from .routers import auth_router, signalements_router, chantiers_router, alertes_router, stats_router, satellite_router, rapports_router, plaintes_router, admin_router

# Cree l'application avec un titre visible dans la doc Swagger
app = FastAPI(
    title="SI-ENV API",
    description="API de suivi environnemental des chantiers du PTUA.",
    version="1.0.0",
)

# CORS : autorise le tableau de bord Angular (localhost:4200) a appeler l'API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def au_demarrage():
    import logging
    logger = logging.getLogger("startup")

    # 1) Active l'extension PostGIS (necessaire pour le type Geometry).
    # Sur Supabase, PostGIS est deja installee : la commande est un no-op.
    # Sur les hebergeurs sans droit CREATE EXTENSION, on veut pas empecher
    # le demarrage : on journalise et on continue.
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            conn.commit()
    except Exception as e:  # pragma: no cover
        logger.warning("PostGIS non actif au demarrage (peut-etre deja present) : %s", e)

    # 2) Cree toutes les tables definies dans models.py (si absentes)
    Base.metadata.create_all(bind=engine)

    # 3) Seed idempotent, uniquement si demande explicitement. Utile pour un
    # premier bootstrap sur une base neuve (Supabase, HF Spaces).
    if os.getenv("SEED_ON_STARTUP", "").lower() in ("1", "true", "yes"):
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from seed import executer_seed  # noqa: E402
            logger.info("SEED_ON_STARTUP=true : execution du seed idempotent")
            executer_seed()
        except Exception as e:
            logger.error("Seed au demarrage echoue : %s", e)


# Branche les groupes d'endpoints
app.include_router(auth_router.router)
app.include_router(signalements_router.router)
app.include_router(chantiers_router.router)
app.include_router(alertes_router.router)
app.include_router(stats_router.router)
app.include_router(satellite_router.router)
app.include_router(rapports_router.router)
app.include_router(plaintes_router.router)
app.include_router(admin_router.router)

# Sert les photos uploadees depuis le mobile.
# En mode Supabase Storage, les octets sont servis par Supabase et le montage
# local devient inutile. On ne le monte que si le stockage est local.
if os.getenv("PHOTO_STORAGE", "local").lower() == "local":
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/", tags=["Sante"])
def racine():
    """Petit endpoint de test : verifie que l'API repond."""
    return {"message": "SI-ENV API operationnelle", "docs": "/docs"}
