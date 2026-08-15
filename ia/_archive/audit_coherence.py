# -*- coding: utf-8 -*-
"""
Recherche les incoherences internes du memoire : ecarts entre les listes et le
contenu reel, trous de numerotation, references bibliographiques orphelines,
chiffres contradictoires. Ne modifie rien.
"""
import re
import sys

from docx import Document

CHEMIN = sys.argv[1] if len(sys.argv) > 1 else \
    r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_N'GUESSAN_v11.docx"

doc = Document(CHEMIN)
paras = [p.text.strip() for p in doc.paragraphs]
txt = "\n".join(paras)
anomalies = []


def bloc_liste(mot_cle, motif):
    """Retourne les numeros listes dans une section de liste."""
    debut = None
    for i, t in enumerate(paras[:200]):
        if t.upper().startswith(mot_cle):
            debut = i
            break
    if debut is None:
        return None, []
    nums = []
    for i in range(debut + 1, min(debut + 80, len(paras))):
        t = paras[i]
        m = re.match(motif, t)
        if m:
            nums.append(m.group(1))
        elif t and nums and not t.startswith(('Figure', 'Tableau', 'Figures')):
            break
    return debut, nums


def tri(n):
    a, b = n.split('.')
    return (0 if a.isdigit() else 1, int(a) if a.isdigit() else ord(a), int(b))


# ── 1. Listes contre contenu reel ───────────────────────────────────────────
_, fig_listees = bloc_liste('LISTE DES FIGURES', r'^Figure\s+([0-9A-D]+\.[0-9]+)')
_, tab_listees = bloc_liste('LISTE DES TABLEAUX', r'^Tableau\s+([0-9]+\.[0-9]+)')

fig_reelles = sorted(set(re.findall(r'^Figure\s+([0-9A-D]+\.[0-9]+)\s*:', txt, re.M)), key=tri)
tab_reels = sorted(set(re.findall(r'^Tableau\s+([0-9]+\.[0-9]+)\s*[:.]', txt, re.M)), key=tri)

for num in fig_reelles:
    if num not in fig_listees:
        anomalies.append(("Figure %s absente de la liste des figures" % num, "liste"))
for num in fig_listees:
    if num not in fig_reelles:
        anomalies.append(("Figure %s listee mais introuvable dans le document" % num, "liste"))
for num in tab_reels:
    if num not in tab_listees:
        anomalies.append(("Tableau %s absent de la liste des tableaux" % num, "liste"))
for num in tab_listees:
    if num not in tab_reels:
        anomalies.append(("Tableau %s liste mais introuvable dans le document" % num, "liste"))

# ── 2. Trous de numerotation ────────────────────────────────────────────────
def trous(nums, etiquette):
    par_chap = {}
    for n in nums:
        c, o = n.split('.')
        par_chap.setdefault(c, []).append(int(o))
    for c, ordres in par_chap.items():
        ordres.sort()
        attendus = set(range(1, max(ordres) + 1))
        for manquant in sorted(attendus - set(ordres)):
            anomalies.append(("%s %s.%d manquant dans la sequence"
                              % (etiquette, c, manquant), "numerotation"))


trous(fig_reelles, "Figure")
trous(tab_reels, "Tableau")

# ── 3. References bibliographiques ──────────────────────────────────────────
citees = set(int(x) for x in re.findall(r'\[(\d+)\]', txt))
# Entrees de bibliographie : lignes commencant par [n]
biblio = set(int(x) for x in re.findall(r'^\[(\d+)\]', txt, re.M))
for n in sorted(citees - biblio):
    anomalies.append(("Source [%d] citee mais absente de la bibliographie" % n, "biblio"))
for n in sorted(biblio - citees):
    anomalies.append(("Source [%d] en bibliographie mais jamais citee" % n, "biblio"))
if citees:
    manquants = sorted(set(range(1, max(citees) + 1)) - citees)
    for n in manquants:
        anomalies.append(("Numero de source [%d] non utilise (sequence trouee)" % n, "biblio"))

# ── 4. Chiffres contradictoires ─────────────────────────────────────────────
controles = [
    (r'mAP@?0?[.,]5[^%]{0,40}?0[.,](\d{3})', "mAP@0,5", {'807'}),
    (r'JWT\s*\((\d+)h', "duree du jeton JWT", {'12'}),
]
for motif, libelle, attendues in controles:
    trouvees = set(re.findall(motif, txt, re.I))
    ecarts = trouvees - attendues
    if ecarts:
        anomalies.append(("%s : valeurs divergentes %s (attendu %s)"
                          % (libelle, sorted(ecarts), sorted(attendues)), "chiffres"))

# Nombre d'images du corpus (tableau 8.1 annonce 2 462)
corpus = set(re.findall(r'(\d[\s\u00a0]?\d{3})\s+images', txt))
if len(corpus) > 1:
    anomalies.append(("Volume du corpus annonce de plusieurs facons : %s"
                      % sorted(corpus), "chiffres"))

# ── 5. Renvois manquants ────────────────────────────────────────────────────
for num in fig_reelles:
    if len(re.findall(r'figure[s]?\s+' + re.escape(num), txt, re.I)) < 2:
        # tolere la forme « figures X et Y »
        if not re.search(r'figures\s+[0-9A-D]+\.\d+\s+et\s+' + re.escape(num), txt, re.I):
            anomalies.append(("Figure %s jamais citee dans le texte" % num, "renvoi"))
for num in tab_reels:
    if len(re.findall(r'tableau[x]?\s+' + re.escape(num), txt, re.I)) < 2:
        anomalies.append(("Tableau %s jamais cite dans le texte" % num, "renvoi"))

# ── Rapport ─────────────────────────────────────────────────────────────────
print("=" * 74)
print("AUDIT DE COHERENCE - %s" % CHEMIN.split("\\")[-1])
print("=" * 74)
print("\nfigures : %d dans le document, %d listees" % (len(fig_reelles), len(fig_listees)))
print("tableaux : %d dans le document, %d listes" % (len(tab_reels), len(tab_listees)))
print("sources : %d citees, %d en bibliographie" % (len(citees), len(biblio)))

if not anomalies:
    print("\nAucune incoherence detectee.")
else:
    par_cat = {}
    for lib, cat in anomalies:
        par_cat.setdefault(cat, []).append(lib)
    print("\n%d INCOHERENCE(S)" % len(anomalies))
    for cat in ('liste', 'numerotation', 'biblio', 'chiffres', 'renvoi'):
        if cat in par_cat:
            print("\n  [%s]" % cat.upper())
            for lib in par_cat[cat]:
                print("    - %s" % lib)
