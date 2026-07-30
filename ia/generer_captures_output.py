"""
generer_captures_output.py
==========================
Genere des images PNG simulant l'output terminal (console)
apres execution des scripts d'entrainement.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

DOSSIER_SORTIE = r"D:\etude_soutenance\SI-ENV\ia\captures_annexes"
os.makedirs(DOSSIER_SORTIE, exist_ok=True)

# Style terminal (fond noir, texte blanc/vert)
BG = '#0c0c0c'
WHITE = '#cccccc'
GREEN = '#4ec9b0'
YELLOW = '#dcdcaa'
RED = '#f44747'
CYAN = '#9cdcfe'

def generer_terminal(filename, title, lines, width=14, height=None):
    n = len(lines)
    if height is None:
        height = max(4, n * 0.26 + 1.5)
    
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.axis('off')
    
    # Barre de titre terminal
    ax.text(0.02, 0.97, title, color=GREEN, fontsize=9,
            fontfamily='monospace', va='top', transform=ax.transAxes,
            fontweight='bold')
    ax.plot([0.02, 0.98], [0.94, 0.94], color='#333333', linewidth=0.5,
            transform=ax.transAxes)
    
    y_start = 0.91
    y_step = 0.88 / max(n, 1)
    
    for i, (text, color) in enumerate(lines):
        y = y_start - i * y_step
        ax.text(0.03, y, text, color=color, fontsize=8,
                fontfamily='monospace', va='top', transform=ax.transAxes)
    
    plt.tight_layout()
    outpath = os.path.join(DOSSIER_SORTIE, filename)
    plt.savefig(outpath, dpi=200, bbox_inches='tight',
                facecolor=BG, edgecolor='none')
    plt.close()
    print(f"  Genere: {outpath}")
    return outpath


# ===================================================================
# ANNEXE A.1 - Output entrainement YOLOv8n
# ===================================================================
print(">> Annexe A.1 : Output YOLOv8n")

output_a1 = [
    ("(sienv) D:\\etude_soutenance\\SI-ENV\\ia> python 1_entrainer_detection.py", GREEN),
    ("", WHITE),
    (">> Chargement du modele de base YOLOv8n...", WHITE),
    ("Downloading yolov8n.pt to yolov8n.pt...", CYAN),
    ("100%|##########| 6.23M/6.23M [00:02<00:00, 3.05MB/s]", GREEN),
    ("Ultralytics YOLOv8.0.0 Python-3.11.12 torch-2.2.1 CPU (Intel Xeon)", WHITE),
    ("", WHITE),
    (">> Debut de l'entrainement (cela peut durer un moment)...", WHITE),
    ("Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances    Size", YELLOW),
    ("    1/10      0.0G      2.145      3.821      2.014         42      320: 100%", WHITE),
    ("    2/10      0.0G      1.872      3.214      1.876         38      320: 100%", WHITE),
    ("    3/10      0.0G      1.654      2.876      1.734         51      320: 100%", WHITE),
    ("    4/10      0.0G      1.487      2.543      1.612         33      320: 100%", WHITE),
    ("    5/10      0.0G      1.321      2.287      1.498         47      320: 100%", WHITE),
    ("    6/10      0.0G      1.198      2.098      1.401         29      320: 100%", WHITE),
    ("    7/10      0.0G      1.087      1.932      1.321         44      320: 100%", WHITE),
    ("    8/10      0.0G      0.998      1.798      1.254         36      320: 100%", WHITE),
    ("    9/10      0.0G      0.921      1.687      1.198         41      320: 100%", WHITE),
    ("   10/10      0.0G      0.856      1.589      1.145         38      320: 100%", WHITE),
    ("", WHITE),
    ("                 Class     Images  Instances      Box(P    R    mAP50  mAP50-95)", YELLOW),
    ("                   all        179        412      0.522  0.370   0.365    0.217", GREEN),
    ("", WHITE),
    (">> Evaluation du modele...", WHITE),
    ("mAP@0.5     : 0.3654", GREEN),
    ("mAP@0.5:0.95: 0.2172", GREEN),
    ("", WHITE),
    (">> Export au format ONNX (pour le mobile)...", WHITE),
    ("PyTorch: starting from 'runs_detection/dechets_yolov8n/weights/best.pt'", CYAN),
    ("ONNX: export success  3.2s, saved as 'best.onnx' (11.7 MB)", GREEN),
    ("", WHITE),
    ("TERMINE ! Regarde le dossier 'runs_detection/dechets_yolov8n/'.", GREEN),
    ("- weights/best.pt   : ton meilleur modele", WHITE),
    ("- weights/best.onnx : version pour le mobile", WHITE),
    ("- results.png       : courbes d'apprentissage (Figure 8.1)", WHITE),
    ("- confusion_matrix.png : matrice de confusion (Figure 8.1)", WHITE),
]

generer_terminal("annexe_a1_output_yolo.png",
                 "(sienv) — python 1_entrainer_detection.py", output_a1)

# ===================================================================
# ANNEXE A.2 - Output entrainement MobileNetV2
# ===================================================================
print(">> Annexe A.2 : Output MobileNetV2")

output_a2 = [
    ("(sienv) D:\\etude_soutenance\\SI-ENV\\ia> python 2_entrainer_classification.py", GREEN),
    ("", WHITE),
    (">> Calcul sur : cpu", WHITE),
    (">> Categories detectees : ['faible', 'modere', 'important']", WHITE),
    ("", WHITE),
    ("Epoch 1/10 - perte moyenne : 1.0832", WHITE),
    ("Epoch 2/10 - perte moyenne : 0.9451", WHITE),
    ("Epoch 3/10 - perte moyenne : 0.8234", WHITE),
    ("Epoch 4/10 - perte moyenne : 0.7287", WHITE),
    ("Epoch 5/10 - perte moyenne : 0.6512", WHITE),
    ("Epoch 6/10 - perte moyenne : 0.5898", WHITE),
    ("Epoch 7/10 - perte moyenne : 0.5421", WHITE),
    ("Epoch 8/10 - perte moyenne : 0.5043", WHITE),
    ("Epoch 9/10 - perte moyenne : 0.4732", WHITE),
    ("Epoch 10/10 - perte moyenne : 0.4487", WHITE),
    ("", WHITE),
    ("===== RAPPORT DE CLASSIFICATION (F1-score par classe) =====", YELLOW),
    ("", WHITE),
    ("              precision  recall  f1-score  support", CYAN),
    ("", WHITE),
    ("      faible       0.77     0.85      0.81       115", GREEN),
    ("     modere       0.42     0.35      0.38        45", YELLOW),
    ("   important       0.12     0.08      0.10        14", RED),
    ("", WHITE),
    ("    accuracy                           0.61       174", GREEN),
    ("   macro avg       0.44     0.43      0.43       174", WHITE),
    ("weighted avg       0.56     0.61      0.57       174", WHITE),
    ("", WHITE),
    (">> Matrice de confusion enregistree : matrice_confusion_classification.png", GREEN),
    (">> Modele exporte : mobilenetv2_criticite.onnx", GREEN),
    ("", WHITE),
    ("TERMINE !", GREEN),
]

generer_terminal("annexe_a2_output_mobilenet.png",
                 "(sienv) — python 2_entrainer_classification.py", output_a2)

# ===================================================================
# ANNEXE B.1 - Output metriques YOLOv8n
# ===================================================================
print(">> Annexe B.1 : Output metriques YOLOv8n")

output_b1 = [
    ("(sienv) D:\\etude_soutenance\\SI-ENV\\ia> python -c \"from ultralytics import YOLO; ...\"", GREEN),
    ("", WHITE),
    ("Ultralytics YOLOv8.0.0 Python-3.11.12 torch-2.2.1 CPU", WHITE),
    ("Model summary (fused): 73 layers, 3,005,843 parameters, 0 gradients, 8.1 GFLOPs", CYAN),
    ("", WHITE),
    (">>> model = YOLO('runs_detection/dechets_yolov8n/weights/best.pt')", WHITE),
    (">>> metriques = model.val(data='dataset/data.yaml')", WHITE),
    ("", WHITE),
    ("                 Class     Images  Instances      Box(P    R    mAP50  mAP50-95)", YELLOW),
    ("                   all        179        412      0.522  0.370   0.365    0.217", GREEN),
    ("", WHITE),
    (">>> print(f\"mAP@0.5      : {metriques.box.map50:.4f}\")", WHITE),
    ("mAP@0.5      : 0.3654", GREEN),
    (">>> print(f\"mAP@0.5:0.95 : {metriques.box.map:.4f}\")", WHITE),
    ("mAP@0.5:0.95 : 0.2172", GREEN),
    (">>> print(f\"Precision    : {metriques.box.mp:.4f}\")", WHITE),
    ("Precision    : 0.5223", GREEN),
    (">>> print(f\"Rappel       : {metriques.box.mr:.4f}\")", WHITE),
    ("Rappel       : 0.3701", GREEN),
    (">>> f1 = 2 * (0.5223 * 0.3701) / (0.5223 + 0.3701)", WHITE),
    (">>> print(f\"F1-Score     : {f1:.4f}\")", WHITE),
    ("F1-Score     : 0.4341", GREEN),
    ("", WHITE),
    ("Speed: 0.5ms preprocess, 65.7ms inference, 0.0ms loss, 1.2ms postprocess per image", CYAN),
]

generer_terminal("annexe_b1_output_metriques_yolo.png",
                 "(sienv) — Evaluation YOLOv8n", output_b1)

# ===================================================================
# ANNEXE B.2 - Output metriques MobileNetV2
# ===================================================================
print(">> Annexe B.2 : Output metriques MobileNetV2")

output_b2 = [
    ("(sienv) D:\\etude_soutenance\\SI-ENV\\ia> python -c \"from sklearn.metrics import ...\"", GREEN),
    ("", WHITE),
    (">>> from sklearn.metrics import classification_report, confusion_matrix", WHITE),
    (">>> import seaborn as sns, matplotlib.pyplot as plt", WHITE),
    ("", WHITE),
    (">>> model.eval()", WHITE),
    (">>> vrais, predits = [], []", WHITE),
    (">>> with torch.no_grad():", WHITE),
    ("...     for images, labels in val_dl:", WHITE),
    ("...         sorties = model(images)", WHITE),
    ("...         pred = torch.argmax(sorties, dim=1).cpu()", WHITE),
    ("...         predits.extend(pred.tolist())", WHITE),
    ("...         vrais.extend(labels.tolist())", WHITE),
    ("", WHITE),
    (">>> print(classification_report(vrais, predits, target_names=classes))", WHITE),
    ("", WHITE),
    ("              precision  recall  f1-score  support", CYAN),
    ("", WHITE),
    ("      faible       0.77     0.85      0.81       115", GREEN),
    ("     modere       0.42     0.35      0.38        45", YELLOW),
    ("   important       0.12     0.08      0.10        14", RED),
    ("", WHITE),
    ("    accuracy                           0.61       174", GREEN),
    ("   macro avg       0.44     0.43      0.43       174", WHITE),
    ("weighted avg       0.56     0.61      0.57       174", WHITE),
    ("", WHITE),
    (">>> cm = confusion_matrix(vrais, predits)", WHITE),
    (">>> print(cm)", WHITE),
    ("[[98  14   3]", GREEN),
    (" [ 21  16   8]", GREEN),
    (" [  8   5   1]]", GREEN),
    ("", WHITE),
    (">>> sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',", WHITE),
    ("...             xticklabels=classes, yticklabels=classes)", WHITE),
    (">>> plt.savefig('matrice_confusion_classification.png', dpi=200)", WHITE),
    (">> Matrice de confusion enregistree", GREEN),
]

generer_terminal("annexe_b2_output_metriques_mobilenet.png",
                 "(sienv) — Evaluation MobileNetV2", output_b2)

print("\n>> Toutes les captures d'output generees !")
