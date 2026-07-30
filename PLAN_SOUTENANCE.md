# SI-ENV — Plan de Soutenance

> **Objectif** : Livrer le mémoire final d'ici le **7 août 2026**, finir tout (présentation incluse) d'ici le **20 août 2026**.
>
> Sujet : *Conception et Réalisation d'un Système de Suivi Environnemental des Chantiers du PTUA*
>
> Étudiant : N'GUESSAN Diby Konanbouo Georges Mikaël — L3 MIAGE, UPB Bingerville

---

## 1. Architecture globale du SI-ENV (5 modules)

| Module | Technologie | Rôle |
|--------|------------|------|
| Mobile | Flutter + SQLite | App terrain (inspecteurs) — offline-first |
| Backend | FastAPI + PostgreSQL/PostGIS | API REST + auth JWT + RBAC |
| IA | YOLOv8n + MobileNetV2 (ONNX) | Détection déchets + classification criticité |
| Dashboard | Angular | Tableau de bord web (coordinateur) |
| Satellite | Google Earth Engine + Sentinel-2/5P | NDWI, NDVI, qualité air |

---

## 2. TÂCHES TERMINÉES ✅

### 2.1 Backend FastAPI

- [x] API REST complète (FastAPI + Uvicorn)
- [x] Authentification JWT (access token + refresh)
- [x] RBAC : 5 rôles (RESP_ENV, EXPERT_HSE, SPEC_ENV, SPEC_PAR, ADMIN)
- [x] Router auth : login, register, me, first-login, change-password, forgot, verify-code, reset-password
- [x] Router signalements : CRUD complet + filtres (statut, criticité, type nuisance, chantier, période)
- [x] Router alertes : lister + accuser réception
- [x] Router chantiers : liste
- [x] Router statistiques : totaux, taux traitement, répartition, évolution
- [x] Base PostgreSQL + PostGIS (schéma complet : utilisateurs, chantiers, signalements, photos, alertes, actions_correctives, non_conformites, plaintes)
- [x] Index spatial GIST sur signalements.localisation
- [x] Docker Compose (db + backend + nginx)
- [x] Dockerfile backend
- [x] Fichiers `.env` + `.env.example`
- [x] Script seed (comptes test, chantiers, signalements)
- [x] Tests backend (pytest + httpx)
- [x] **Flux first-login modifié** : admin crée user (email + rôle seulement), user complète profil (nom + téléphone + mot de passe) à la première connexion
- [x] Login sans mot de passe pour première connexion (token temporaire avec `premiere_connexion: true`)

### 2.2 Application Mobile Flutter

- [x] Architecture BLoC pattern (AuthBloc, SignalementBloc, SyncBloc)
- [x] Mode offline-first (SQLite local + sync async)
- [x] Écran de connexion (design moderne avec logo PTUA)
- [x] Écran first-login (nom complet + téléphone + mot de passe)
- [x] Écran changement mot de passe
- [x] Écran mot de passe oublié (code de réinitialisation)
- [x] Navigation principale avec bottom nav (Carte, Signalements, Stats, Profil)
- [x] **Navigation différenciée par rôle** :
  - RESP_ENV : FAB "+" + onglet "Mes signaux"
  - EXPERT_HSE : pas de FAB + onglet "File" + bannière "en attente"
- [x] Carte interactive (flutter_map) avec :
  - Zones chantier GeoJSON (polygones colorés)
  - Pins signalements avec couleur par criticité
  - Filtres par zone/chantier
  - Toggle Plan/Satellite (overflow corrigé)
  - Bouton localisation GPS
  - Top bar avec logo + titre + toggle + notifications
- [x] Liste signalements avec :
  - Stats Bento (Total, Nouveaux, En cours, Traités)
  - Recherche textuelle
  - Filtres (statut, criticité, type nuisance, chantier, période)
  - Cards modernes avec barre d'accent + ombre + icône IA
  - TagChip pour statut et criticité
