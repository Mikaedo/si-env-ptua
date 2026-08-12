# Dockerfile pour Hugging Face Spaces (SDK Docker).
#
# Trois specificites par rapport au Dockerfile local :
#   1. Port 7860 (contrainte HF), et non 8000.
#   2. Aucune reference au certificat racine Avast : l'environnement HF n'a
#      pas d'antivirus a inspection SSL.
#   3. Utilisateur non-root (contrainte HF Spaces).
#
# Les fichiers du repertoire backend/ sont copies via un contexte de build
# etendu. HF Spaces autorise la directive `context` dans le README uniquement
# pour docker-compose ; en SDK docker, on triche en copiant tout le sous-arbre
# necessaire dans deploy/huggingface/ juste avant le push. Voir le script
# deploy/huggingface/publier.sh.

FROM python:3.12-slim

# HF Spaces impose un utilisateur non-root avec HOME defini.
RUN useradd -m -u 1000 sienv
ENV HOME=/home/sienv \
    PATH=/home/sienv/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependances Python
COPY --chown=sienv:sienv requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Code applicatif
COPY --chown=sienv:sienv app ./app
COPY --chown=sienv:sienv seed.py .

USER sienv

EXPOSE 7860

# HF injecte parfois un PORT dynamique via l'env : on s'y adapte, avec 7860
# en repli. `--proxy-headers` fait confiance a l'en-tete X-Forwarded-For pose
# par le reverse proxy HF, sans quoi la journalisation IP est fausse.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --proxy-headers"]
