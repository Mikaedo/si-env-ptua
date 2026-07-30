"""
3_preparer_criticite.py
=======================
Prepare le dataset de classification (criticite) a partir du dataset YOLO TACO.

Logique : on compte le nombre de dechets (bounding boxes) par image.
  - 1-2 objets  -> faible
  - 3-5 objets  -> modere
  - 6+ objets   -> important

On copie les images dans dataset_criticite/train et dataset_criticite/val
avec la structure attendue par torchvision.ImageFolder.
"""
import os
import shutil
import random
from pathlib import Path

# --- parametres ---
SRC = Path("dataset")
DST = Path("dataset_criticite")
RATIO_VAL = 0.2   # 20% pour la validation
SEED = 42

random.seed(SEED)

def compter_objets(label_file):
    """Compte le nombre de lignes (= bounding boxes) dans un fichier label YOLO."""
    with open(label_file, "r") as f:
        lignes = [l.strip() for l in f if l.strip()]
    return len(lignes)

def categoriser(n):
    if n <= 2:
        return "faible"
    elif n <= 5:
        return "modere"
    else:
        return "important"

def preparer():
    # nettoyer l'ancien dossier
    if DST.exists():
        shutil.rmtree(DST)

    for split in ["train", "val"]:
        for cat in ["faible", "modere", "important"]:
            (DST / split / cat).mkdir(parents=True, exist_ok=True)

    # parcourir train et val du dataset YOLO
    stats = {"faible": 0, "modere": 0, "important": 0}

    for split_src in ["train", "valid"]:
        split_dst = "val" if split_src == "valid" else "train"
        img_dir = SRC / split_src / "images"
        lbl_dir = SRC / split_src / "labels"

        if not img_dir.exists():
            print(f"[!] Dossier introuvable : {img_dir}")
            continue

        images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.JPG")) + list(img_dir.glob("*.png"))

        for img_path in images:
            lbl_path = lbl_dir / (img_path.stem + ".txt")
            if not lbl_path.exists():
                continue

            n = compter_objets(lbl_path)
            cat = categoriser(n)
            stats[cat] += 1

            # pour train, on garde 80% ; pour val on utilise le split valid
            dst_dir = DST / split_dst / cat
            shutil.copy2(img_path, dst_dir / img_path.name)

    print(">> Dataset criticite prepare dans :", DST)
    print(">> Repartition :")
    for cat, count in stats.items():
        print(f"   {cat:12s} : {count} images")

    # afficher le contenu final
    for split in ["train", "val"]:
        for cat in ["faible", "modere", "important"]:
            n = len(list((DST / split / cat).glob("*")))
            print(f"   {split}/{cat:12s} : {n} images")

if __name__ == "__main__":
    preparer()
    print("\nTERMINE ! Tu peux lancer : python 2_entrainer_classification.py")
