"""
1_entrainer_detection.py  (PHASE 1 : DETECTION avec YOLOv8)
==========================================================

OBJECTIF (rappel du memoire, chapitre 8.3) :
Apprendre a un modele a REPERER les dechets sur une photo (dessiner une boite autour).

COMMENT CA MARCHE, simplement :
- YOLO = "You Only Look Once". Il regarde l'image une seule fois et dit
  "il y a un dechet ici, dans ce rectangle".
- On part d'un modele DEJA entraine (yolov8n.pt) et on le "specialise" sur nos dechets :
  c'est le TRANSFER LEARNING. On n'apprend pas de zero, on adapte. C'est plus rapide
  et cela demande beaucoup moins d'images.

CE DONT TU AS BESOIN AVANT DE LANCER :
- Un dataset au format YOLO decrit par un fichier "data.yaml".
  (Voir 0_GUIDE_ENTRAINEMENT.md, section "Preparer le dataset TACO".)

LANCE-MOI AINSI (dans Anaconda Prompt, env active) :
    python 1_entrainer_detection.py
"""
from ultralytics import YOLO

# ------------------------------------------------------------------
# PARAMETRES : tu peux les ajuster. Correspondent au Tableau 8.4 du memoire.
# ------------------------------------------------------------------
CHEMIN_DATA_YAML = "dataset/data.yaml"  # decrit ou sont les images + les classes
NB_EPOCHS = 10        # nombre de passages sur tout le dataset (10 = rapide sur CPU)
TAILLE_IMAGE = 320    # taille reduite a 320 pour accelerer l'entrainement sur CPU
BATCH = 8             # nombre d'images traitees en meme temps (8 = adapte au CPU)

# 1) On charge le petit modele pre-entraine "nano" (le plus leger, ideal mobile)
print(">> Chargement du modele de base YOLOv8n...")
model = YOLO("yolov8n.pt")   # se telecharge automatiquement la 1ere fois

# 2) On lance l'entrainement (la partie qui prend du temps)
print(">> Debut de l'entrainement (cela peut durer un moment)...")
resultats = model.train(
    data=CHEMIN_DATA_YAML,
    epochs=NB_EPOCHS,
    imgsz=TAILLE_IMAGE,
    batch=BATCH,
    project="runs_detection",   # dossier ou tout sera sauvegarde
    name="dechets_yolov8n",
)

# 3) On evalue le modele sur les images de test -> donne le mAP (Tableau 8.2)
print(">> Evaluation du modele...")
metriques = model.val()
print("mAP@0.5     :", metriques.box.map50)   # la metrique cle de ton memoire
print("mAP@0.5:0.95:", metriques.box.map)

# 4) On exporte au format ONNX pour l'executer sur le telephone (chapitre 8.6)
print(">> Export au format ONNX (pour le mobile)...")
model.export(format="onnx")

print("\nTERMINE ! Regarde le dossier 'runs_detection/dechets_yolov8n/'.")
print("- weights/best.pt   : ton meilleur modele")
print("- weights/best.onnx : version pour le mobile")
print("- results.png       : courbes d'apprentissage (Figure 8.1 du memoire)")
print("- confusion_matrix.png : matrice de confusion (Figure 8.1 du memoire)")
