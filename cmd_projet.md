# Commandes de démarrage — SI-ENV

## 1. Backend (Docker — 3 conteneurs : db, backend, nginx)

```powershell
cd D:\etude_soutenance\SI-ENV\backend

# Démarrer les conteneurs
docker compose up -d

# Vérifier que tout tourne
docker ps

# Arrêter les conteneurs
docker compose down

# Rebuilder après modification du code
docker compose up -d --build
```

API accessible sur :
- `http://localhost:8000/docs` (direct backend)
- `http://localhost:80/docs` (via nginx)

---

## 2. Mobile (Flutter)

```powershell
cd D:\etude_soutenance\SI-ENV\mobile

# Récupérer les dépendances
flutter pub get

# Lancer l'app (émulateur ou device connecté)
flutter run

# Lancer sur Chrome (si pas d'émulateur)
flutter run -d chrome
```

---

## 3. Tests

### Tests backend (pytest)

```powershell
cd D:\etude_soutenance\SI-ENV\backend
python -m pytest tests/ -v
```

### Tests mobile (flutter test)

```powershell
cd D:\etude_soutenance\SI-ENV\mobile
flutter test
```

---

## 4. Accès aux services

| Service      | URL / Port          |
|--------------|---------------------|
| API direct   | `localhost:8000`    |
| Via nginx    | `localhost:80`      |
| PostgreSQL   | `localhost:5433`    |
| Swagger docs | `localhost:8000/docs` |
