# -*- coding: utf-8 -*-
"""Corrige la table des matieres (champ Word TOC reel) apres suppression du
Tableau 5.3 et de la section 5.6 par l'utilisateur :
1) supprime l'entree de TDM devenue obsolete ("5.6  Cas d'utilisation")
2) force Word a recalculer TOUS les champs (TOC + PAGEREF) a l'ouverture,
   ce qui regenere automatiquement des numeros de page corrects pour
   chaque chapitre/section."""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_N'GUESSAN.docx"
DST = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_N'GUESSAN_TDM_corrigee.docx"

doc = Document(SRC)
paras = doc.paragraphs

# 1) Supprimer l'entree de TDM obsolete (style TM2, texte "5.6  Cas d'utilisation")
removed = 0
for p in paras:
    if "5.6" in p.text and "Cas d'utilisation" in p.text:
        p._element.getparent().remove(p._element)
        removed += 1
assert removed == 1, f"attendu 1 entree supprimee, trouve {removed}"
print("[OK] Entree de TDM obsolete '5.6 Cas d'utilisation' supprimee")

# 2) Forcer la mise a jour de tous les champs (TOC + PAGEREF) a l'ouverture
settings = doc.settings.element
uf = settings.find(qn('w:updateFields'))
if uf is None:
    uf = OxmlElement('w:updateFields')
    settings.insert(0, uf)
uf.set(qn('w:val'), 'true')
print("[OK] updateFields active : Word recalculera les numeros de page a l'ouverture")

doc.save(DST)
print(f"\n=== SAUVEGARDE : {DST} ===")
