# -*- coding: utf-8 -*-
"""Descend en annexe les captures qui n'etablissent rien.

Une capture merite le corps lorsqu'elle prouve ce que le texte affirme sans
pouvoir le montrer. Celles qui disent seulement « cela existe » alourdissent la
lecture sans l'eclairer : la documentation interactive des services, les vues
generales du tableau de bord et le journal d'audit sont dans ce cas. Le texte
qui les annoncait renvoie desormais a l'annexe.
"""
import shutil, sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_FINAL.docx"
shutil.copy2(SRC, SRC.replace(".docx", "_avant_descente_annexe.docx"))
d = Document(SRC)
NSB="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NSI="{http://schemas.openxmlformats.org/drawingml/2006/main}blip"

corps=[]
for e in d.element.body.iterchildren():
    if e.tag==NSB+"p": corps.append(("p",Paragraph(e,d),e))
    elif e.tag==NSB+"tbl": corps.append(("t",Table(e,d),e))

A_DESCENDRE = ["Figure 5.1 :", "Figure 5.3 :", "Figure 5.4 :"]

# Le corps commence a l introduction generale : avant se trouvent les
# listes liminaires, ou les memes legendes reapparaissent sans image.
DEBUT = next(i for i,(g,el,x) in enumerate(corps)
             if g=="p" and el.style.name.startswith("Heading 1")
             and el.text.strip().lower().startswith("introduction g"))

# Destination : la fin des annexes.
fin_annexes = corps[-1][2]

deplaces = 0
for cle in A_DESCENDRE:
    i_leg = None
    for i,(g,el,x) in enumerate(corps):
        if i < DEBUT: continue
        if g=="p" and el.text.strip().startswith(cle):
            i_leg = i; break
    if i_leg is None:
        print(f"  introuvable : {cle}"); continue
    # L'image se trouve juste au-dessus de sa legende.
    i_img = None
    for j in range(i_leg-1, max(0,i_leg-3), -1):
        if corps[j][0]=="p" and corps[j][1]._element.findall(".//"+NSI):
            i_img = j; break
    if i_img is None:
        print(f"  image introuvable pour {cle}"); continue

    bloc = [corps[i_img][2], corps[i_leg][2]]
    for x in bloc: x.getparent().remove(x)
    courant = fin_annexes
    for x in bloc:
        courant.addnext(x); courant = x
    fin_annexes = courant
    deplaces += 1
    print(f"  descendu : {cle}")

d.save(SRC)
print(f"\n{deplaces} figure(s) deplacee(s) en annexe")
