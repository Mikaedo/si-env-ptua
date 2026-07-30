"""
generer_captures_code.py
========================
Genere des images PNG de captures de code (style editeur sombre)
pour les Annexes A et B, puis les insere dans le memoire.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

DOSSIER_SORTIE = r"D:\etude_soutenance\SI-ENV\ia\captures_annexes"
os.makedirs(DOSSIER_SORTIE, exist_ok=True)

# Style editeur sombre
BG_COLOR = '#1e1e1e'
TEXT_COLOR = '#d4d4d4'
COMMENT_COLOR = '#6a9955'
KEYWORD_COLOR = '#569cd6'
STRING_COLOR = '#ce9178'
FUNC_COLOR = '#dcdcaa'
PARAM_COLOR = '#9cdcfe'
TITLE_COLOR = '#4ec9b0'

def generer_capture(filename, title, lines, max_lines_per_page=35):
    """Genere une image PNG d'une capture de code style VS Code."""
    
    # Couper en pages si trop de lignes
    pages = []
    if len(lines) > max_lines_per_page:
        for i in range(0, len(lines), max_lines_per_page):
            pages.append(lines[i:i+max_lines_per_page])
    else:
        pages.append(lines)
    
    generated_files = []
    
    for page_num, page_lines in enumerate(pages):
        n_lines = len(page_lines)
        fig_height = max(4, n_lines * 0.28 + 1.2)
        fig_width = 12
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)
        ax.axis('off')
        
        # Barre de titre (style onglet VS Code)
        title_bar = FancyBboxPatch((0.02, 0.93), 0.96, 0.06,
                                   boxstyle="round,pad=0.01",
                                   facecolor='#2d2d2d', edgecolor='#3c3c3c',
                                   transform=ax.transAxes)
        ax.add_patch(title_bar)
        ax.text(0.05, 0.96, title, color='#cccccc', fontsize=9,
                fontfamily='monospace', va='center', transform=ax.transAxes)
        
        # Numero de page si plusieurs pages
        if len(pages) > 1:
            ax.text(0.95, 0.96, f'({page_num+1}/{len(pages)})', color='#888888',
                    fontsize=8, fontfamily='monospace', va='center', ha='right',
                    transform=ax.transAxes)
        
        # Afficher les lignes de code
        y_start = 0.88
        y_step = 0.85 / max(n_lines, 1)
        
        for i, line in enumerate(page_lines):
            y = y_start - i * y_step
            
            # Determiner la couleur selon le type de ligne
            color = TEXT_COLOR
            stripped = line.lstrip()
            
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                color = COMMENT_COLOR
            elif any(kw in stripped for kw in ['import ', 'from ', 'def ', 'class ', 'for ', 'if ', 'with ', 'return ', 'print(']):
                # Mot-cle en bleu, reste en blanc
                ax.text(0.05, y, line, color=TEXT_COLOR, fontsize=8.5,
                        fontfamily='monospace', va='center', transform=ax.axes.transAxes)
                # Surligner les mots-cles
                for kw in ['import', 'from', 'def', 'class', 'for', 'if', 'with', 'return', 'print']:
                    if kw in line:
                        idx = line.find(kw)
                        ax.text(0.05 + idx * 0.0052, y, kw, color=KEYWORD_COLOR, fontsize=8.5,
                                fontfamily='monospace', va='center', transform=ax.transAxes)
                generated_files.append(None)  # placeholder
                break
            elif stripped.startswith("'") or stripped.startswith('"'):
                color = STRING_COLOR
            elif stripped.startswith('model.') or stripped.startswith('metriques.') or stripped.startswith('optim.'):
                color = FUNC_COLOR
            
            ax.text(0.05, y, line, color=color, fontsize=8.5,
                    fontfamily='monospace', va='center', transform=ax.transAxes)
        
        # Numero de ligne (style editeur)
        for i in range(n_lines):
            y = y_start - i * y_step
            ax.text(0.01, y, str(i + 1 + page_num * max_lines_per_page), 
                    color='#858585', fontsize=7.5,
                    fontfamily='monospace', va='center', ha='right',
                    transform=ax.transAxes)
        
        plt.tight_layout()
        
        if len(pages) == 1:
            outpath = os.path.join(DOSSIER_SORTIE, filename)
        else:
            base, ext = os.path.splitext(filename)
            outpath = os.path.join(DOSSIER_SORTIE, f"{base}_p{page_num+1}{ext}")
        
        plt.savefig(outpath, dpi=200, bbox_inches='tight',
                    facecolor=BG_COLOR, edgecolor='none')
        plt.close()
        generated_files.append(outpath)
        print(f"  Genere: {outpath}")
    
    return [f for f in generated_files if f is not None]


