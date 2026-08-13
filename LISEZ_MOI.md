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

## Comptes de démonstration

| Rôle | Email | Mot de passe |
|---|---|---|
| Spécialiste Environnement | spec.env@ageroute.ci | spec123 |
| Administrateur | admin@sienv.ci | admin123 |
| Expert HSE | expert.hse@ageroute.ci | expert123 |
| Spécialiste P.A.R | spec.par@ageroute.ci | spec123 |

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

## Reconstruire l'APK mobile

Dans PowerShell :

```powershell
cd mobile
flutter build apk --release
adb install -r build/app/outputs/flutter-apk/app-release.apk
```

L'URL du backend est déjà pointée sur Render (`si-env-ptua.onrender.com`). Pour cibler
la pile Docker locale (avec `adb reverse`), utilisez :

```powershell
flutter build apk --release --dart-define="API_URL=http://127.0.0.1:8000"
```

## Documentation

- Mémoire complet : `MEMOIRE_N'GUESSAN_DIBY_FINAL.pdf`
- Guide de soutenance : `GUIDE_PREPARATION_SOUTENANCE_SI-ENV.docx`
- Interprétation des figures : `INTERPRETATION_FIGURES_STATISTIQUES_SI-ENV.docx`
