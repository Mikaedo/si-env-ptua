"""
database.py
-----------
Ce fichier etablit la CONNEXION a la base de donnees.

Notions simples :
- "engine"  : le moteur qui parle a PostgreSQL (comme un tuyau vers la base).
- "Session" : une conversation temporaire avec la base (on l'ouvre, on travaille, on la ferme).
- "Base"    : la classe mere de tous nos modeles (tables). Chaque table heritera d'elle.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings


def _nettoyer_url(url: str) -> str:
    """Robustifie la chaine de connexion avant de la passer au driver.

    Les secrets copies depuis une interface web arrivent regulierement avec un
    retour a la ligne ou des guillemets rescapes du copier-coller. psycopg2
    remonte alors des erreurs opaques (« invalid sslmode value ») qui pointent
    en apparence vers un parametre de connexion alors que le probleme est
    purement typographique.
    """
    if not url:
        return url
    url = url.strip()
    if (url.startswith('"') and url.endswith('"')) or \
       (url.startswith("'") and url.endswith("'")):
        url = url[1:-1]
    return url


# Le moteur de connexion. pool_pre_ping verifie que la connexion est vivante.
engine = create_engine(_nettoyer_url(settings.DATABASE_URL), pool_pre_ping=True)


# ── search_path pour PostGIS ──────────────────────────────────────────────
# Sur Supabase, PostGIS est installe dans le schema `topology` (verifie via
# verifier-supabase.yml). Le search_path par defaut (`public, extensions`) ne
# le couvre pas, donc les appels a ST_MakePoint, ST_SetSRID, geometry, etc.
# echouent avec « function does not exist ». On l'ajoute ici pour chaque
# nouvelle connexion tiree du pool. `public` reste en tete pour que
# `Base.metadata.create_all` continue de creer les tables applicatives dans le
# bon schema.
if engine.dialect.name == "postgresql":
    @event.listens_for(engine, "connect")
    def _forcer_search_path_postgis(dbapi_connection, _record):
        curseur = dbapi_connection.cursor()
        try:
            curseur.execute("SET search_path TO public, topology, extensions")
        finally:
            curseur.close()

# Fabrique de sessions : chaque requete HTTP ouvrira sa propre session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe de base dont heriteront tous les modeles (voir models.py)
Base = declarative_base()


def get_db():
    """
    Fonction "dependance" de FastAPI.
    Elle ouvre une session avant chaque requete et la ferme apres,
    meme en cas d'erreur (grace au try/finally).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
