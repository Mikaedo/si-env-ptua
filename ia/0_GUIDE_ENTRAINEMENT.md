# Guide d'entraînement IA — pas à pas (Anaconda)

Ce guide t'accompagne comme un prof. Suis les étapes **dans l'ordre**.
Tu vas produire les vrais résultats des **Tableaux 8.2 / 8.3** et la **Figure 8.1** de ton mémoire.

---

## Vue d'ensemble (à quoi ça sert)

Ton mémoire décrit une **cascade en 2 phases** :
1. **Détection (YOLOv8)** → *où* sont les déchets sur la photo.
2. **Classification (MobileNetV2)** → *quelle gravité* (faible / modéré / important).

On entraîne les deux séparément, puis on les exporte en **ONNX** pour le mobile.

---

## Étape 1 — Créer l'environnement Anaconda

Ouvre **Anaconda Prompt** :
```bash
conda create -n sienv-ia python=3.10 -y
conda activate sienv-ia
cd D:\etude_soutenance\SI-ENV\ia
pip install -r requirements_ia.txt
```

> **Note** : Python 3.10 est le plus stable pour PyTorch/Ultralytics.
> Si tu as une carte graphique NVIDIA, l'entraînement sera bien plus rapide,
> mais **ça marche aussi sur processeur** (juste plus lent).

---

## Étape 2 — Préparer le dataset TACO (détection)

TACO = jeu d'images de déchets annotées (cité dans ton mémoire, réf. dataset public).
Il est téléchargé automatiquement depuis son dépôt **GitHub officiel** (pas besoin de Roboflow).

### 2a. Télécharger les images (déjà lancé par Cascade)
Le dépôt est cloné dans `ia/TACO/`, et les ~1500 images se téléchargent via :
```bash
cd TACO
python download.py
```
> Ça prend ~25-30 min. Si la connexion coupe, relance la commande : elle reprend où elle s'était arrêtée.

### 2b. Convertir au format YOLO
TACO est au format COCO. On le convertit en format YOLO (1 classe « dechet ») avec :
```bash
cd D:\etude_soutenance\SI-ENV\ia
python preparer_taco_yolo.py
```
Cela crée automatiquement le dossier `dataset/` complet avec `data.yaml`,
et répartit les images en train (70%) / valid (20%) / test (10%) :
```
dataset/
├── data.yaml
├── train/{images,labels}
├── valid/{images,labels}
└── test/{images,labels}
```

> **Astuce mémoire** : ton Tableau 8.1 parle de 2000 images. TACO en contient ~1500,
> ce qui reste cohérent. Tu peux ajuster le chiffre du Tableau 8.1 à la valeur réelle obtenue.

---

## Étape 3 — Lancer la détection (Phase 1)

```bash
python 1_entrainer_detection.py
```
À la fin, regarde le dossier `runs_detection/dechets_yolov8n/` :
- `weights/best.pt` → ton modèle entraîné
- `weights/best.onnx` → version mobile
- `results.png` → **courbes d'apprentissage** (pour Figure 8.1)
- `confusion_matrix.png` → **matrice de confusion** (pour Figure 8.1)
- Le **mAP@0.5** s'affiche dans le terminal → note-le dans le **Tableau 8.2**.

> **Si erreur "out of memory"** : ouvre `1_entrainer_detection.py` et baisse
> `BATCH = 16` à `BATCH = 8` ou `4`.

---

## Étape 4 — Préparer le dataset de criticité (classification)

Ici, structure ultra-simple : **un dossier par niveau de gravité**.
```
dataset_criticite/
├── train/
│   ├── faible/     (photos peu de déchets)
│   ├── modere/     (photos moyennement)
│   └── important/  (photos beaucoup)
└── val/
    ├── faible/
    ├── modere/
    └── important/
```
Tu peux constituer ces images en découpant/triant des photos de déchets par densité.
Vise ~100-200 images par catégorie pour un premier essai.

---

## Étape 5 — Lancer la classification (Phase 2)

```bash
python 2_entrainer_classification.py
```
Résultats :
- Le **F1-score par classe** s'affiche → note-le dans le **Tableau 8.3**.
- `matrice_confusion_classification.png` → **Figure 8.1**.
- `mobilenetv2_criticite.onnx` → modèle pour le mobile.

---

## Étape 6 — Reporter les résultats dans le mémoire

1. Remplace les **objectifs visés** par les **vrais chiffres** obtenus (Tableaux 8.2, 8.3).
2. Insère les images (`results.png`, matrices de confusion) à la place de la **Figure 8.1**.
3. Ajuste une phrase de conclusion : *"les résultats confirment/nuancent les objectifs..."*.

---

## Récap des commandes (mémo)
```bash
conda activate sienv-ia
cd D:\etude_soutenance\SI-ENV\ia
python 1_entrainer_detection.py       # Phase 1 : détection
python 2_entrainer_classification.py  # Phase 2 : criticité
```

Tu as maintenant tout pour produire des **résultats réels** aujourd'hui. Bon entraînement !
