# -*- coding: utf-8 -*-
"""Etape 1/3 : ajoute les 3 citations bibliographiques presentes dans la
liste finale mais jamais utilisees dans le texte ([11] SSD, [18] YOLOv8
Docs Performance Metrics, [23] Roboflow Universe), a des endroits
pertinents et deja discutes dans le texte."""
from docx import Document

SRC = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_N'GUESSAN_v3.docx"
DST = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_N'GUESSAN_v4.docx"

doc = Document(SRC)
paras = doc.paragraphs

def fix_para(p, new_text):
    runs = p.runs
    assert runs, f"paragraphe sans run : {p.text!r}"
    runs[0].text = new_text
    for r in runs[1:]:
        r.text = ''

FIXES = {
    297: ("La vision par ordinateur permet d'analyser automatiquement des images. Pour la détection "
          "d'objets, les architectures à un seul passage comme YOLOv8 [7] et SSD [11] privilégient la "
          "rapidité (adaptées au mobile), tandis que Faster R-CNN [12], à deux étages, offre une "
          "meilleure précision mais reste trop lent. Pour la classification, MobileNetV2 [8] est "
          "optimisé pour les terminaux mobiles (3,4 M paramètres, 14 Mo), contre 25,6 M pour ResNet50 "
          "[9] et 138 M pour VGG16 [10]."),
    469: ("L'entraînement d'un réseau de neurones convolutifs exige un volume massif d'images annotées. "
          "N'ayant pas eu l'autorisation de photographier extensivement les chantiers du PTUA durant "
          "notre stage, nous nous sommes appuyés sur Recycle Trash, un jeu de données public de "
          "détection de déchets recyclables, disponible sur GitHub et Roboflow Universe [23]. Ce dataset "
          "comporte 2 462 images annotées au format YOLO, réparties en six catégories (métal, plastique, "
          "papier, carton, verre, organique), avec des contextes variés (extérieur, intérieur, surfaces "
          "mixtes) proches des conditions d'un chantier de construction."),
    474: ("Le Rappel (Recall) mérite une attention particulière : un faux négatif (déchets non détectés) "
          "a des conséquences pratiques directes sur la fiabilité du diagnostic automatique. Ce critère, "
          "au même titre que le mAP et les autres métriques retenues [18], justifie le choix du modèle "
          "retenu pour le SI-ENV."),
}

for idx, new_text in FIXES.items():
    old = paras[idx].text
    fix_para(paras[idx], new_text)
    assert paras[idx].text == new_text
    print(f"[OK] p{idx} corrige")

doc.save(DST)
print(f"\n=== SAUVEGARDE : {DST} ===")
