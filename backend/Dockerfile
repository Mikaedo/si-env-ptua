FROM python:3.12-slim

WORKDIR /app

# psycopg2-binary et geoalchemy2 ne necessitent pas de paquets systeme supplementaires
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code et la clé GEE
COPY . .

# Exposer le port
EXPOSE 8000

# Lancer avec uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
