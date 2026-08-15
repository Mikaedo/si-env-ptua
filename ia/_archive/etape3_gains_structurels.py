# -*- coding: utf-8 -*-
"""
Etape 3 : recuperer des pages par la structure, seul levier qui en fait
vraiment gagner.

Constat de l'etape precedente : reduire les figures libere de la hauteur, mais
cette hauteur se repartit en bas d'une vingtaine de pages sans qu'aucune ne
disparaisse. Les gains reels viennent des sauts de page.

  a) Pages blanches : trois paires de sauts de page consecutifs produisent
     chacune une page vide.
  b) Titres de partie : chaque « PREMIERE / DEUXIEME / TROISIEME PARTIE »
     occupe une page entiere pour trois lignes. Le titre est conserve mais
     placee en tete du chapitre qui suit.
  c) Espacement apres les paragraphes ramene de 8 a 6 points : l'interligne
     1,5 impose par le reglement n'est pas touche.

Sortie : MEMOIRE_ETAPE3.docx
"""
import os
import re
import shutil

from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn

DOSSIER = r"C:\Users\DELL\Downloads\MEMOIRE"
SOURCE = os.path.join(DOSSIER, "MEMOIRE_ETAPE2.docx")
SORTIE = os.path.join(DOSSIER, "MEMOIRE_ETAPE3.docx")

A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'


def sauts_de_page(element):
    """Retourne les balises de saut de page contenues dans un paragraphe."""
    return [br for br in element.findall('.//' + qn('w:br'))
            if br.get(qn('w:type')) == 'page']


def est_vide(element):
    if not element.tag.endswith('}p'):
        return False
    texte = ''.join(t.text or '' for t in element.iter(qn('w:t'))).strip()
    return not texte and not element.findall('.//{%s}blip' % A_NS)


def supprimer_pages_blanches(doc):
    """Retire le second saut de page de chaque paire consecutive.

    Deux sauts qui se suivent, sans contenu entre eux, produisent une page
    entierement vide.
    """
    body = doc.element.body
    elements = [el for el in body if el.tag.endswith('}p')]
    retires = 0
    precedent_avait_saut = False
    for el in elements:
        sauts = sauts_de_page(el)
        vide = est_vide(el)
        if sauts and vide:
            if precedent_avait_saut:
                # Saut redondant : on le supprime, la page vide disparait.
                for br in sauts:
                    br.getparent().remove(br)
                retires += 1
                precedent_avait_saut = False
                continue
            precedent_avait_saut = True
        elif not vide:
            precedent_avait_saut = False
    return retires


def compacter_titres_parties(doc):
    """Supprime le saut de page qui suit un titre de partie.

    Le titre reste, mais le chapitre suivant enchaine sur la meme page au lieu
    d'en ouvrir une nouvelle.
    """
    traites = 0
    for p in doc.paragraphs:
        if not re.search(r'(PREMI|DEUXI|TROISI)\w?RE PARTIE', p.text.upper()):
            continue
        # On avance jusqu'au prochain saut de page et on le retire
        suivant = p._element.getnext()
        parcourus = 0
        while suivant is not None and parcourus < 12:
            sauts = sauts_de_page(suivant)
            if sauts:
                for br in sauts:
                    br.getparent().remove(br)
                traites += 1
                break
            texte = ''.join(t.text or '' for t in suivant.iter(qn('w:t'))).strip()
            if texte and not texte.upper().startswith('CE'):
                break  # on est deja dans le contenu, ne rien toucher
            suivant = suivant.getnext()
            parcourus += 1
    return traites


def resserrer_espacement(doc):
    """Ramene l'espacement apres paragraphe de 8 a 6 points.

    L'interligne 1,5 exige par les regles de forme reste inchange : seul
    l'espace entre paragraphes est resserre.
    """
    style = doc.styles['Normal']
    avant = style.paragraph_format.space_after
    style.paragraph_format.space_after = Pt(6)
    return (avant.pt if avant else None), 6


def main():
    shutil.copy2(SOURCE, SORTIE)
    doc = Document(SORTIE)

    blanches = supprimer_pages_blanches(doc)
    print("  pages blanches supprimees              : %d" % blanches)

    parties = compacter_titres_parties(doc)
    print("  titres de partie compactes             : %d" % parties)

    avant, apres = resserrer_espacement(doc)
    print("  espacement apres paragraphe            : %s -> %d pt" % (avant, apres))

    doc.save(SORTIE)
    print("\nEnregistre : %s" % SORTIE)


if __name__ == "__main__":
    main()
