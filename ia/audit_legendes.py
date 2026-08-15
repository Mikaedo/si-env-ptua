# -*- coding: utf-8 -*-
"""Verifie que chaque legende de tableau precede immediatement son tableau,
et que chaque legende de figure suit immediatement son image."""
import re, sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

d = Document(r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_FINAL.docx")
NSB = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NSI = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"

corps = []
for e in d.element.body.iterchildren():
    if e.tag == NSB + "p":
        corps.append(("p", Paragraph(e, d)))
    elif e.tag == NSB + "tbl":
        corps.append(("t", Table(e, d)))

DEBUT_CORPS = next(i for i, (g, e) in enumerate(corps)
                   if g == "p" and e.text.strip() == "Introduction generale"
                   or (g == "p" and e.text.strip().startswith("Introduction g")))

print("=== legendes de tableaux non suivies de leur tableau ===")
souci = 0
for i, (g, el) in enumerate(corps):
    if g != "p" or i < DEBUT_CORPS:
        continue
    m = re.match(r"Tableau (\d+\.\d+)\s*:", el.text.strip())
    if not m:
        continue
    # Le tableau doit suivre, en tolerant un paragraphe vide
    j, ok = i + 1, False
    while j < len(corps) and j <= i + 2:
        if corps[j][0] == "t":
            ok = True
            break
        if corps[j][0] == "p" and corps[j][1].text.strip():
            break
        j += 1
    if not ok:
        souci += 1
        suivant = corps[i+1][1].text.strip()[:52] if corps[i+1][0] == "p" else "TABLEAU"
        print(f"  Tableau {m.group(1)} : suivi de {suivant!r}")
if not souci:
    print("  aucun")

print("\n=== legendes de figures non precedees d'une image ===")
souci2 = 0
for i, (g, el) in enumerate(corps):
    if g != "p" or i < DEBUT_CORPS:
        continue
    m = re.match(r"Figure ([\d.]+(?: bis)?)\s*:", el.text.strip())
    if not m:
        continue
    j, ok = i - 1, False
    while j >= 0 and j >= i - 2:
        if corps[j][0] == "p" and corps[j][1]._element.findall(".//" + NSI):
            ok = True
            break
        if corps[j][0] == "p" and corps[j][1].text.strip():
            break
        j -= 1
    if not ok:
        souci2 += 1
        print(f"  Figure {m.group(1)} : pas d'image juste au-dessus")
if not souci2:
    print("  aucune")
