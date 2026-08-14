"""
main.py
-------
Point d'ENTREE de l'application. C'est le fichier que uvicorn lance.

Il fait 3 choses :
1. Cree l'application FastAPI.
2. Active PostGIS et cree les tables si elles n'existent pas.
3. Branche les routers (auth, signalements) et autorise le dashboard (CORS).
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from sqlalchemy import text
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import os

from .config import settings
from .database import Base, engine
from .routers import auth_router, signalements_router, chantiers_router, alertes_router, stats_router, satellite_router, rapports_router, plaintes_router, admin_router
from .services import erreur_service

# Cree l'application avec un titre visible dans la doc Swagger
app = FastAPI(
    title="SI-ENV API",
    description="API de suivi environnemental des chantiers du PTUA.",
    version="1.0.0",
)

# Rate limiting embarque. La cle est l'IP source (via l'entete X-Forwarded-For
# pose par le reverse proxy Render), avec un plancher par defaut de 500
# requetes/minute par IP pour ne pas bloquer les usages legitimes du
# tableau de bord ou du mobile.
limiter = Limiter(key_func=get_remote_address, default_limits=["500/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware de capture d'erreurs : chaque exception non geree est persistee
# en base pour consultation admin (equivalent Sentry embarque, cf.
# app/services/erreur_service.py).
erreur_service.gestionnaire_exceptions(app)

# CORS : autorise le tableau de bord Angular (localhost:4200) a appeler l'API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Consultation seule pour l'ANDE et la BAD ──────────────────────────────
# Le regulateur national et le bailleur consultent le dispositif sans jamais
# y ecrire. La restriction est posee en amont du routage plutot que sur chaque
# operation : un endpoint ajoute plus tard sera couvert d'office, alors qu'une
# dependance a repeter finit toujours par etre oubliee quelque part. Masquer
# les boutons dans le tableau de bord ne suffirait pas, une requete construite
# a la main contournerait l'interface.
_METHODES_ECRITURE = {"POST", "PUT", "PATCH", "DELETE"}

# Operations qui touchent au compte de la personne elle-meme, et non aux
# donnees du projet. Les interdire enfermerait un consultant hors de sa
# propre session.
_CHEMINS_TOLERES = {
    "/auth/login",
    "/auth/logout",
    "/auth/refresh",
    "/auth/first-login",
    "/auth/change-password",
    "/auth/forgot",
    "/auth/verify-code",
    "/auth/reset-password",
    "/auth/2fa/verifier",
    "/auth/2fa/configurer",
}


@app.middleware("http")
async def restreindre_consultation(request: Request, call_next):
    if request.method in _METHODES_ECRITURE and request.url.path not in _CHEMINS_TOLERES:
        entete = request.headers.get("authorization", "")
        if entete.lower().startswith("bearer "):
            try:
                charge = jwt.decode(
                    entete.split(" ", 1)[1],
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                if charge.get("role") in {"ANDE", "BAD"}:
                    return JSONResponse(
                        status_code=403,
                        content={
                            "detail": "Votre profil donne un acces en consultation. "
                                      "La modification des donnees releve des equipes AGEROUTE."
                        },
                    )
            except JWTError:
                # Jeton illisible : ce n'est pas a ce middleware de trancher,
                # la dependance d'authentification renverra un 401 en aval.
                pass
    return await call_next(request)


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

    # 2 bis) Micro-migration : create_all n'ajoute pas les colonnes manquantes
    # aux tables existantes. On ajoute ici les colonnes recentes de facon
    # idempotente pour eviter d'introduire Alembic sur un projet de cette
    # taille. Chaque ALTER est protege par IF NOT EXISTS (PostgreSQL) ou par
    # un try/catch pour SQLite.
    def _ajouter_colonne_si_absente(nom_table: str, nom_col: str, definition: str):
        with engine.connect() as conn:
            dialecte = conn.dialect.name
            if dialecte == "postgresql":
                try:
                    conn.execute(text(
                        f'ALTER TABLE {nom_table} ADD COLUMN IF NOT EXISTS {nom_col} {definition}'
                    ))
                    conn.commit()
                except Exception as e:  # pragma: no cover
                    logger.warning("ALTER %s.%s : %s", nom_table, nom_col, e)
            else:
                # SQLite ne connait pas IF NOT EXISTS pour ADD COLUMN.
                try:
                    conn.execute(text(f'ALTER TABLE {nom_table} ADD COLUMN {nom_col} {definition}'))
                    conn.commit()
                except Exception:
                    pass  # deja presente, on ignore

    _ajouter_colonne_si_absente(
        "utilisateurs", "twofa_email_actif", "BOOLEAN NOT NULL DEFAULT FALSE"
    )

    # Colonnes introduites avec les huit profils et le canal citoyen. Le meme
    # mecanisme idempotent s'applique : create_all cree les tables absentes
    # mais ne touche jamais a celles qui existent deja, or la base de production
    # porte des donnees qu'il n'est pas question de reconstruire.
    _ajouter_colonne_si_absente(
        "chantiers", "rayon_influence_m", "INTEGER NOT NULL DEFAULT 1500"
    )
    _ajouter_colonne_si_absente(
        "utilisateurs", "chantier_rattachement_id", "INTEGER"
    )
    _ajouter_colonne_si_absente(
        "alertes_seuils", "chantier_id", "INTEGER"
    )
    for nom_colonne, definition in (
        ("plaignant_id", "INTEGER"),
        ("categorie", "VARCHAR(40)"),
        ("photo_chemin", "VARCHAR(255)"),
        ("canal", "VARCHAR(20) DEFAULT 'GUICHET'"),
    ):
        _ajouter_colonne_si_absente("plaintes", nom_colonne, definition)

    # La colonne geometrique passe par le type PostGIS, absent sous SQLite ou
    # les tests tournent. On la traite donc a part, sans faire echouer le
    # demarrage si le dialecte ne la comprend pas.
    if engine.dialect.name == "postgresql":
        _ajouter_colonne_si_absente(
            "plaintes", "geom", "geometry(Point, 4326)"
        )

    # Les trois nouveaux profils doivent exister dans le type enumere cote
    # PostgreSQL, sans quoi toute insertion les mentionnant serait rejetee.
    # ADD VALUE IF NOT EXISTS est rejoue sans risque a chaque demarrage.
    if engine.dialect.name == "postgresql":
        with engine.connect() as conn:
            for valeur in ("ANDE", "BAD", "PLAIGNANT"):
                try:
                    conn.execute(
                        text(f"ALTER TYPE roleenum ADD VALUE IF NOT EXISTS '{valeur}'")
                    )
                    conn.commit()
                except Exception as e:  # pragma: no cover
                    logger.warning("ALTER TYPE roleenum %s : %s", valeur, e)

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
