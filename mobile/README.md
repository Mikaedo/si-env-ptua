# SI-ENV Mobile

Application Flutter de Suivi Environnemental des chantiers du PTUA - AGEROUTE.

## Architecture

- **Pattern** : BLoC (flutter_bloc 8.1.3)
- **State management** : AuthBloc, SignalementBloc, SyncBloc
- **Local storage** : SQLite (sqflite 2.3.0) - mode offline-first
- **API client** : HTTP (http 1.2.0) - FastAPI backend
- **Maps** : flutter_map 8.3.0 + OpenStreetMap
- **GPS** : geolocator 10.1.0
- **Camera** : image_picker 1.0.7
- **AI** : onnxruntime 1.16.0 (YOLOv8n + MobileNetV2)

## Structure

```
lib/
  main.dart                    # Entry point + MultiBlocProvider
  core/
    constants.dart             # Colors, API URL, enums
  models/
    models.dart                # Utilisateur, Signalement, Alerte, etc.
  services/
    api_service.dart           # HTTP client (auth, signalements, stats...)
    local_database.dart        # SQLite offline storage
  blocs/
    auth/auth_bloc.dart        # Login, first-login, logout
    signalement/signalement_bloc.dart  # CRUD signalements
    sync/sync_bloc.dart        # Synchronisation offline -> online
  screens/
    login_screen.dart          # Ecran de connexion
    first_login_screen.dart    # Premiere connexion (definir mot de passe)
    forgot_password_screen.dart# Mot de passe oublie (3 etapes)
    main_navigation.dart       # Bottom nav (Carte, Signalements, Stats, Profil)
    map_screen.dart            # Carte avec markers
    nouveau_signalement_screen.dart  # Creation signalement (5 types)
    confirmation_screen.dart   # Confirmation apres creation
    signalements_list_screen.dart  # Liste avec recherche
    signalement_detail_screen.dart  # Detail + action corrective + retour agent
    filters_screen.dart        # Filtres (statut, criticite, type, chantier, periode)
    stats_screen.dart          # Statistiques avec graphiques
    alertes_screen.dart        # Alertes + accuser reception
    sync_screen.dart           # Synchronisation manuelle
    profile_screen.dart        # Profil utilisateur
    change_password_screen.dart# Changer mot de passe
    settings_screen.dart       # Parametres app
```

## Backend API

- Base URL : `http://10.0.2.2:8000` (emulator) / `http://localhost:8000` (desktop)
- FastAPI + PostgreSQL 16 + PostGIS 3.4
- JWT authentication
- Endpoints : /auth/*, /signalements/*, /chantiers, /alertes/*, /stats

## Demarrage

```bash
flutter pub get
flutter run
```
