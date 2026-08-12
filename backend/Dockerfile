FROM python:3.12-slim

WORKDIR /app

# psycopg2-binary et geoalchemy2 ne necessitent pas de paquets systeme supplementaires
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier uniquement le code applicatif : la cle GEE, les caches locaux et
# les uploads sont explicitement exclus par .dockerignore. En prod la cle
# arrive via la variable d'environnement GEE_SERVICE_ACCOUNT_JSON ; en dev
# le fichier est monte en volume par docker-compose.
COPY . .

# Exposer le port
EXPOSE 8000

# Lancer avec uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