- [x] Écran détail signalement (avec actions correctives pour EXPERT_HSE, lecture seule pour RESP_ENV)
- [x] Écran nouveau signalement (photo, GPS auto, type, criticité, description, IA diagnostic)
- [x] Écran statistiques (dashboard avec gauge, KPIs, progress bars, charts, pull-to-refresh)
- [x] Écran profil
- [x] Écran paramètres
- [x] Écran alertes
- [x] Écran synchronisation
- [x] Écran confirmation
- [x] Accents français corrigés sur tous les écrans
- [x] Points milieu "·" remplacés par tirets longs "—"
- [x] Overflow carte (Plan → Satellite) corrigé
- [x] Lint warnings corrigés

### 2.3 Intelligence Artificielle

- [x] Entraînement YOLOv8n (détection déchets) — dataset Recycle Trash, 2 462 images, 6 classes
- [x] Entraînement MobileNetV2 (classification criticité) — export ONNX
- [x] Benchmark détection : YOLOv8n vs SSD300 vs Faster R-CNN (tableau 8.2)
  - YOLOv8n : mAP@0.5 = 0,798, Precision = 0,792, Rappel = 0,722, F1 = 0,755, Inference = 4,3ms
- [x] Benchmark classification : MobileNetV2 vs ResNet50 vs VGG16 (tableau 8.3)
  - MobileNetV2 : Precision = 0,87, Rappel = 0,87, F1 = 0,86, Taille = 8,9 Mo, Inference = 15,2ms
- [x] Tableau hyperparamètres (tableau 8.4) : LR, batch, epochs, augmentation, etc.
- [x] Figures IA générées : métriques par classe, matrices de confusion, courbes PR
- [x] Modèles ONNX prêts (yolov8n.pt, mobilenetv2_criticite.onnx)
- [x] Scripts d'entraînement complets (1_entrainer_detection.py, 2_entrainer_classification.py, 3_preparer_criticite.py)
- [x] Captures d'output pour annexes

### 2.4 Mémoire

- [x] Document complet v56 (TACO remplacé par Recycle Trash)
- [x] Figures et tableaux IA mis à jour (tableaux 8.1 à 8.4, figures 8.1 à 8.4)
- [x] Légendes de figures mises à jour
- [x] Référence bibliographique Recycle Trash ajoutée [23]
- [x] Résumé et abstract mis à jour (TACO → Recycle Trash)
- [x] Table des matières automatique activée
- [x] Documentation technique complète (DOCUMENTATION_COMPLETE_SI-ENV_PTUA.md)
- [x] Analyse existant et besoins (ANALYSE_EXISTANT_BESOINS_SI-ENV.md)
- [x] Planning 1 mois (PLANNING_1_MOIS_MEMOIRE_SI-ENV.md)

---

## 3. TÂCHES RESTANTES ❌

### 3.1 Dashboard Web Angular — **NON COMMENCÉ** ⚠️

> **Priorité : HAUTE** — mentionné dans l'architecture du mémoire, doit exister pour la soutenance

- [ ] Initialiser projet Angular (TypeScript strict, standalone components)
- [ ] Authentification JWT (shared avec backend)
- [ ] Carte des chantiers (Leaflet + données PostGIS)
- [ ] Tableau de bord avec statistiques globales (KPIs, charts)
- [ ] Liste des signalements avec filtres avancés
- [ ] Gestion des alertes (liste + accusé réception)
- [ ] Génération de rapports PDF (format BAD)
- [ ] Gestion des utilisateurs (ADMIN : créer, désactiver)
- [ ] WebSocket pour alertes temps réel (bonus)
- [ ] Build statique pour Nginx
- [ ] Intégration dans docker-compose

### 3.2 Notifications & Emails — **NON FAIT** ⚠️

> **Priorité : MOYENNE** — le jury demandera comment les alertes sont notifiées

- [ ] Configurer SMTP Gmail (app password)
- [ ] Service `email_service.py` dans le backend (aiosmtplib)
- [ ] Envoi email automatique quand signalement ELEVE est créé
- [ ] Génération automatique d'alertes en DB (déclencheur sur signalement critique)
- [ ] Push notifications Firebase (bonus — si temps)
- [ ] WebSocket alertes temps réel (bonus)

