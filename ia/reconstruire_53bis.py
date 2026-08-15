# -*- coding: utf-8 -*-
"""Reconstruit l'ordre du passage 5.3 bis, desordonne par des insertions
successives dont chacune deplacait le point d'ancrage de la suivante."""
import shutil, sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_FINAL.docx"
shutil.copy2(SRC, SRC.replace(".docx", "_avant_reconstruction.docx"))
d = Document(SRC)
NSB = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NSI = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"

corps = []
for e in d.element.body.iterchildren():
    if e.tag == NSB+"p": corps.append(("p", Paragraph(e, d), e))
    elif e.tag == NSB+"tbl": corps.append(("t", Table(e, d), e))

def trouver(debut_texte, apres=400):
    for i,(g,el,x) in enumerate(corps):
        if i < apres or g != "p": continue
        if el.text.strip().startswith(debut_texte): return i,x
    return None, None

def trouver_image(apres=400):
    """Le paragraphe portant les deux captures citoyennes."""
    for i,(g,el,x) in enumerate(corps):
        if i < apres or g != "p" or el.text.strip(): continue
        if len(el._element.findall(".//"+NSI)) >= 2: return i,x
    return None, None

# Ordre voulu, apres le tableau des paquets Flutter.
CLES = [
    "5.3 bis",
    "Le mécanisme de gestion des plaintes du PTUA",
    "L'accès est conditionné à la proximité",
    "Le rattachement au chantier est déduit",
    "@IMAGE@",
    "Figure 5.2 bis :",
    "La portée de ce contrôle doit enfin",
]

elements = []
for cle in CLES:
    if cle == "@IMAGE@":
        i,x = trouver_image()
    else:
        i,x = trouver(cle)
    if x is None:
        print(f"  INTROUVABLE : {cle}")
    else:
        elements.append(x)

# Le tableau des paquets Flutter, point d'ancrage.
ancre = None
i_leg,_ = trouver("Tableau 5.2 :")
for k in range(i_leg+1, min(i_leg+8, len(corps))):
    if corps[k][0] == "t":
        ancre = corps[k][2]; break
if ancre is None: raise SystemExit("tableau 5.2 introuvable")

for x in elements:
    x.getparent().remove(x)
courant = ancre
for x in elements:
    courant.addnext(x)
    courant = x

d.save(SRC)
print(f"{len(elements)} elements replaces dans l'ordre")
