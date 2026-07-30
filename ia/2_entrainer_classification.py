"""
2_entrainer_classification.py  (PHASE 2 : CLASSIFICATION avec MobileNetV2)
=========================================================================

OBJECTIF (memoire, chapitre 8.4) :
Une fois qu'on a repere une zone de dechets (phase 1), on veut juger sa GRAVITE :
  - faible   (accumulation legere)
  - modere   (accumulation moyenne)
  - important(accumulation importante)
C'est de la CLASSIFICATION : ranger une image dans une categorie.

POURQUOI MobileNetV2 ?
C'est un reseau leger (14 Mo) concu pour les telephones. Parfait pour l'app terrain.

STRUCTURE DE DONNEES ATTENDUE (tres simple : un dossier par categorie) :
    dataset_criticite/
        train/
            faible/     *.jpg
            modere/     *.jpg
            important/  *.jpg
        val/
            faible/ ...
            modere/ ...
            important/ ...

LANCE-MOI AINSI :
    python 2_entrainer_classification.py
"""
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------------------------------------------------------
# PARAMETRES
# ------------------------------------------------------------------
DOSSIER = "dataset_criticite"
NB_EPOCHS = 10
BATCH = 16
LR = 0.0001   # "learning rate" : la vitesse d'apprentissage (petit = prudent)

# On utilise le GPU (carte graphique) s'il existe, sinon le CPU (plus lent mais ok)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(">> Calcul sur :", device)

# ------------------------------------------------------------------
# 1) PREPARATION DES IMAGES
#    On redimensionne en 224x224 (taille attendue par MobileNetV2) et on normalise.
# ------------------------------------------------------------------
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

train_ds = datasets.ImageFolder(f"{DOSSIER}/train", transform=transform)
val_ds = datasets.ImageFolder(f"{DOSSIER}/val", transform=transform)
classes = train_ds.classes
print(">> Categories detectees :", classes)

train_dl = DataLoader(train_ds, batch_size=BATCH, shuffle=True)
val_dl = DataLoader(val_ds, batch_size=BATCH)

# ------------------------------------------------------------------
# 2) LE MODELE : on prend MobileNetV2 pre-entraine et on remplace sa derniere couche
#    pour qu'il sorte NOTRE nombre de categories (3).
# ------------------------------------------------------------------
model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
model.classifier[1] = nn.Linear(model.last_channel, len(classes))
model = model.to(device)

# La "loss" mesure l'erreur ; l'"optimizer" corrige le modele pour reduire cette erreur.
critere = nn.CrossEntropyLoss()
optim = torch.optim.Adam(model.parameters(), lr=LR)

# ------------------------------------------------------------------
# 3) BOUCLE D'ENTRAINEMENT
# ------------------------------------------------------------------
for epoch in range(NB_EPOCHS):
    model.train()
    perte_totale = 0
    for images, labels in train_dl:
        images, labels = images.to(device), labels.to(device)
        optim.zero_grad()              # on remet les gradients a zero
        sorties = model(images)        # prediction
        perte = critere(sorties, labels)
        perte.backward()               # calcule comment corriger
        optim.step()                   # applique la correction
        perte_totale += perte.item()
    print(f"Epoch {epoch+1}/{NB_EPOCHS} - perte moyenne : {perte_totale/len(train_dl):.4f}")

# ------------------------------------------------------------------
# 4) EVALUATION : F1-score + matrice de confusion (Tableau 8.3 + Figure 8.1)
# ------------------------------------------------------------------
model.eval()
vrais, predits = [], []
with torch.no_grad():
    for images, labels in val_dl:
        images = images.to(device)
        sorties = model(images)
        pred = torch.argmax(sorties, dim=1).cpu()
        predits.extend(pred.tolist())
        vrais.extend(labels.tolist())

print("\n===== RAPPORT DE CLASSIFICATION (F1-score par classe) =====")
print(classification_report(vrais, predits, target_names=classes))

# Matrice de confusion visuelle
cm = confusion_matrix(vrais, predits)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=classes, yticklabels=classes)
plt.xlabel("Predit"); plt.ylabel("Reel"); plt.title("Matrice de confusion - Criticite")
plt.tight_layout()
plt.savefig("matrice_confusion_classification.png", dpi=150)
print(">> Matrice de confusion enregistree : matrice_confusion_classification.png")

# ------------------------------------------------------------------
# 5) EXPORT ONNX (pour le mobile, chapitre 8.6)
# ------------------------------------------------------------------
exemple = torch.randn(1, 3, 224, 224).to(device)
torch.onnx.export(model, exemple, "mobilenetv2_criticite.onnx",
                  input_names=["image"], output_names=["criticite"])
print(">> Modele exporte : mobilenetv2_criticite.onnx")
print("\nTERMINE !")
