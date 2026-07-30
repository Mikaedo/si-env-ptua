"""
config.py
---------
Ce fichier centralise la CONFIGURATION de l'application.
Au lieu d'ecrire les mots de passe ou cles secretes directement dans le code,
on les lit depuis le fichier ".env". C'est une bonne pratique de securite :
le code peut etre partage sans divulguer les secrets.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # URL de connexion a la base PostgreSQL/PostGIS
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/sienv"
    # Cle utilisee pour signer les jetons JWT
    SECRET_KEY: str = "dev-secret-key"
    # Algorithme de signature du jeton
    ALGORITHM: str = "HS256"
    # Duree de validite d'un jeton en minutes
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Configuration SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"
# On cree une seule instance partagee dans toute l'application
settings = Settings()
