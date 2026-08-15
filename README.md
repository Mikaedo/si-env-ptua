# SI-ENV — Système d'Information Environnemental (PTUA)

## Démarrage rapide

**Double-cliquez sur `demarrer_demo.bat`** — tout démarre en un clic :

- Docker : backend FastAPI, PostgreSQL/PostGIS, nginx
- Redirection USB vers le téléphone (adb reverse)
- L'application mobile sur votre téléphone connecté
- Le tableau de bord dans votre navigateur

Puis, quand vous avez fini, **double-cliquez sur `arreter_demo.bat`**.

### Prérequis

- Docker Desktop ouvert
- Téléphone Android branché en USB, débogage USB activé
- L'APK déjà installé sur le téléphone (voir plus bas)

## URL de production (déploiement cloud)

Aucune installation, accessible depuis n'importe quel navigateur, 24/7.

| Service | URL |
|---|---|
| Tableau de bord | https://si-env-ptua.pages.dev |
| API + Swagger | https://si-env-ptua.onrender.com/docs |
| Dépôt code | https://github.com/Mikaedo/si-env-ptua |

## Les deux applications mobiles

Le projet produit deux applications distinctes, bâties sur un socle de code
commun et installables côte à côte sur un même téléphone.

| Fichier | Pour qui | Identifiant Android |
|---|---|---|
| `SI-ENV_agent.apk` | Agents AGEROUTE sur le terrain | `ci.ageroute.si_env` |
| `SI-ENV_citoyen.apk` | Riverains des chantiers | `ci.ageroute.si_env.citoyen` |

L'application citoyenne vérifie la position au premier lancement : elle n'ouvre
l'inscription qu'aux personnes situées dans la zone d'influence d'un chantier,
périmètre que le spécialiste du suivi environnemental fixe ouvrage par ouvrage.

## Comptes de démonstration

**Tableau de bord web**

| Rôle | Email | Mot de passe |
|---|---|---|
| Spécialiste Environnement | spec.env@ageroute.ci | spec123 |
| Spécialiste P.A.R (volet social) | spec.par@ageroute.ci | spec123 |
| Administrateur | admin@sienv.ci | admin123 |
| ANDE (consultation) | controle@ande.ci | ande123 |
| BAD (consultation) | mission@afdb.org | bad123 |

**Application des agents** (`SI-ENV_agent.apk`)

| Rôle | Email | Mot de passe |
|---|---|---|
| Responsable Environnement | resp.env@ageroute.ci | env123 |
| Expert HSE | expert.hse@ageroute.ci | expert123 |

**Application citoyenne** (`SI-ENV_citoyen.apk`)

Aucun compte préexistant : le riverain s'inscrit lui-même depuis l'application,
après vérification de sa position.

L'ANDE et la BAD accèdent au tableau de bord en lecture seule. Le serveur refuse
toute écriture émise avec leur jeton, y compris hors de l'interface.

## Structure du projet

```
SI-ENV/
├── demarrer_demo.bat     Lanceur en un clic
├── arreter_demo.bat      Arrêt propre
├── backend/              FastAPI + PostgreSQL + services IA/satellite
├── dashboard/            Angular (tableau de bord web)
├── mobile/               Flutter (application terrain)
├── deploy/               Recettes de déploiement (Cloudflare, Hugging Face)
├── ia/                   Modèles entraînés, jeu de données, scripts
│   └── _archive/         Anciens scripts de génération, gardés en cas de besoin
└── .github/workflows/    CI/CD, watchdog, health check, self-heal
```

## Reconstruire les applications mobiles

Chaque application correspond à une variante Android, avec son propre point
d'entrée :

```powershell
cd mobile

# Application des agents AGEROUTE
flutter build apk --release --flavor agent -t lib/main.dart

# Application citoyenne
flutter build apk --release --flavor citoyen -t lib/main_citoyen.dart
```

Les fichiers produits se trouvent dans `build/app/outputs/flutter-apk/`.

Installation sur un téléphone branché en USB :

```powershell
adb install -r build/app/outputs/flutter-apk/app-agent-release.apk
adb install -r build/app/outputs/flutter-apk/app-citoyen-release.apk
```

L'URL du backend pointe déjà sur Render (`si-env-ptua.onrender.com`). Pour viser
la pile Docker locale (avec `adb reverse`) :

```powershell
flutter build apk --release --flavor agent -t lib/main.dart --dart-define="API_URL=http://127.0.0.1:8000"
```

## Documentation

- Mémoire complet : `MEMOIRE_N'GUESSAN_DIBY_FINAL.pdf`
- Guide de soutenance : `GUIDE_PREPARATION_SOUTENANCE_SI-ENV.docx`
- Interprétation des figures : `INTERPRETATION_FIGURES_STATISTIQUES_SI-ENV.docx`
