# -*- coding: utf-8 -*-
"""Corrige deux incoherences de numerotation figures/tableaux detectees en
verifiant la conformite au guide UPB (format chapitre.ordre strictement
numerique, legende identique en liste et en corps) :
1) Tableau 6.5a / 6.5b -> renumerotes 6.4 / 6.5 (le format 'a/b' n'est pas
   conforme au format numerique impose par le guide ; ce renumerotage ne
   decale rien d'autre car le trou etait exactement d'un numero).
2) Figure 9.1 : la legende de la "Liste des figures" ne correspondait plus
   a la legende reelle dans le corps du chapitre 9 (donnees GEE reelles
   ajoutees depuis) -> synchronisee sur la legende du corps."""
from docx import Document

SRC = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_N'GUESSAN_v2.docx"
DST = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_N'GUESSAN_v3.docx"

doc = Document(SRC)
paras = doc.paragraphs

def fix_para(p, new_text):
    runs = p.runs
    assert runs, f"paragraphe sans run : {p.text!r}"
    runs[0].text = new_text
    for r in runs[1:]:
        r.text = ''

FIXES = {
    109: ("Figure 9.1 : Indices environnementaux calculés via Google Earth Engine (NO2, NDVI, NDWI, "
          "risque pluie/relief) pour les six chantiers PTUA — données réelles Sentinel-5P/Sentinel-2, "
          "capture du 31 juillet 2026."),
    121: "Tableau 6.4 : Identification des acteurs principaux.",
    122: "Tableau 6.5 : Identification des acteurs secondaires.",
    366: "Tableau 6.4 : Identification des acteurs principaux.",
    368: "Tableau 6.5 : Identification des acteurs secondaires.",
}

for idx, new_text in FIXES.items():
    old = paras[idx].text
    fix_para(paras[idx], new_text)
    assert paras[idx].text == new_text
    print(f"[OK] p{idx}: {old[:60]!r} -> {new_text[:60]!r}")

doc.save(DST)
print(f"\n=== SAUVEGARDE : {DST} ===")
