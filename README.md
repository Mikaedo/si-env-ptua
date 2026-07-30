# SI-ENV — Système de Suivi Environnemental (PTUA)

Code source accompagnant le mémoire. Deux briques à réaliser aujourd'hui :

## 1. Backend (API + base spatiale)
Dossier : [`backend/`](backend/README.md)
FastAPI + PostgreSQL/PostGIS. Auth JWT, signalements géolocalisés.
→ Suis **`backend/README.md`**.

## 2. Module IA (entraînement)
Dossier : [`ia/`](ia/0_GUIDE_ENTRAINEMENT.md)
YOLOv8 (détection) + MobileNetV2 (criticité), export ONNX.
→ Suis **`ia/0_GUIDE_ENTRAINEMENT.md`**.

## Ordre conseillé pour aujourd'hui
1. **Backend** : environnement conda → base (Docker) → `seed.py` → `uvicorn` → tester `/docs`.
2. **IA** : environnement conda → dataset TACO → `1_entrainer_detection.py` → `2_entrainer_classification.py`.

Chaque fichier de code contient des **commentaires pédagogiques** expliquant les notions.
