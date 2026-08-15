# -*- coding: utf-8 -*-
"""
evaluer_criticite.py
====================
Evaluation rigoureuse du module de criticite, sans reentrainement.

Ce script ne cree aucun modele : il fait tourner les deux reseaux DEJA
entraines (exportes en ONNX et embarques dans l'application mobile) sur le
jeu de validation, et produit ce qui manquait au memoire :

  1. les metriques reelles par classe, recalculees a partir des sorties du
     modele et non recopiees ;
  2. un BASELINE : la criticite deduite du simple comptage des detections de
     YOLOv8, a comparer au reseau de classification. C'est le comparateur
     naturel puisque l'etiquette de criticite est, par construction, une
     fonction du nombre d'objets annotes (regle de 3_preparer_criticite.py :
     1-2 objets = faible, 3-5 = modere, 6+ = important) ;
  3. une OPTION DE REJET : en dessous d'un seuil de confiance, le modele
     s'abstient et laisse l'agent trancher. On mesure alors le taux de
     couverture et la justesse sur les cas couverts, ce qui decrit un systeme
     utilisable plutot qu'un score moyen ;
  4. des INTERVALLES DE CONFIANCE par bootstrap, le jeu de validation ne
     comptant que 179 images ;
  5. une VARIANTE BINAIRE (faible / elevee), qui correspond a la seule
     decision utile a l'agent : intervenir ou non.

Sorties : figures PNG + fichier JSON des metriques dans le scratchpad.
"""
import json
import os
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

RACINE = Path(__file__).resolve().parent
VAL = RACINE / "dataset_criticite" / "val"
MODELE_CLS = RACINE.parent / "mobile" / "assets" / "models" / "classification_mobilenetv2.onnx"
MODELE_DET = RACINE.parent / "mobile" / "assets" / "models" / "detection_yolov8n.onnx"
SORTIE = Path(r"C:\Users\DELL\AppData\Local\Temp\claude"
              r"\d--etude-soutenance-SI-ENV\3233866b-194c-446a-b8f6-65c65b911c25"
              r"\scratchpad")

# torchvision.datasets.ImageFolder ordonne les classes alphabetiquement :
# c'est cet ordre qui a servi a l'entrainement, il faut le respecter ici.
CLASSES = ["faible", "important", "modere"]
LIBELLE = {"faible": "Faible", "modere": "Modérée", "important": "Importante"}

MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# Regle d'etiquetage d'origine, reprise telle quelle pour le baseline.
def criticite_depuis_compte(n):
    if n <= 2:
        return "faible"
    if n <= 5:
        return "modere"
    return "important"


def preparer_classification(chemin):
    img = Image.open(chemin).convert("RGB").resize((224, 224), Image.BILINEAR)
    x = np.asarray(img, dtype=np.float32) / 255.0
    x = (x - MEAN) / STD
    return x.transpose(2, 0, 1)[None, :, :, :].astype(np.float32)


def preparer_detection(chemin, taille=320):
    img = Image.open(chemin).convert("RGB").resize((taille, taille), Image.BILINEAR)
    x = np.asarray(img, dtype=np.float32) / 255.0
    return x.transpose(2, 0, 1)[None, :, :, :].astype(np.float32)


def softmax(v):
    e = np.exp(v - v.max())
    return e / e.sum()


def iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    aire_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    aire_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = aire_a + aire_b - inter
    return inter / union if union > 0 else 0.0


def compter_detections(sortie, seuil_conf=0.25, seuil_iou=0.45):
    """Decode la sortie YOLOv8 [1, 4+nc, A] et renvoie le nombre d'objets
    retenus apres suppression des doublons (NMS)."""
    p = sortie[0]                     # (4+nc, A)
    boites = p[:4].T                  # (A, 4) : cx, cy, w, h
    scores = p[4:].T                  # (A, nc)
    conf = scores.max(axis=1)
    garde = conf >= seuil_conf
    boites, conf = boites[garde], conf[garde]
    if len(boites) == 0:
        return 0
    xy = np.stack([boites[:, 0] - boites[:, 2] / 2, boites[:, 1] - boites[:, 3] / 2,
                   boites[:, 0] + boites[:, 2] / 2, boites[:, 1] + boites[:, 3] / 2], axis=1)
    ordre = conf.argsort()[::-1]
    retenues = []
    while len(ordre):
        i = ordre[0]
        retenues.append(i)
        if len(ordre) == 1:
            break
        reste = ordre[1:]
        ious = np.array([iou(xy[i], xy[j]) for j in reste])
        ordre = reste[ious < seuil_iou]
    return len(retenues)


