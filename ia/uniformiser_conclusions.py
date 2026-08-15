# -*- coding: utf-8 -*-
"""
Rend uniforme la mise en page des conclusions partielles.

Le document en comptait trois dans le corps, dont deux precedees d'un saut de
page et une non. La regle retenue est qu'aucune ne commence une page.

Le raisonnement est de hierarchie : ouvrir une page neuve signale au lecteur
qu'une division majeure commence. Le chapitre merite ce signal, sa conclusion
partielle non, puisqu'elle referme ce qui precede au lieu d'ouvrir autre chose.
La detacher reviendrait a lui donner le poids d'un chapitre. S'y ajoute un
effet pratique : ces conclusions font une dizaine de lignes, et seules sur une
page elles laissent les trois quarts de la feuille en blanc, exactement le
defaut que la relecture precedente avait corrige ailleurs.

Le saut n'est pas porte par le titre mais par un paragraphe vide qui le
precede. C'est ce paragraphe qu'il faut retirer, sans quoi le saut subsiste et
laisse en plus une ligne vide orpheline.

En contrepartie, le titre recoit keep_with_next : sans lui, la suppression du
saut pourrait laisser le titre seul en bas de page, son texte commencant sur la
suivante, ce qui serait un defaut pire que celui corrige.
"""
import shutil
from pathlib import Path

from docx import Document

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SOURCE = Path(r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_FINAL.docx")
SAUVEGARDE = SOURCE.with_name("MEMOIRE_FINAL_avant_conclusions.docx")


def porte_un_saut(p):
    """Un paragraphe contient-il un saut de page manuel ?"""
    if p is None:
        return False
    if p.paragraph_format.page_break_before:
        return True
    return bool(p._element.findall(f".//{W}br[@{W}type='page']"))


def main():
    shutil.copy2(SOURCE, SAUVEGARDE)
    doc = Document(SOURCE)
    paras = doc.paragraphs

    cibles = [i for i, p in enumerate(paras)
              if p.style.name.startswith("Heading")
              and p.text.strip() == "Conclusion partielle"]
    print(f"{len(cibles)} conclusion(s) partielle(s) dans le corps")

    for i in cibles:
        titre = paras[i]
        titre.paragraph_format.page_break_before = False
        titre.paragraph_format.keep_with_next = True

        # Le paragraphe vide qui precede porte le saut : on le supprime.
        avant = paras[i - 1] if i else None
        if avant is not None and not avant.text.strip() and porte_un_saut(avant):
            avant._element.getparent().remove(avant._element)
            print(f"  saut retire avant la conclusion du rang {i}")
        else:
            print(f"  rang {i} : deja au fil du texte")

    doc.save(SOURCE)
    print(f"\nSauvegarde : {SAUVEGARDE.name}")


if __name__ == "__main__":
    main()
