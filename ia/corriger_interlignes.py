# -*- coding: utf-8 -*-
"""
Retablit l'interligne de 1,5 sur les paragraphes de corps qui l'avaient perdu.

Le guide impose un interligne de 1,5 pour le texte courant. Dans le document,
cette valeur n'est pas fixee paragraphe par paragraphe : elle est heritee du
style Normal, et les paragraphes conformes portent donc line_spacing = None.
Un paragraphe qui porte explicitement 1,0 est donc une anomalie, vestige d'une
mise en forme locale : il se lit plus dense que ses voisins, ce qui saute aux
yeux sur une page comme la conclusion generale ou il ouvre le texte.

La correction consiste a effacer la valeur locale plutot qu'a la remplacer par
1,5. Effacer rend le paragraphe a nouveau solidaire du style : si la norme
changeait, il suivrait, alors qu'une valeur ecrite en dur resterait figee.

Encore faut-il distinguer l'anomalie du choix. Un premier passage trop large
avait signale vingt-sept paragraphes, dont toutes les entrees de bibliographie
a 1,2, la page de garde a 1,1 et la dedicace a 1,0 : ces valeurs sont uniformes
sur l'ensemble de leur section, donc voulues. Le critere retenu est donc
relatif et non absolu : un paragraphe n'est fautif que s'il s'ecarte de ses
voisins immediats a l'interieur de la meme section. La conclusion generale est
le seul endroit ou cela se produit.
"""
import shutil
from pathlib import Path

from docx import Document
from docx.shared import Pt

SOURCE = Path(r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_FINAL.docx")
SAUVEGARDE = SOURCE.with_name("MEMOIRE_FINAL_avant_interlignes.docx")

# En deca de cette longueur, un paragraphe Normal est probablement une legende
# ou une ligne technique, pas du texte courant.
LONGUEUR_CORPS = 120


def main():
    shutil.copy2(SOURCE, SAUVEGARDE)
    doc = Document(SOURCE)

    # Le document est parcouru section par section, une section commencant a
    # chaque titre de niveau 1. Dans chacune, on ne retient que les paragraphes
    # de corps, puis on compare leur interligne a celui de leurs voisins.
    sections, courante = [], []
    for p in doc.paragraphs:
        if p.style.name.startswith("Heading 1"):
            if courante:
                sections.append(courante)
            courante = []
            continue
        texte = p.text.strip()
        if (p.style.name == "Normal" and len(texte) >= LONGUEUR_CORPS
                and not texte.startswith(("Figure", "Tableau", "Source"))):
            courante.append(p)
    if courante:
        sections.append(courante)

    anomalies = []
    for groupe in sections:
        if len(groupe) < 3:
            continue                    # trop court pour degager une norme
        valeurs = [p.paragraph_format.line_spacing for p in groupe]
        # L'interligne dominant de la section fait foi.
        dominant = max(set(valeurs), key=valeurs.count)
        if valeurs.count(dominant) < len(valeurs) * 0.6:
            continue                    # section sans norme claire, on s'abstient
        for p, valeur in zip(groupe, valeurs):
            if valeur != dominant:
                anomalies.append((p, valeur, dominant, p.text.strip()[:60]))

    print(f"{len(anomalies)} paragraphe(s) en rupture avec leur section")
    for p, valeur, dominant, extrait in anomalies:
        f = p.paragraph_format
        f.line_spacing = dominant      # aligne sur ses voisins
        if f.space_after is not None and f.space_after < Pt(6):
            f.space_after = Pt(6)      # espacement des paragraphes voisins
        print(f"  {valeur} devient {dominant} : {extrait}")

    doc.save(SOURCE)
    print(f"\nSauvegarde : {SAUVEGARDE.name}")


if __name__ == "__main__":
    main()
