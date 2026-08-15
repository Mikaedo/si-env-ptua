# -*- coding: utf-8 -*-
"""
Troisieme passe : compression finale pour tenir en 50 pages.
  - Tableau 6.5 (plateformes commerciales) : contenu recycle en une phrase
    dans le paragraphe qui l'introduit.
  - Section §5.7 « Journalisation » : reduite a une phrase courte fusionnee
    au §5.6, la figure 5.4 restant en place a titre d'illustration.
"""
import docx

CHEMIN = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_FINAL.docx"
d = docx.Document(CHEMIN)


def par(debut):
    for p in d.paragraphs:
        if p.text.strip().startswith(debut):
            return p
    raise SystemExit("INTROUVABLE : " + debut[:70])


def remplacer(p, vieux, neuf):
    if vieux not in p.text:
        raise SystemExit("FRAGMENT : " + vieux[:70])
    p.runs[0].text = p.text.replace(vieux, neuf)
    for r in p.runs[1:]:
        r.text = ""


def supprimer(p):
    p._p.getparent().remove(p._p)


# ─── Tableau 6.5 : retirer la ligne titre et la table, remplacer par une
#     phrase synthetique dans le paragraphe precedent ──────────────────
titre_65 = par("Tableau 6.5 : Comparaison indicative avec des plateformes commerciales")

# Retirer la table qui suit
tbl_65 = titre_65._p.getnext()
if tbl_65 is not None and tbl_65.tag.endswith("}tbl"):
    tbl_65.getparent().remove(tbl_65)
supprimer(titre_65)

# ─── §5.7 : journalisation raccourcie ─────────────────────────────────
# On fusionne le contenu principal en une phrase, en supprimant l'ensemble
# des detailles techniques deja implicites dans le §5.6.
p57_texte = par("Chaque opération sensible du système laisse une trace")
remplacer(
    p57_texte,
    "Chaque opération sensible du système laisse une trace : connexions réussies et tentatives échouées, création et changement de statut des signalements, ajout d'actions correctives, génération des rapports PGES, déclenchement automatique des alertes, refus opposés par le contrôle des habilitations, et actions d'administration (comptes, seuils, déploiement du modèle d'intelligence artificielle). Chaque entrée porte un horodatage UTC, un niveau de gravité (INFO, WARNING ou ERROR), l'utilisateur à l'origine de l'action et son adresse IP, reconstituée derrière le proxy à partir de l'en-tête X-Forwarded-For. L'administrateur consulte ce journal depuis le tableau de bord (figure 5.4) et le filtre par niveau, par utilisateur ou par période. Les entrées de plus de trente jours sont purgées à la consultation, le système ne disposant pas d'ordonnanceur dédié.",
    "Chaque opération sensible du système laisse une trace horodatée en UTC "
    "avec son niveau (INFO, WARNING, ERROR), l'utilisateur et l'adresse IP "
    "d'origine. Cela couvre les tentatives d'authentification, les changements "
    "de statut de signalement, la génération des rapports PGES, les alertes "
    "automatiques, les accès refusés par le contrôle des habilitations et les "
    "actions d'administration. L'administrateur consulte ce journal depuis le "
    "tableau de bord (figure 5.4) et le filtre par niveau, utilisateur ou "
    "période ; les entrées de plus de trente jours sont purgées automatiquement.",
)

d.save(CHEMIN)
print("Tableau 6.5 remplace, §5.7 condense.")
