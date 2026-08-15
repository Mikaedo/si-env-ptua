# -*- coding: utf-8 -*-
"""Etape 2/3 : renumerote les 23 references bibliographiques selon l'ordre
IEEE strict (ordre de PREMIERE apparition dans le texte), comme l'exige le
guide UPB et comme l'annonce deja le memoire lui-meme (paragraphe
d'introduction de la bibliographie). Deux passes :
  1) toutes les citations [n] dans le corps du texte -> [nouveau_n]
  2) les 23 entrees de la bibliographie sont reordonnees + relabelisees,
     en conservant la mise en forme (numero en gras, reste en texte normal).
Utilise des jetons temporaires pour eviter toute collision lors du
remappage (ex: l'ancien [6] devient [2], mais un [2] existant devient [4] :
un remplacement sequentiel naif corromprait les valeurs)."""
import re
from docx import Document

SRC = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_N'GUESSAN_v4.docx"
DST = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_N'GUESSAN_v5.docx"

doc = Document(SRC)
paras = doc.paragraphs

BIBLIO_HEADING = 548
BIBLIO_FIRST_ENTRY = 552
BIBLIO_LAST_ENTRY = 574  # inclus, 23 entrees (552..574)

cite_re = re.compile(r'\[(\d+)\]')

# --- 1) determiner l'ordre de premiere apparition dans le corps ---
seen_order = []
for i in range(0, BIBLIO_HEADING):
    for m in cite_re.finditer(paras[i].text):
        n = int(m.group(1))
        if n not in seen_order:
            seen_order.append(n)

assert len(seen_order) == 23, f"attendu 23 references distinctes citees, trouve {len(seen_order)}"
old2new = {old: new for new, old in enumerate(seen_order, start=1)}
print("Mapping ancien -> nouveau numero :")
for old in sorted(old2new):
    print(f"  [{old}] -> [{old2new[old]}]")

# --- 2) remplacer toutes les citations dans le corps (jetons temporaires) ---
def remap_paragraph_citations(p):
    t = p.text
    if not cite_re.search(t):
        return
    # jeton temporaire insensible aux collisions
    def to_token(m):
        return f"\uE000{old2new[int(m.group(1))]}\uE001"
    tmp = cite_re.sub(to_token, t)
    new_t = tmp.replace('\uE000', '[').replace('\uE001', ']')
    runs = p.runs
    assert runs, f"paragraphe sans run : {t!r}"
    runs[0].text = new_t
    for r in runs[1:]:
        r.text = ''

n_changed = 0
for i in range(0, BIBLIO_HEADING):
    if cite_re.search(paras[i].text):
        remap_paragraph_citations(paras[i])
        n_changed += 1
print(f"[OK] {n_changed} paragraphes du corps remappes")

# --- 3) extraire les 23 entrees actuelles (ancien numero -> texte apres le crochet) ---
entry_re = re.compile(r'^\[(\d+)\]\s*(.*)$', re.DOTALL)
entries = {}
for i in range(BIBLIO_FIRST_ENTRY, BIBLIO_LAST_ENTRY + 1):
    t = paras[i].text
    m = entry_re.match(t)
    assert m, f"entree bibliographique inattendue a p{i} : {t!r}"
    old_num = int(m.group(1))
    rest = m.group(2)  # texte apres "[n]" (les 2 espaces inclus)
    entries[old_num] = rest

assert set(entries.keys()) == set(range(1, 24)), f"numeros manquants : {set(range(1,24)) - set(entries.keys())}"

# --- 4) reecrire les 23 paragraphes dans le nouvel ordre ascendant ---
for k in range(23):
    new_num = k + 1
    p_idx = BIBLIO_FIRST_ENTRY + k
    old_num = seen_order[k]
    rest = entries[old_num]
    p = paras[p_idx]
    runs = p.runs
    assert len(runs) >= 2, f"structure inattendue a p{p_idx}"
    runs[0].text = f"[{new_num}]"
    runs[0].bold = True
    runs[1].text = rest
    runs[1].bold = False
    for r in runs[2:]:
        r.text = ''
    expected = f"[{new_num}]{rest}"
    assert p.text == expected, f"echec p{p_idx} : {p.text!r} != {expected!r}"

print("[OK] 23 entrees de bibliographie reordonnees et relabelisees")

doc.save(DST)
print(f"\n=== SAUVEGARDE : {DST} ===")
