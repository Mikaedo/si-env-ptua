---
title: SI-ENV Backend
emoji: 🌱
colorFrom: blue
colorTo: orange
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: API FastAPI de suivi environnemental des chantiers du PTUA
---

# SI-ENV Backend — API FastAPI

Backend du projet **SI-ENV** (Système d'Information Environnemental) déployé
sur Hugging Face Spaces au titre du mémoire MIAGE.

Ce Space fournit l'API REST consommée par le tableau de bord Angular et
l'application mobile Flutter.

## Documentation interactive

Une fois le Space démarré, la documentation Swagger UI est accessible à
`/docs` sous l'URL publique du Space.

## Variables d'environnement requises

Ces secrets sont configurés dans les **Settings → Variables and secrets** du
Space, pas dans ce dépôt.

| Variable | Description |
|---|---|
| `DATABASE_URL` | Chaîne de connexion PostgreSQL Supabase (avec `?sslmode=require`) |
| `SECRET_KEY` | Clé de signature des jetons JWT |
| `CORS_ORIGINS` | Domaines du dashboard, séparés par des virgules |
| `SUPABASE_URL` | URL du projet Supabase (`https://<projet>.supabase.co`) |
| `SUPABASE_SERVICE_ROLE_KEY` | Clé de service Supabase (secret) |
| `SUPABASE_BUCKET` | Nom du bucket de photos (par défaut `photos`) |
| `PHOTO_STORAGE` | `supabase` en prod, `local` en dev |
| `GEE_SERVICE_ACCOUNT_JSON` | Contenu JSON de la clé du compte de service Google Earth Engine |
| `SEED_ON_STARTUP` | `true` pour peupler la base au premier démarrage |

## Architecture

Voir le chapitre 4 du mémoire pour l'architecture d'ensemble. Ce déploiement
substitue Supabase à PostgreSQL/PostGIS local et Supabase Storage à
l'écriture sur disque, sans modification du modèle de données.
