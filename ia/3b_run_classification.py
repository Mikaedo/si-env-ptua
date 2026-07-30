"""
3b_run_classification.py
Wrapper pour lancer la classification avec logging dans un fichier.
"""
import sys
import traceback

log_file = open("classification_output.txt", "w", encoding="utf-8")

def log(msg):
    print(msg)
    log_file.write(str(msg) + "\n")
    log_file.flush()

try:
    log(">> Debut du script de classification...")

    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader
    from torchvision import datasets, transforms, models
    from sklearn.metrics import classification_report, confusion_matrix
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    DOSSIER = "dataset_criticite"
    NB_EPOCHS = 10
    BATCH = 8
    LR = 0.0001

    device = "cuda" if torch.cuda.is_available() else "cpu"
    log(f">> Calcul sur : {device}")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    train_ds = datasets.ImageFolder(f"{DOSSIER}/train", transform=transform)
    val_ds = datasets.ImageFolder(f"{DOSSIER}/val", transform=transform)
    classes = train_ds.classes
    log(f">> Categories detectees : {classes}")
    log(f">> Train: {len(train_ds)} images, Val: {len(val_ds)} images")

    train_dl = DataLoader(train_ds, batch_size=BATCH, shuffle=True, num_workers=0)
    val_dl = DataLoader(val_ds, batch_size=BATCH, num_workers=0)

    log(">> Chargement de MobileNetV2 pre-entraine...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    model.classifier[1] = nn.Linear(model.last_channel, len(classes))
    model = model.to(device)

    critere = nn.CrossEntropyLoss()
    optim = torch.optim.Adam(model.parameters(), lr=LR)

    log(">> Debut de la boucle d'entrainement...")
    for epoch in range(NB_EPOCHS):
        model.train()
        perte_totale = 0
        n_batches = 0
        for i, (images, labels) in enumerate(train_dl):
            try:
                images, labels = images.to(device), labels.to(device)
                optim.zero_grad()
                sorties = model(images)
                perte = critere(sorties, labels)
                perte.backward()
                optim.step()
                perte_totale += perte.item()
                n_batches += 1
                if (i+1) % 10 == 0:
                    log(f"  Epoch {epoch+1} - batch {i+1}/{len(train_dl)} - perte: {perte.item():.4f}")
            except Exception as e:
                log(f"  ERREUR batch {i+1}: {e}")
                continue
        log(f"Epoch {epoch+1}/{NB_EPOCHS} - perte moyenne : {perte_totale/max(n_batches,1):.4f}")

    log(">> Entrainement termine. Evaluation...")

    model.eval()
    vrais, predits = [], []
    with torch.no_grad():
        for images, labels in val_dl:
            images = images.to(device)
            sorties = model(images)
            pred = torch.argmax(sorties, dim=1).cpu()
            predits.extend(pred.tolist())
            vrais.extend(labels.tolist())

    log("\n===== RAPPORT DE CLASSIFICATION (F1-score par classe) =====")
    report = classification_report(vrais, predits, target_names=classes)
    log(report)

    cm = confusion_matrix(vrais, predits)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=classes, yticklabels=classes)
    plt.xlabel("Predit")
    plt.ylabel("Reel")
    plt.title("Matrice de confusion - Criticite")
    plt.tight_layout()
    plt.savefig("matrice_confusion_classification.png", dpi=150)
    log(">> Matrice de confusion enregistree : matrice_confusion_classification.png")

    # Courbes d'apprentissage
    plt.figure(figsize=(8, 5))
    plt.plot(range(1, NB_EPOCHS+1), [0], marker='o')
    plt.xlabel("Epoch")
    plt.ylabel("Perte")
    plt.title("Courbe d'apprentissage - MobileNetV2")
    plt.savefig("courbe_apprentissage_classification.png", dpi=150)
    log(">> Courbe d'apprentissage enregistree")

    # Export ONNX
    exemple = torch.randn(1, 3, 224, 224).to(device)
    torch.onnx.export(model, exemple, "mobilenetv2_criticite.onnx",
                      input_names=["image"], output_names=["criticite"])
    log(">> Modele exporte : mobilenetv2_criticite.onnx")
    log("\nTERMINE !")

except Exception as e:
    log(f"ERREUR : {e}")
    log(traceback.format_exc())

log_file.close()
