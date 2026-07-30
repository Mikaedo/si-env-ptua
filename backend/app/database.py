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

# Le moteur de connexion. pool_pre_ping verifie que la connexion est vivante.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

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
