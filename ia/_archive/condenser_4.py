# -*- coding: utf-8 -*-
"""
Passe finale :
  - Tableau 6.6 remplace par une phrase fluide integree au paragraphe qui
    l'introduit.
  - §6.5 discussion : longue enumeration synthetisee.
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


# ─── Tableau 6.6 : titre et table supprimes, contenu integre ────────────
titre_66 = par("Tableau 6.6 : Répartition des composants sur les hébergeurs gratuits")
tbl_66 = titre_66._p.getnext()
if tbl_66 is not None and tbl_66.tag.endswith("}tbl"):
    tbl_66.getparent().remove(tbl_66)
supprimer(titre_66)

# On enrichit le paragraphe precedent pour ne pas perdre l'information
p_choix = par("Trois plateformes se répartissent les composants du système")
remplacer(
    p_choix,
    "Trois plateformes se répartissent les composants du système, chacune "
    "ayant été retenue pour un point précis de son offre gratuite. Supabase "
    "héberge la base PostgreSQL 16 accompagnée de l'extension PostGIS "
    "préinstallée, ce qui a été le critère décisif : aucun autre acteur "
    "gratuit ne propose PostGIS sans carte. Hugging Face Spaces exécute le "
    "backend FastAPI dans un conteneur Docker identique à celui de "
    "l'environnement local, avec HTTPS assuré par la plateforme. Cloudflare "
    "Pages sert le tableau de bord Angular sous forme de fichiers statiques "
    "distribués par son CDN mondial. GitHub Actions orchestre l'ensemble : les "
    "trente-deux tests fonctionnels du paragraphe 6.2 sont rejoués à chaque "
    "poussée de code, et un déploiement automatique publie le backend sur "
    "Hugging Face à chaque fusion sur la branche principale. Le tableau 6.6 "
    "récapitule cette répartition.",
    "Trois plateformes se répartissent les composants, chacune retenue pour "
    "un point précis de son offre gratuite. Supabase héberge la base "
    "PostgreSQL 16 accompagnée de l'extension PostGIS préinstallée (critère "
    "décisif, aucun autre acteur gratuit ne propose PostGIS sans carte) et un "
    "bucket public d'un gigaoctet pour les photos. Hugging Face Spaces exécute "
    "le backend FastAPI dans un conteneur Docker identique à celui de "
    "l'environnement local, avec HTTPS assuré par la plateforme. Cloudflare "
    "Pages sert le tableau de bord Angular en fichiers statiques distribués "
    "par son CDN mondial. GitHub Actions orchestre l'ensemble : les "
    "trente-deux tests fonctionnels du paragraphe 6.2 sont rejoués à chaque "
    "poussée de code, et un déploiement automatique publie le backend sur "
    "Hugging Face à chaque fusion sur la branche principale.",
)

# ─── §6.5 discussion condensee ─────────────────────────────────────────
p65 = par("Le SI-ENV répond aux six lacunes du chapitre 2")
remplacer(
    p65,
    "Le SI-ENV répond aux six lacunes du chapitre 2 : signalement instantané avec diagnostic IA, subjectivité encadrée, géolocalisation automatique, données centralisées, rapports en secondes, alertes quasi temps réel (tableau de bord rafraîchi toutes les 10 à 15 secondes, file d'attente mobile vidée automatiquement dès le retour du réseau). Les limites : tests exécutés en environnement de développement local, dataset Recycle Trash non encore validé sur des photographies réelles des chantiers du PTUA, propagation d'erreur inhérente au pipeline en cascade (une détection manquée par YOLOv8 dégrade la classification par MobileNetV2), dépendance Internet pour le satellite, résolution Sentinel-5P trop grossière au niveau chantier.",
    "Le SI-ENV répond aux six lacunes du chapitre 2 : signalement instantané "
    "avec diagnostic IA, subjectivité encadrée, géolocalisation automatique, "
    "données centralisées, rapports en secondes, alertes quasi temps réel "
    "(dashboard rafraîchi toutes les 10 à 15 secondes, file d'attente mobile "
    "vidée dès le retour du réseau). Les limites assumées sont la validation "
    "en environnement local, un dataset Recycle Trash non encore éprouvé sur "
    "des photographies réelles du PTUA, la propagation d'erreur du pipeline "
    "en cascade et la résolution grossière de Sentinel-5P.",
)

d.save(CHEMIN)
print("Tableau 6.6 fusionné dans le texte, §6.5 condensé.")
