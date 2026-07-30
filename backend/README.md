# Backend SI-ENV (FastAPI + PostgreSQL/PostGIS)

API de suivi environnemental des chantiers du PTUA.
Ce guide te fait démarrer **pas à pas**. Suis-le dans l'ordre.

---

## 1. Prérequis
- **Anaconda** installé (tu l'utilises déjà).
- **Une base PostgreSQL avec PostGIS**. Deux options ci-dessous : choisis-en **une**.

---

## 2. Créer l'environnement Python (Anaconda)

Ouvre **Anaconda Prompt**, puis :

```bash
conda create -n sienv python=3.12 -y
conda activate sienv
cd D:\etude_soutenance\SI-ENV\backend
pip install -r requirements.txt
```

> **Explication** : on crée un environnement isolé `sienv` pour ne pas mélanger
> les librairies de ce projet avec celles des autres.

---

## 3. Préparer la base de données

### Option A — Docker (le plus simple, recommandé)
Si tu as **Docker Desktop** :
```bash
docker compose up -d
```
La base est prête sur `localhost:5433`. Rien d'autre à faire.

> **Pourquoi 5433 et non 5432 ?** Un **PostgreSQL 18 est déjà installé** sur ta machine
> et occupe le port 5432. Pour éviter le conflit, la base Docker écoute sur **5433**.
> Le fichier `.env` pointe déjà vers ce port.

### Option B — PostgreSQL installé manuellement
1. Installe PostgreSQL 16 + l'extension PostGIS (via Stack Builder).
2. Crée une base nommée `sienv`.
3. L'extension PostGIS sera activée automatiquement au démarrage de l'API.

---

## 4. Configurer les secrets

Copie le fichier d'exemple en `.env` :
```bash
copy .env.example .env
```
Ouvre `.env` et vérifie que `DATABASE_URL` correspond bien à ta base.
(Par défaut : `postgresql://postgres:postgres@localhost:5433/sienv`.)

---

## 5. Initialiser les données de test
```bash
python seed.py
```
Cela crée un compte **admin@sienv.ci / admin123** et un chantier de démo.

---

## 6. Lancer l'API
```bash
uvicorn app.main:app --reload
```
Ouvre ton navigateur sur **http://localhost:8000/docs**
→ c'est la **documentation Swagger** (Figure 7.1 de ton mémoire !).

---

## 7. Tester en 30 secondes (dans /docs)
1. `POST /auth/login` → mets `username = admin@sienv.ci`, `password = admin123`.
   Copie le `access_token` renvoyé.
2. Clique sur le bouton **Authorize** (en haut à droite), colle le token.
3. `POST /signalements` → crée un signalement de test.
4. `GET /signalements` → tu vois ton signalement. 🎉

---

## Structure du projet
```
backend/
├── app/
│   ├── main.py            # point d'entrée de l'API
│   ├── config.py          # configuration (.env)
│   ├── database.py        # connexion à PostgreSQL
│   ├── models.py          # tables (Utilisateur, Chantier, Signalement...)
│   ├── schemas.py         # formats JSON entrée/sortie
│   ├── auth.py            # mots de passe + JWT
│   └── routers/
│       ├── auth_router.py         # /auth/*
│       └── signalements_router.py # /signalements/*
├── seed.py                # données de départ
├── docker-compose.yml     # base PostGIS clé en main
├── requirements.txt
└── .env.example
```
