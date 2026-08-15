# -*- coding: utf-8 -*-
"""
Etape 23 : basculer les deux diagrammes les plus charges (cas d'utilisation,
classes) sur une page dediee en paysage, agrandie.

Analyse prealable (par extraction des images et mesure) :
  - Figure 4.2 (cas d'utilisation) : 7 acteurs, 15+ cas, ratio 1,1:1 (quasi
    carre). En portrait, deja a la largeur max (15,5 cm = largeur utile de la
    page). Le paysage avec les memes marges (2,5/2,5/2,5/3,0 cm) n'apporterait
    qu'un gain marginal, la hauteur utile en paysage (16 cm) etant a peine
    superieure a la hauteur actuelle. Un gain reel suppose des marges plus
    serrees (1,5 cm), usage courant pour une page dediee a une seule figure
    pleine page.
  - Figure 4.3 (diagramme de classes) : 12 classes, ratio 1,75:1 (large). Le
    paysage apporte un gain net meme avec les marges du corps.

Les deux figures recoivent donc une page paysage dediee, marges reduites a
1,5 cm (uniquement sur ces deux pages, le reste du document garde les marges
du reglement UPB deja verifiees 15/15). En-tete/pied de page et numerotation
des pages sont conserves a l'identique (memes references), la pagination
continue normalement.

Sortie : mise a jour de MEMOIRE_FINAL.docx
"""
import os
import sys

from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

sys.stdout.reconfigure(encoding='utf-8')

CIBLE = os.path.join('C:', os.sep, 'Users', 'DELL', 'Downloads', 'MEMOIRE',
                     'MEMOIRE_FINAL.docx')
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
WQ = '{%s}' % W

MARGE_PAYSAGE_TWIPS = 850  # 1,5 cm


def qw(tag):
    return qn('w:' + tag)


def trouver_figure(body, legende_exacte):
    """Renvoie (paragraphe_image, paragraphe_legende) pour la vraie
    occurrence dans le corps (pas celle de la liste des figures)."""
    els = list(body)
    for i, el in enumerate(els):
        if not el.tag.endswith('}p'):
            continue
        txt = ''.join(t.text or '' for t in el.iter(WQ + 't')).strip()
        if txt != legende_exacte:
            continue
        for j in range(i - 1, max(0, i - 3), -1):
            if els[j].findall('.//{%s}blip' % A_NS):
                return els[j], el
    return None, None


def copier_sectpr_reference(ref_sectpr):
    """Copie profonde du sectPr de reference (memes en-tete/pied/numerotation)."""
    import copy
    return copy.deepcopy(ref_sectpr)


def construire_sectpr_paysage(ref_sectpr, page_w, page_h):
    sect = copier_sectpr_reference(ref_sectpr)
    # Supprime un eventuel pgNumType (on ne veut pas relancer la numerotation)
    for tag in ('pgNumType', 'type'):
        el = sect.find(WQ + tag)
        if el is not None:
            sect.remove(el)
    pgsz = sect.find(WQ + 'pgSz')
    pgsz.set(qw('w'), str(page_h))   # page tournee : la largeur devient hauteur
    pgsz.set(qw('h'), str(page_w))
    pgsz.set(qw('orient'), 'landscape')
    pgmar = sect.find(WQ + 'pgMar')
    for cote in ('top', 'right', 'bottom', 'left'):
        pgmar.set(qw(cote), str(MARGE_PAYSAGE_TWIPS))
    return sect


def construire_sectpr_portrait(ref_sectpr):
    import copy
    sect = copy.deepcopy(ref_sectpr)
    for tag in ('pgNumType', 'type'):
        el = sect.find(WQ + tag)
        if el is not None:
            sect.remove(el)
    return sect


def inserer_marqueur_section(ancre_el, sectpr, avant=True):
    p = OxmlElement('w:p')
    if avant:
        ancre_el.addprevious(p)
    else:
        ancre_el.addnext(p)
    ppr = OxmlElement('w:pPr')
    p.append(ppr)
    ppr.append(sectpr)
    return p


def redimensionner(img_para, largeur_cm, hauteur_cm):
    for ext in img_para.iter(WQ.replace('w:', '') + 'ext') if False else []:
        pass
    for ext in img_para.iter('{%s}ext' % A_NS):
        ext.set('cx', str(int(round(largeur_cm * 360000))))
        ext.set('cy', str(int(round(hauteur_cm * 360000))))


def main():
    doc = Document(CIBLE)
    body = doc.element.body
    ref_sectpr = body.find(WQ + 'sectPr')  # dernier sectPr (portrait, corps)
    page_w = int(ref_sectpr.find(WQ + 'pgSz').get(qw('w')))
    page_h = int(ref_sectpr.find(WQ + 'pgSz').get(qw('h')))
    print("  page de reference : %d x %d twips (portrait)" % (page_w, page_h))

    cibles = [
        ("Figure 4.2 : Diagramme de cas d'utilisation.", 15.95, 14.5),
        ("Figure 4.3 : Diagramme de classes.", 18.5, 10.57),
    ]

    for legende, larg_cm, haut_cm in cibles:
        img_el, cap_el = trouver_figure(body, legende)
        assert img_el is not None, "figure introuvable : %r" % legende
        print("  trouve : %s" % legende[:50])

        # Marqueur de fin de section portrait, juste avant l'image
        sect_portrait_avant = construire_sectpr_portrait(ref_sectpr)
        inserer_marqueur_section(img_el, sect_portrait_avant, avant=True)

        # Redimensionnement de l'image pour la page paysage
        redimensionner(img_el, larg_cm, haut_cm)

        # Marqueur de fin de section paysage, juste apres la legende
        sect_paysage = construire_sectpr_paysage(ref_sectpr, page_w, page_h)
        inserer_marqueur_section(cap_el, sect_paysage, avant=False)

        print("    -> page paysage dediee, image %.1f x %.1f cm"
              % (larg_cm, haut_cm))

    doc.save(CIBLE)
    print("\nEnregistré : %s" % CIBLE)


if __name__ == "__main__":
    main()
