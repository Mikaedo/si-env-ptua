"""
conftest.py
-----------
Configuration pytest pour les tests du backend SI-ENV.
Utilise une base SQLite en memoire avec mock des colonnes Geometry PostGIS.
"""
import os
import sys

# --- Patch GeoAlchemy2 AVANT tout import de l'app ---
# Remplace le type Geometry par String pour SQLite
from sqlalchemy import String as SAString
import geoalchemy2.types
geoalchemy2.types.Geometry = lambda *a, **kw: SAString()
geoalchemy2.types._GISType = lambda *a, **kw: SAString()
import geoalchemy2
geoalchemy2.Geometry = lambda *a, **kw: SAString()
geoalchemy2.Geography = lambda *a, **kw: SAString()

os.environ["DATABASE_URL"] = "sqlite:///./test_sienv.db"

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app import models, auth

# Engine SQLite pour les tests
engine = create_engine("sqlite:///./test_sienv.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_test_tables():
    """Cree les tables SQLite en remplacant Geometry par String."""
    for tbl in Base.metadata.tables.values():
        for col in list(tbl.columns):
            if 'Geometry' in str(type(col.type).__name__) or 'geoalchemy' in str(col.type).lower():
                col.type = SAString(255)
    Base.metadata.create_all(bind=engine)


# Importer l'app apres les patches
from app.main import app

# Override du startup event pour eviter la connexion PostgreSQL
@app.on_event("startup")
def _test_startup():
    Base.metadata.drop_all(bind=engine)
    _create_test_tables()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def _setup_db():
    """Recreer les tables avant chaque test."""
    Base.metadata.drop_all(bind=engine)
    _create_test_tables()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Cree une session de test fraiche pour chaque test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """Client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def admin_user(db_session):
    user = models.Utilisateur(
        nom="Admin Test",
        email="admin@test.com",
        mot_de_passe_hash=auth.hasher_mot_de_passe("admin123"),
        role=models.RoleEnum.ADMIN,
        premiere_connexion=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def resp_env_user(db_session):
    user = models.Utilisateur(
        nom="Agent Test",
        email="agent@test.com",
        mot_de_passe_hash=auth.hasher_mot_de_passe("agent123"),
        role=models.RoleEnum.RESP_ENV,
        premiere_connexion=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def expert_hse_user(db_session):
    user = models.Utilisateur(
        nom="Expert Test",
        email="expert@test.com",
        mot_de_passe_hash=auth.hasher_mot_de_passe("expert123"),
        role=models.RoleEnum.EXPERT_HSE,
        premiere_connexion=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    return auth.creer_token({"sub": str(admin_user.id), "role": admin_user.role.value})


@pytest.fixture
def resp_env_token(resp_env_user):
    return auth.creer_token({"sub": str(resp_env_user.id), "role": resp_env_user.role.value})


@pytest.fixture
def expert_token(expert_hse_user):
    return auth.creer_token({"sub": str(expert_hse_user.id), "role": expert_hse_user.role.value})


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def agent_headers(resp_env_token):
    return {"Authorization": f"Bearer {resp_env_token}"}


@pytest.fixture
def expert_headers(expert_token):
    return {"Authorization": f"Bearer {expert_token}"}


@pytest.fixture
def chantier(db_session):
    c = models.Chantier(nom="Pont de Bassam", commune="Bassam")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


@pytest.fixture
def ande_user(db_session):
    """Agent de l'Agence Nationale de l'Environnement, en consultation seule."""
    user = models.Utilisateur(
        nom="Controleur ANDE",
        email="controle@ande.ci",
        mot_de_passe_hash=auth.hasher_mot_de_passe("ande123"),
        role=models.RoleEnum.ANDE,
        premiere_connexion=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def bad_user(db_session):
    """Charge de mission de la Banque Africaine de Developpement."""
    user = models.Utilisateur(
        nom="Mission BAD",
        email="mission@afdb.org",
        mot_de_passe_hash=auth.hasher_mot_de_passe("bad123"),
        role=models.RoleEnum.BAD,
        premiere_connexion=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def ande_headers(ande_user):
    jeton = auth.creer_token({"sub": str(ande_user.id), "role": ande_user.role.value})
    return {"Authorization": f"Bearer {jeton}"}


@pytest.fixture
def bad_headers(bad_user):
    jeton = auth.creer_token({"sub": str(bad_user.id), "role": bad_user.role.value})
    return {"Authorization": f"Bearer {jeton}"}
