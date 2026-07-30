"""
preparer_taco_yolo.py
=====================
TACO est fourni au format COCO (un gros fichier annotations.json).
YOLOv8 attend un autre format : un fichier .txt par image, et un data.yaml.

Ce script fait la CONVERSION automatiquement :
1. Lit les annotations COCO de TACO.
2. Fusionne les 60 categories TACO en UNE SEULE classe "dechet" (coherent avec ton memoire, nc=1).
3. Convertit les boites (bbox) au format YOLO normalise (x_centre, y_centre, largeur, hauteur).
4. Repartit les images en train / valid / test (70 / 20 / 10 %).
5. Ecrit le fichier dataset/data.yaml pret pour l'entrainement.

LANCE-MOI APRES la fin du telechargement des images (download.py) :
    python preparer_taco_yolo.py
"""
import json
import os
import random
import shutil

# --- Chemins ---
TACO_DIR = "TACO/data"                     # ou sont les images + annotations.json
ANN_FILE = os.path.join(TACO_DIR, "annotations.json")
SORTIE = "dataset"                          # dossier de sortie au format YOLO

random.seed(42)  # pour une repartition reproductible

# --- 1) Lecture des annotations COCO ---
print(">> Lecture des annotations TACO...")
with open(ANN_FILE, "r", encoding="utf-8") as f:
    coco = json.load(f)

# Index : id_image -> infos (nom de fichier, largeur, hauteur)
images = {img["id"]: img for img in coco["images"]}

# Regroupe les annotations (boites) par image
boites_par_image = {}
for ann in coco["annotations"]:
    boites_par_image.setdefault(ann["image_id"], []).append(ann["bbox"])

# --- 2) Repartition train / valid / test ---
ids = list(images.keys())
random.shuffle(ids)
n = len(ids)
n_train = int(0.7 * n)
n_val = int(0.2 * n)
split = {
    "train": ids[:n_train],
    "valid": ids[n_train:n_train + n_val],
    "test": ids[n_train + n_val:],
}
print(f">> {n} images : {len(split['train'])} train / {len(split['valid'])} valid / {len(split['test'])} test")

# --- 3) Creation des dossiers ---
for part in ["train", "valid", "test"]:
    os.makedirs(f"{SORTIE}/{part}/images", exist_ok=True)
    os.makedirs(f"{SORTIE}/{part}/labels", exist_ok=True)

# --- 4) Conversion + copie ---
manquantes = 0
for part, id_list in split.items():
    for img_id in id_list:
        info = images[img_id]
        src = os.path.join(TACO_DIR, info["file_name"])  # ex: batch_1/000006.jpg
        if not os.path.isfile(src):
            manquantes += 1
            continue

        # Nom de fichier plat (on remplace le / du sous-dossier batch par _)
        nom_plat = info["file_name"].replace("/", "_").replace("\\", "_")
        base = os.path.splitext(nom_plat)[0]

        # Copie l'image
        shutil.copy(src, f"{SORTIE}/{part}/images/{nom_plat}")

        # Ecrit le fichier label YOLO correspondant
        W, H = info["width"], info["height"]
        lignes = []
        for (x, y, w, h) in boites_par_image.get(img_id, []):
            # COCO bbox = [x_coin, y_coin, largeur, hauteur] en pixels
            # YOLO veut : classe x_centre y_centre largeur hauteur (tout normalise 0..1)
            xc = (x + w / 2) / W
            yc = (y + h / 2) / H
            wn = w / W
            hn = h / H
            lignes.append(f"0 {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}")  # 0 = classe "dechet"

        with open(f"{SORTIE}/{part}/labels/{base}.txt", "w") as lf:
            lf.write("\n".join(lignes))

if manquantes:
    print(f"!! {manquantes} images non trouvees (telechargement incomplet ?)")

# --- 5) Ecriture du data.yaml ---
chemin_abs = os.path.abspath(SORTIE).replace("\\", "/")
yaml = f"""# Configuration dataset YOLO - TACO (1 classe)
path: {chemin_abs}
train: train/images
val: valid/images
test: test/images

nc: 1
names: ['dechet']
"""
with open(f"{SORTIE}/data.yaml", "w", encoding="utf-8") as f:
    f.write(yaml)

print(">> Conversion terminee ! Dataset pret dans 'dataset/'.")
print(">> Tu peux maintenant lancer : python 1_entrainer_detection.py")
