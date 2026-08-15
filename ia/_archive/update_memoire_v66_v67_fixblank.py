# -*- coding: utf-8 -*-
"""v66 -> v67 : supprime 2 sauts de page redondants juste apres le tableau
"DEUXIEME PARTIE" (3 sauts consecutifs au lieu d'un seul), qui creaient deux
pages blanches avant le chapitre 4."""
from docx import Document
from docx.oxml.ns import qn

SRC = r"C:\Users\DELL\Downloads\MEMOIRE_SI-ENV_v66.docx"
DST = r"C:\Users\DELL\Downloads\MEMOIRE_SI-ENV_v67.docx"

doc = Document(SRC)
body = doc.element.body
children = list(body.iterchildren())

count_p = -1
targets = []
for el in children:
    if el.tag == qn('w:p'):
        count_p += 1
        if count_p in (301, 302):
            brs = el.findall('.//' + qn('w:br'))
            pgbrs = [b for b in brs if b.get(qn('w:type')) == 'page']
            txt = ''.join(t.text or '' for t in el.findall('.//' + qn('w:t')))
            assert len(pgbrs) == 1 and not txt.strip(), f"paragraphe {count_p} inattendu : {txt!r}"
            targets.append(el)

assert len(targets) == 2, f"attendu 2 paragraphes a supprimer, trouve {len(targets)}"
for el in targets:
    el.getparent().remove(el)
    print("[OK] Saut de page redondant supprime")

doc.save(DST)
print(f"\n=== MEMOIRE SAUVEGARDE : {DST} ===")