# ===================================================================
# ANNEXE A - Code 1: Entrainement YOLOv8n (detection)
# ===================================================================
print(">> Annexe A.1 : Entrainement YOLOv8n")

code_a1 = [
    "from ultralytics import YOLO",
    "",
    "# --- Parametres (Tableau 8.4 du memoire) ---",
    "CHEMIN_DATA_YAML = \"dataset/data.yaml\"",
    "NB_EPOCHS = 10",
    "TAILLE_IMAGE = 320",
    "BATCH = 8",
    "",
    "# 1) Chargement du modele pre-entraine YOLOv8n (transfer learning)",
    "model = YOLO(\"yolov8n.pt\")",
    "",
    "# 2) Entrainement sur le dataset TACO",
    "resultats = model.train(",
    "    data=CHEMIN_DATA_YAML,",
    "    epochs=NB_EPOCHS,",
    "    imgsz=TAILLE_IMAGE,",
    "    batch=BATCH,",
    "    project=\"runs_detection\",",
    "    name=\"dechets_yolov8n\",",
    ")",
    "",
    "# 3) Evaluation -> metriques du Tableau 8.2",
    "metriques = model.val()",
    "print(\"mAP@0.5     :\", metriques.box.map50)",
    "print(\"mAP@0.5:0.95:\", metriques.box.map)",
    "",
    "# 4) Export ONNX pour le mobile (chapitre 8.6)",
    "model.export(format=\"onnx\")",
]

files_a1 = generer_capture("annexe_a1_yolov8n.png", "1_entrainer_detection.py", code_a1)

# ===================================================================
# ANNEXE A - Code 2: Entrainement MobileNetV2 (classification)
# ===================================================================
print(">> Annexe A.2 : Entrainement MobileNetV2")

code_a2 = [
    "import torch",
    "import torch.nn as nn",
    "from torch.utils.data import DataLoader",
    "from torchvision import datasets, transforms, models",
    "from sklearn.metrics import classification_report, confusion_matrix",
    "import matplotlib.pyplot as plt",
    "import seaborn as sns",
    "",
    "# --- Parametres ---",
    "DOSSIER = \"dataset_criticite\"",
    "NB_EPOCHS = 10",
    "BATCH = 16",
    "LR = 0.0001",
    "",
    "device = \"cuda\" if torch.cuda.is_available() else \"cpu\"",
    "",
    "# 1) Preparation des images (redimensionnement + normalisation)",
    "transform = transforms.Compose([",
    "    transforms.Resize((224, 224)),",
    "    transforms.ToTensor(),",
    "    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),",
    "])",
    "",
    "train_ds = datasets.ImageFolder(f\"{DOSSIER}/train\", transform=transform)",
    "val_ds = datasets.ImageFolder(f\"{DOSSIER}/val\", transform=transform)",
    "classes = train_ds.classes",
    "",
    "# 2) MobileNetV2 pre-entraine + remplacement derniere couche",
    "model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)",
    "model.classifier[1] = nn.Linear(model.last_channel, len(classes))",
    "model = model.to(device)",
    "",
    "critere = nn.CrossEntropyLoss()",
    "optim = torch.optim.Adam(model.parameters(), lr=LR)",
    "",
    "# 3) Boucle d'entrainement",
    "for epoch in range(NB_EPOCHS):",
    "    model.train()",
    "    for images, labels in train_dl:",
    "        images, labels = images.to(device), labels.to(device)",
    "        optim.zero_grad()",
    "        sorties = model(images)",
    "        perte = critere(sorties, labels)",
    "        perte.backward()",
    "        optim.step()",
    "",
    "# 4) Export ONNX",
    "exemple = torch.randn(1, 3, 224, 224).to(device)",
    "torch.onnx.export(model, exemple, \"mobilenetv2_criticite.onnx\")",
]

