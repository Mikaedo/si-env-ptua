# -*- coding: utf-8 -*-
"""Audit du corps seul : adjacence legende/objet, numerotation, renvois."""
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

# Le corps commence a l'introduction generale : avant, ce sont les listes.
debut = 0
for i, (g, el) in enumerate(corps):
    if g == "p" and el.style.name.startswith("Heading 1") \
       and el.text.strip().lower().startswith("introduction g"):
        debut = i
        break
print(f"corps a partir de l'element {debut} sur {len(corps)}\n")

pb = []
for i in range(debut, len(corps)):
    g, el = corps[i]
    if g != "p":
        continue
    t = el.text.strip()

    m = re.match(r"Tableau ([\dA-Z]+\.\d+)\s*:", t)
    if m:
        ok = False
        for j in range(i + 1, min(i + 3, len(corps))):
            if corps[j][0] == "t":
                ok = True; break
            if corps[j][0] == "p" and corps[j][1].text.strip():
                break
        if not ok:
            pb.append(f"Tableau {m.group(1)} : aucun tableau juste apres la legende")

    m = re.match(r"Figure ([\d.]+(?: bis)?)\s*:", t)
    if m:
        ok = False
        for j in range(i - 1, max(debut - 1, i - 3), -1):
            if corps[j][0] == "p" and corps[j][1]._element.findall(".//" + NSI):
                ok = True; break
            if corps[j][0] == "p" and corps[j][1].text.strip():
                break
        if not ok:
            pb.append(f"Figure {m.group(1)} : aucune image juste avant la legende")

print("=== adjacence legende / objet ===")
print("\n".join("  " + x for x in pb) if pb else "  tout est correct")

# Ordre des numeros dans le corps
print("\n=== ordre des numeros ===")
for genre, motif in (("Tableau", r"Tableau (\d+\.\d+)\s*:"), ("Figure", r"Figure ([\d.]+)\s*:")):
    vus = []
    for i in range(debut, len(corps)):
        g, el = corps[i]
        if g != "p": continue
        m = re.match(motif, el.text.strip())
        if m: vus.append(m.group(1))
    desordre = [(a, b) for a, b in zip(vus, vus[1:])
                if tuple(map(int, a.split('.'))) > tuple(map(int, b.split('.')))]
    print(f"  {genre}s : {' '.join(vus[:16])}")
    print(f"    desordre : {desordre if desordre else 'aucun'}")
