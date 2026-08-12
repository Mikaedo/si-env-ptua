"""
database.py
-----------
Ce fichier etablit la CONNEXION a la base de donnees.

Notions simples :
- "engine"  : le moteur qui parle a PostgreSQL (comme un tuyau vers la base).
- "Session" : une conversation temporaire avec la base (on l'ouvre, on travaille, on la ferme).
- "Base"    : la classe mere de tous nos modeles (tables). Chaque table heritera d'elle.
"""
from sqlalchemy import create_engine
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