def matrice_confusion(vrais, predits, classes):
    idx = {c: i for i, c in enumerate(classes)}
    m = np.zeros((len(classes), len(classes)), dtype=int)
    for v, p in zip(vrais, predits):
        m[idx[v], idx[p]] += 1
    return m


def metriques(vrais, predits, classes):
    m = matrice_confusion(vrais, predits, classes)
    res = {}
    for i, c in enumerate(classes):
        vp = m[i, i]
        fp = m[:, i].sum() - vp
        fn = m[i, :].sum() - vp
        p = vp / (vp + fp) if vp + fp else 0.0
        r = vp / (vp + fn) if vp + fn else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        res[c] = {"precision": p, "rappel": r, "f1": f1, "effectif": int(m[i, :].sum())}
    total = m.sum()
    justesse = np.trace(m) / total if total else 0.0
    f1_pond = sum(res[c]["f1"] * res[c]["effectif"] for c in classes) / total if total else 0.0
    return {"par_classe": res, "justesse": justesse, "f1_pondere": f1_pond,
            "matrice": m.tolist(), "n": int(total)}


def bootstrap_ic(vrais, predits, classes, n_tirages=2000, graine=42):
    """Intervalle de confiance a 95 % par bootstrap sur le jeu de validation."""
    rng = np.random.default_rng(graine)
    n = len(vrais)
    just, f1p = [], []
    v = np.array(vrais)
    p = np.array(predits)
    for _ in range(n_tirages):
        k = rng.integers(0, n, n)
        r = metriques(list(v[k]), list(p[k]), classes)
        just.append(r["justesse"])
        f1p.append(r["f1_pondere"])
    q = lambda a: (float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5)))
    return {"justesse_ic95": q(just), "f1_pondere_ic95": q(f1p)}


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    images = []
    for c in CLASSES:
        for f in sorted((VAL / c).glob("*")):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
                images.append((f, c))
    print(f"Jeu de validation : {len(images)} images")
    for c in CLASSES:
        print(f"   {c:11s} : {sum(1 for _, y in images if y == c)}")

    sess_cls = ort.InferenceSession(str(MODELE_CLS), providers=["CPUExecutionProvider"])
    nom_cls = sess_cls.get_inputs()[0].name
    sess_det = ort.InferenceSession(str(MODELE_DET), providers=["CPUExecutionProvider"])
    nom_det = sess_det.get_inputs()[0].name

    vrais, predits, confiances, predits_baseline, nb_objets = [], [], [], [], []
    t_cls, t_det = [], []

    for chemin, vrai in images:
        x = preparer_classification(chemin)
        t0 = time.perf_counter()
        sortie = sess_cls.run(None, {nom_cls: x})[0][0]
        t_cls.append((time.perf_counter() - t0) * 1000)
        prob = softmax(sortie)
        vrais.append(vrai)
        predits.append(CLASSES[int(prob.argmax())])
        confiances.append(float(prob.max()))

        xd = preparer_detection(chemin)
        t0 = time.perf_counter()
        sd = sess_det.run(None, {nom_det: xd})[0]
        t_det.append((time.perf_counter() - t0) * 1000)
        n = compter_detections(sd)
        nb_objets.append(n)
        predits_baseline.append(criticite_depuis_compte(n))

    # ---------- 3 classes ----------
    m_cls = metriques(vrais, predits, CLASSES)
    m_base = metriques(vrais, predits_baseline, CLASSES)
    # baseline trivial : toujours la classe majoritaire
    majoritaire = max(CLASSES, key=lambda c: sum(1 for v in vrais if v == c))
    m_maj = metriques(vrais, [majoritaire] * len(vrais), CLASSES)

    # ---------- variante binaire ----------
    binaire = lambda y: "faible" if y == "faible" else "elevee"
    CL_BIN = ["faible", "elevee"]
    m_bin = metriques([binaire(v) for v in vrais], [binaire(p) for p in predits], CL_BIN)
    m_bin_base = metriques([binaire(v) for v in vrais],
                           [binaire(p) for p in predits_baseline], CL_BIN)

    # ---------- option de rejet ----------
    rejet = []
    conf = np.array(confiances)
    for tau in np.arange(0.34, 0.99, 0.02):
        garde = conf >= tau
        couverture = float(garde.mean())
        if garde.sum() == 0:
            rejet.append({"tau": float(tau), "couverture": 0.0, "justesse": None})
            continue
        v = [vrais[i] for i in range(len(vrais)) if garde[i]]
        p = [predits[i] for i in range(len(vrais)) if garde[i]]
        rejet.append({"tau": float(tau), "couverture": couverture,
                      "justesse": float(np.mean([a == b for a, b in zip(v, p)]))})

    ic = bootstrap_ic(vrais, predits, CLASSES)
    ic_bin = bootstrap_ic([binaire(v) for v in vrais], [binaire(p) for p in predits], CL_BIN)

    resultats = {
        "n_images": len(images),
        "classification_3_classes": m_cls,
        "baseline_comptage_detections": m_base,
        "baseline_classe_majoritaire": {"classe": majoritaire, **m_maj},
        "binaire_2_classes": m_bin,
        "binaire_baseline_comptage": m_bin_base,
        "option_de_rejet": rejet,
        "intervalles_confiance_3_classes": ic,
        "intervalles_confiance_binaire": ic_bin,
        "latence_ms": {
            "classification_mediane": float(np.median(t_cls)),
            "classification_p95": float(np.percentile(t_cls, 95)),
            "detection_mediane": float(np.median(t_det)),
            "detection_p95": float(np.percentile(t_det, 95)),
        },
        "nb_objets_detectes": {"moyenne": float(np.mean(nb_objets)),
                               "median": float(np.median(nb_objets))},
    }
    chemin_json = SORTIE / "metriques_criticite.json"
    chemin_json.write_text(json.dumps(resultats, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---------- affichage ----------
    print("\n--- Classification MobileNetV2, 3 classes ---")
    for c in CLASSES:
        r = m_cls["par_classe"][c]
        print(f"   {LIBELLE[c]:11s} P={r['precision']:.3f} R={r['rappel']:.3f} "
              f"F1={r['f1']:.3f} (n={r['effectif']})")
    print(f"   justesse {m_cls['justesse']:.3f}  IC95 {ic['justesse_ic95'][0]:.3f}-{ic['justesse_ic95'][1]:.3f}")
    print(f"   F1 pondere {m_cls['f1_pondere']:.3f}")

    print("\n--- Baselines, 3 classes ---")
    print(f"   comptage des detections : justesse {m_base['justesse']:.3f}, F1 pondere {m_base['f1_pondere']:.3f}")
    print(f"   classe majoritaire ({majoritaire}) : justesse {m_maj['justesse']:.3f}")

    print("\n--- Variante binaire (intervenir ou non) ---")
    for c in CL_BIN:
        r = m_bin["par_classe"][c]
        print(f"   {c:8s} P={r['precision']:.3f} R={r['rappel']:.3f} F1={r['f1']:.3f} (n={r['effectif']})")
    print(f"   justesse {m_bin['justesse']:.3f}  IC95 "
          f"{ic_bin['justesse_ic95'][0]:.3f}-{ic_bin['justesse_ic95'][1]:.3f}")
    print(f"   baseline comptage, binaire : justesse {m_bin_base['justesse']:.3f}")

    print("\n--- Latence mesuree sur ce processeur ---")
    l = resultats["latence_ms"]
    print(f"   classification : mediane {l['classification_mediane']:.1f} ms, p95 {l['classification_p95']:.1f} ms")
    print(f"   detection      : mediane {l['detection_mediane']:.1f} ms, p95 {l['detection_p95']:.1f} ms")

    print(f"\nMetriques ecrites dans {chemin_json}")
    return resultats


if __name__ == "__main__":
    main()