files_a2 = generer_capture("annexe_a2_mobilenet.png", "2_entrainer_classification.py", code_a2)

# ===================================================================
# ANNEXE B - Code 1: Evaluation YOLOv8n (metriques de detection)
# ===================================================================
print(">> Annexe B.1 : Metriques YOLOv8n")

code_b1 = [
    "from ultralytics import YOLO",
    "",
    "# Charger le meilleur modele apres entrainement",
    "model = YOLO(\"runs_detection/dechets_yolov8n/weights/best.pt\")",
    "",
    "# Evaluation sur le set de validation",
    "metriques = model.val(data=\"dataset/data.yaml\")",
    "",
    "# --- Metriques calculees (Tableau 8.2) ---",
    "mAP_50      = metriques.box.map50    # 0.365",
    "mAP_50_95   = metriques.box.map       # 0.217",
    "precision   = metriques.box.mp        # 0.522",
    "rappel      = metriques.box.mr        # 0.370",
    "f1_score    = 2 * (precision * rappel) / (precision + rappel)  # 0.434",
    "",
    "print(f\"mAP@0.5      : {mAP_50:.4f}\")",
    "print(f\"mAP@0.5:0.95 : {mAP_50_95:.4f}\")",
    "print(f\"Precision    : {precision:.4f}\")",
    "print(f\"Rappel       : {rappel:.4f}\")",
    "print(f\"F1-Score     : {f1_score:.4f}\")",
]

files_b1 = generer_capture("annexe_b1_metriques_yolo.png", "Evaluation YOLOv8n - Metriques de detection", code_b1)

# ===================================================================
# ANNEXE B - Code 2: Evaluation MobileNetV2 (classification report)
# ===================================================================
print(">> Annexe B.2 : Metriques MobileNetV2")

code_b2 = [
    "from sklearn.metrics import classification_report, confusion_matrix",
    "import seaborn as sns",
    "import matplotlib.pyplot as plt",
    "",
    "# Predictions sur le set de validation",
    "model.eval()",
    "vrais, predits = [], []",
    "with torch.no_grad():",
    "    for images, labels in val_dl:",
    "        images = images.to(device)",
    "        sorties = model(images)",
    "        pred = torch.argmax(sorties, dim=1).cpu()",
    "        predits.extend(pred.tolist())",
    "        vrais.extend(labels.tolist())",
    "",
    "# --- Rapport de classification (Tableau 8.3) ---",
    "print(classification_report(vrais, predits, target_names=classes))",
    "",
    "#               precision  recall  f1-score  support",
    "#       faible       0.77     0.85      0.81       115",
    "#      modere       0.42     0.35      0.38        45",
    "#    important       0.12     0.08      0.10        14",
    "#    accuracy                           0.61       174",
    "#   macro avg       0.44     0.43      0.43       174",
    "# weighted avg       0.56     0.61      0.57       174",
    "",
    "# --- Matrice de confusion (Figure 8.4) ---",
    "cm = confusion_matrix(vrais, predits)",
    "sns.heatmap(cm, annot=True, fmt=\"d\", cmap=\"Blues\",",
    "            xticklabels=classes, yticklabels=classes)",
    "plt.xlabel(\"Predit\"); plt.ylabel(\"Reel\")",
    "plt.title(\"Matrice de confusion - Criticite\")",
    "plt.savefig(\"matrice_confusion_classification.png\", dpi=200)",
]

files_b2 = generer_capture("annexe_b2_metriques_mobilenet.png", "Evaluation MobileNetV2 - Metriques de classification", code_b2)

print("\n>> Toutes les captures generees dans :", DOSSIER_SORTIE)
print(">> Fichiers :")
all_files = files_a1 + files_a2 + files_b1 + files_b2
for f in all_files:
    print(f"   {f}")
