# -*- coding: utf-8 -*-
"""Audit de l'ordre reel du document : paragraphes et tableaux entremeles."""
import re, sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

d = Document(r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_FINAL.docx")
NSB = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NSI = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"

corps = []
for enfant in d.element.body.iterchildren():
    if enfant.tag == NSB + "p":
        p = Paragraph(enfant, d)
        corps.append(("p", p))
    elif enfant.tag == NSB + "tbl":
        corps.append(("t", Table(enfant, d)))

print(f"{len(corps)} elements dans le corps\n")
print("=== ordre autour des legendes de tableaux du chapitre 5 ===")
for i, (genre, el) in enumerate(corps):
    if genre != "p":
        continue
    t = el.text.strip()
    if re.match(r"Tableau 5\.[123] :", t):
        for j in range(max(0, i - 2), min(len(corps), i + 4)):
            g, e = corps[j]
            if g == "t":
                desc = f"[TABLEAU {len(e.rows)}x{len(e.columns)}] {e.rows[0].cells[0].text.strip()[:26]}"
            else:
                img = len(e._element.findall(".//" + NSI))
                desc = f"{'IMG ' if img else ''}{e.text.strip()[:56]}"
            marque = "  <<<" if j == i else ""
            print(f"  [{j}] {desc}{marque}")
        print()