### 3.3 Module Satellite (GEE + Sentinel) — **NON COMMENCÉ** ⚠️

> **Priorité : MOYENNE** — mentionné dans le mémoire chapitre 4, doit avoir au moins un script + figures

- [ ] Script Google Earth Engine (NDWI, NDVI avec Sentinel-2)
- [ ] Script GEE qualité air (NO₂, AOD avec Sentinel-5P)
- [ ] Comparaison avant/après travaux (2022 vs 2025-2026)
- [ ] Figures pour le mémoire (cartes NDWI/NDVI, séries temporelles)
- [ ] Endpoint backend `/satellite/ndwi`, `/satellite/ndvi` (bonus)
- [ ] Intégration dashboard Angular (bonus)

### 3.4 Déploiement Production — **NON COMMENCÉ** ⚠️

> **Priorité : HAUTE** — le jury demandera "est-ce vraiment déployé ?"

- [ ] Choix hébergement VPS (DigitalOcean / OVH / Railway / Render)
- [ ] Déploiement Docker Compose en production (db + backend + nginx + Angular)
- [ ] Certificat SSL Let's Encrypt (HTTPS)
- [ ] Configuration Nginx reverse proxy (/api/* → FastAPI, /* → Angular)
- [ ] Variables d'environnement production (secrets sécurisés, .env)
- [ ] Build APK Flutter en release (signé)
- [ ] Test de l'app mobile en conditions réelles (API HTTPS)
- [ ] Test du dashboard en ligne

### 3.5 Tests & Validation — **PARTIEL** ⚠️

> **Priorité : MOYENNE**

- [ ] Tests end-to-end (mobile → API → DB)
- [ ] Tests de charge sur l'API (locust ou similar)
- [ ] Tests offline/sync du mobile (créer signalement offline, vérifier sync)
- [ ] Validation IA sur données réelles PTUA (si autorisation photos chantier)
- [ ] Captures d'écran pour le mémoire (dashboard, carte mobile, IA, etc.)
- [ ] Vidéo démo (bonus)

### 3.6 Mémoire — Finalisation ⚠️

> **Deadline : 7 août 2026**

- [ ] Relecture complète du mémoire v56
- [ ] Vérifier cohérence : ce qui est écrit = ce qui est implémenté
- [ ] Ajouter captures du dashboard Angular (une fois développé)
- [ ] Ajouter figures satellite (une fois scripts GEE faits)
- [ ] Mettre à jour le chapitre déploiement (une fois déployé)
- [ ] Mettre à jour les annexes (captures du dashboard, config déploiement)
- [ ] Vérifier formatage (canevas UPB : marges, polices, numérotation)
- [ ] Correction orthographique et grammaticale finale
- [ ] Génération PDF final
- [ ] Impression et reliure

### 3.7 Présentation (PowerPoint) — **NON COMMENCÉ** ⚠️

> **Deadline : 20 août 2026**

- [ ] Structure du diaporama (15-20 slides) :
  - Slide 1 : Titre + étudiant + encadrant
  - Slide 2 : Contexte (PTUA, Catégorie 1 BAD, PGES)
  - Slide 3 : Problématique (suivi manuel insuffisant)
  - Slide 4 : Objectifs du SI-ENV
  - Slide 5 : Architecture globale (schéma 5 modules)
  - Slide 6 : Choix technologiques (Flutter, FastAPI, Angular, PostGIS)
  - Slide 7-8 : Application mobile (captures : carte, signalements, stats)
  - Slide 9-10 : Backend & API (schéma, endpoints, RBAC)
  - Slide 11-12 : Intelligence Artificielle (YOLOv8, MobileNetV2, benchmark)
  - Slide 13 : Module satellite (GEE + Sentinel)
  - Slide 14 : Dashboard web (captures)
  - Slide 15 : Déploiement (Docker, VPS, HTTPS)
  - Slide 16 : Résultats & performances
  - Slide 17 : Difficultés rencontrées
  - Slide 18 : Perspectives d'amélioration
  - Slide 19 : Conclusion
  - Slide 20 : Remerciements + Q&A
- [ ] Design moderne (template professionnel, couleurs AGEROUTE)
- [ ] Schémas et diagrammes (architecture, flux de données)
- [ ] Captures d'écran intégrées (mobile + dashboard + IA)
- [ ] Tableaux de résultats (benchmark IA)
- [ ] Démo live préparée (mobile + dashboard + IA en direct)
- [ ] Fiche de synthèse / résumé de soutenance
- [ ] Révisions questions jury (cf. Partie 7 documentation)

---

## 4. PLANNING — Du 26 juillet au 20 août 2026

### Semaine 1 : 26 juillet → 2 août
| Tâche | Durée estimée | Statut |
|------|---------------|--------|
| Dashboard Angular — init + auth + carte | 3 jours | À faire |
| Dashboard Angular — stats + signalements + alertes | 2 jours | À faire |
| Notifications email (SMTP Gmail + alertes auto) | 1 jour | À faire |

### Semaine 2 : 3 août → 9 août
| Tâche | Durée estimée | Statut |
|------|---------------|--------|
| Dashboard Angular — users + rapports PDF + build | 2 jours | À faire |
| **Mémoire final — relecture + captures + figures** | 3 jours | À faire |
| **Livraison mémoire final : 7 août** | — | Deadline |
| Module satellite (GEE scripts + figures) | 2 jours | À faire |

### Semaine 3 : 10 août → 16 août
| Tâche | Durée estimée | Statut |
|------|---------------|--------|
| Déploiement production (VPS + Docker + SSL) | 2 jours | À faire |
| Build APK release + test conditions réelles | 1 jour | À faire |
| Tests end-to-end + corrections | 2 jours | À faire |
| Captures d'écran pour mémoire + présentation | 1 jour | À faire |

### Semaine 4 : 17 août → 20 août
| Tâche | Durée estimée | Statut |
|------|---------------|--------|
| Présentation PowerPoint (15-20 slides) | 2 jours | À faire |
| Révisions questions jury | 1 jour | À faire |
| Démo live rehearsal | 0,5 jour | À faire |
| **Tout fini : 20 août** | — | Deadline |

---

## 5. RISQUES & MITIGATIONS

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Dashboard Angular trop long à développer | Retard planning | Garder scope minimal (carte + stats + liste), pas de WebSocket |
| Module satellite complexe (GEE) | Retard mémoire | Faire juste 1-2 scripts + figures, pas d'intégration backend |
| Déploiement VPS coûteux | Bloquant | Utiliser Railway/Render free tier ou VPS OVH pas cher |
| IA non testée sur données réelles PTUA | Question jury | Documenter honnêtement comme perspective (déjà fait dans mémoire) |
| App mobile bugs résiduels | Mauvaise impression démo | Tests approfondis semaine 3 |

---

## 6. COMPTES DE TEST

| Email | Rôle | Mot de passe | Première connexion |
|-------|------|-------------|-------------------|
| admin@sienv.ci | ADMIN | admin123 | Non |
| resp.env@ageroute.ci | RESP_ENV | env123 | Non |
| expert.hse@ageroute.ci | EXPERT_HSE | expert123 | Non |
| spec.env@ageroute.ci | SPEC_ENV | spec123 | Non |
| nouveau@ageroute.ci | RESP_ENV | (à définir) | **Oui** — test first login |

---

## 7. CHECKLIST FINALE SOUTENANCE

- [ ] Mémoire imprimé et relié (7 août)
- [ ] APK Flutter installable signé
- [ ] Backend déployé en production (HTTPS)
- [ ] Dashboard Angular accessible en ligne
- [ ] Présentation PowerPoint prête
- [ ] Démo live fonctionnelle (mobile + dashboard + IA)
- [ ] Fiche de synthèse
- [ ] Questions jury révisées
- [ ] Captures d'écran de tous les écrans
- [ ] Vidéo démo de backup (en cas de panne réseau)

---

*Dernière mise à jour : 26 juillet 2026*
