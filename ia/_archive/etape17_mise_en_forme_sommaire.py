# -*- coding: utf-8 -*-
"""
Etape 17 : uniformiser la mise en forme du sommaire.

Le sommaire a ete reecrit sur les lignes de l'ancienne version : chacune a donc
garde le gras de l'entree qu'elle remplacait, ce qui met en gras « Chapitre 3 »
et « Chapitre 6 » mais laisse les deuxieme et troisieme parties en maigre. Les
quatre lignes devenues inutiles, videes de leur texte, creusent en plus un blanc
au milieu de la page.

Regle appliquee : gras pour les titres de partie, maigre pour tout le reste ;
suppression des lignes vides residuelles.

Sortie : mise a jour de MEMOIRE_FINAL.docx
"""
import os
import re
import sys

from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

CIBLE = os.path.join('C:', os.sep, 'Users', 'DELL', 'Downloads', 'MEMOIRE',
                     'MEMOIRE_FINAL.docx')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

#: Entrees du sommaire qui doivent etre en gras.
EN_GRAS = re.compile(r'^(Première|Deuxième|Troisième) partie\b')

#: Toutes les entrees attendues, pour delimiter le bloc a traiter.
ENTREES = re.compile(
    r'^(Introduction générale|(Première|Deuxième|Troisième) partie|'
    r'Chapitre [1-6] :|Conclusion partielle|Conclusion générale)')


def main():
    doc = Document(CIBLE)
    paras = doc.paragraphs

    # Reperage du bloc : de SOMMAIRE a la ligne « Bibliographie ».
    debut = fin = None
    for i, p in enumerate(paras):
        if i > 140:
            break
        t = p.text.strip()
        if t.upper() == 'SOMMAIRE':
            debut = i
        elif debut is not None and t == 'Bibliographie':
            fin = i
            break
    if debut is None or fin is None:
        raise SystemExit("Bloc du sommaire introuvable, rien modifie")
    print("  bloc du sommaire : paragraphes %d a %d" % (debut, fin))

    # ── Uniformisation du gras ──────────────────────────────────────────────
    n_gras = 0
    for i in range(debut + 1, fin):
        t = paras[i].text.strip()
        if not ENTREES.match(t):
            continue
        gras = bool(EN_GRAS.match(t))
        for run in paras[i].runs:
            if run.bold != gras:
                run.bold = gras
                n_gras += 1
    print("  fragments dont le gras a ete corrige : %d" % n_gras)

    # ── Suppression des lignes vides residuelles ────────────────────────────
    supprimes = 0
    for i in range(fin - 1, debut, -1):
        p = paras[i]
        if p.text.strip():
            continue
        # On ne touche pas a un paragraphe porteur d'un saut de section.
        if p._element.findall('.//' + W + 'sectPr'):
            continue
        p._element.getparent().remove(p._element)
        supprimes += 1
    print("  lignes vides supprimees dans le sommaire : %d" % supprimes)

    doc.save(CIBLE)
    print("\nEnregistre : %s" % CIBLE)


if __name__ == "__main__":
    main()
