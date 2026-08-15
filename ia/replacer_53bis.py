# -*- coding: utf-8 -*-
"""Replace la section 5.3 bis apres le tableau 5.2, et non entre la legende
et le tableau qu'elle annonce."""
import shutil, sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_FINAL.docx"
shutil.copy2(SRC, SRC.replace(".docx", "_avant_replacement_53bis.docx"))
d = Document(SRC)
NSB = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

corps = []
for e in d.element.body.iterchildren():
    if e.tag == NSB + "p":
        corps.append(("p", Paragraph(e, d), e))
    elif e.tag == NSB + "tbl":
        corps.append(("t", Table(e, d), e))

# Le bloc egare : le titre 5.3 bis et ses quatre paragraphes.
debut = None
for i, (g, el, xml) in enumerate(corps):
    if g == "p" and el.text.strip().startswith("5.3 bis"):
        debut = i
        break
if debut is None:
    raise SystemExit("section 5.3 bis introuvable")

bloc = [corps[debut + k][2] for k in range(5)]

# Destination : le tableau qui suit immediatement, c'est-a-dire le tableau 5.2
# que la legende annonce. Une legende de tableau se place au-dessus de son
# tableau ; s'interposer entre les deux les separe.
cible = None
for k in range(debut + 5, min(debut + 9, len(corps))):
    if corps[k][0] == "t":
        cible = corps[k][2]
        break
if cible is None:
    raise SystemExit("tableau 5.2 introuvable apres la section")

for el in bloc:
    el.getparent().remove(el)
ancre = cible
for el in bloc:
    ancre.addnext(el)
    ancre = el

d.save(SRC)
print("section 5.3 bis replacee apres le tableau 5.2")
