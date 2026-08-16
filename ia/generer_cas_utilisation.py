# -*- coding: utf-8 -*-
"""
Regenere le diagramme de cas d'utilisation (figure 4.2).

Aucun script source n'existait. L'image en place presentait trois defauts :
  1. un titre incruste « Figure 6.2 » (ancienne numerotation), en contradiction
     avec la legende Word placee juste en dessous ;
  2. acteurs, ellipses et libelles trop petits pour une lecture confortable
     apres reduction a la largeur de la page ;
  3. des associations traversaient des ellipses tierces, et plus de la moitie
     de la hauteur etait vide.

Disposition retenue : les acteurs principaux sont en colonne a gauche, chacun
face a sa bande de cas d'utilisation, ce qui rend les associations courtes et
locales. « S'authentifier », partage par les huit profils, est place en haut
d'un couloir volontairement laisse vide entre la colonne des acteurs et la
premiere colonne de cas : les traits qui y convergent ne rencontrent donc
aucune ellipse.

Les deux organismes de controle sont places immediatement sous le
specialiste du suivi environnemental. Ils n'ouvrent aucun cas qui leur soit
propre et se rattachent aux memes ellipses que lui, ce qui est exactement ce
que signifie un acces en consultation : ils voient ce qu'il produit sans rien
y ajouter. Ce voisinage garde en outre leurs associations courtes.
"""
from PIL import Image, ImageDraw, ImageFont
import math

W, H = 2380, 2740
BLANC = (255, 255, 255)
FG = (0, 0, 0)
GRIS = (110, 110, 110)

img = Image.new("RGB", (W, H), BLANC)
d = ImageDraw.Draw(img)

F_CAS = ImageFont.truetype("arial.ttf", 21)
F_ACTEUR = ImageFont.truetype("arialbd.ttf", 22)
F_SYS = ImageFont.truetype("arialbd.ttf", 26)
F_STEREO = ImageFont.truetype("ariali.ttf", 18)

RX, RY = 148, 52          # demi-axes des ellipses (agrandies)
X_ACTEURS = 130
X_AUTH = 500              # colonne dediee a S'authentifier
COL_A, COL_B = 980, 1560  # deux colonnes de cas d'utilisation
X_SECOND = 2230           # acteurs secondaires, a droite
SYS = (330, 90, 2010, 2620)   # cadre du systeme


def acteur(x, y, nom):
    """Bonhomme UML, agrandi, nom centre en dessous (sur plusieurs lignes)."""
    r = 20
    d.ellipse([x - r, y - r, x + r, y + r], outline=FG, width=4)
    d.line([x, y + r, x, y + 62], fill=FG, width=4)            # tronc
    d.line([x - 34, y + 30, x + 34, y + 30], fill=FG, width=4)  # bras
    d.line([x, y + 62, x - 28, y + 108], fill=FG, width=4)      # jambes
    d.line([x, y + 62, x + 28, y + 108], fill=FG, width=4)
    for i, ligne in enumerate(nom.split("\n")):
        tw = d.textlength(ligne, font=F_ACTEUR)
        d.text((x - tw / 2, y + 120 + 26 * i), ligne, font=F_ACTEUR, fill=FG)


_ellipses = []          # tracees en dernier, apres les associations


def cas(x, y, libelle):
    """Enregistre une ellipse de cas d'utilisation (tracee en seconde passe)."""
    _ellipses.append((x, y, libelle))
    return (x, y)


def tracer_ellipses():
    """Seconde passe : les ellipses, opaques, recouvrent tout trait qui
    passerait derriere elles, comme le fait un outil de modelisation."""
    for x, y, libelle in _ellipses:
        d.ellipse([x - RX, y - RY, x + RX, y + RY], outline=FG, width=3, fill=BLANC)
        lignes = libelle.split("\n")
        depart = y - (len(lignes) * 26) / 2 + 3
        for i, l in enumerate(lignes):
            tw = d.textlength(l, font=F_CAS)
            d.text((x - tw / 2, depart + 26 * i), l, font=F_CAS, fill=FG)


def bord_ellipse(cx, cy, vers):
    """Point du contour de l'ellipse dans la direction de `vers`."""
    dx, dy = vers[0] - cx, vers[1] - cy
    if dx == 0 and dy == 0:
        return (cx, cy)
    ang = math.atan2(dy, dx)
    # rayon de l'ellipse dans cette direction
    k = 1 / math.sqrt((math.cos(ang) / RX) ** 2 + (math.sin(ang) / RY) ** 2)
    return (cx + k * math.cos(ang), cy + k * math.sin(ang))


def association(pt_acteur, centre_cas):
    """Trait acteur - cas d'utilisation, arrete au contour de l'ellipse."""
    p2 = bord_ellipse(centre_cas[0], centre_cas[1], pt_acteur)
    d.line([pt_acteur, p2], fill=FG, width=2)


def include(depuis, vers):
    """Relation d'inclusion : pointille, fleche ouverte, stereotype."""
    p1 = bord_ellipse(depuis[0], depuis[1], vers)
    p2 = bord_ellipse(vers[0], vers[1], depuis)
    pas, t = 16, 0
    lg = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    while t < lg:
        a, b = t / lg, min((t + 9) / lg, 1)
        d.line([p1[0] + (p2[0] - p1[0]) * a, p1[1] + (p2[1] - p1[1]) * a,
                p1[0] + (p2[0] - p1[0]) * b, p1[1] + (p2[1] - p1[1]) * b],
               fill=FG, width=2)
        t += pas
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    for signe in (1, -1):
        a = ang + signe * math.radians(150)
        d.line([p2, (p2[0] + 16 * math.cos(a), p2[1] + 16 * math.sin(a))], fill=FG, width=2)
    txt = "« include »"
    tw = d.textlength(txt, font=F_STEREO)
    d.text(((p1[0] + p2[0]) / 2 - tw / 2, (p1[1] + p2[1]) / 2 - 26), txt, font=F_STEREO, fill=GRIS)


# ─── Cadre du systeme ───────────────────────────────────────────────────
d.rectangle(list(SYS), outline=FG, width=3)
tw = d.textlength("SI-ENV", font=F_SYS)
d.text(((SYS[0] + SYS[2]) / 2 - tw / 2, SYS[1] + 18), "SI-ENV", font=F_SYS, fill=FG)

# ─── Cas d'utilisation ──────────────────────────────────────────────────
auth = cas(X_AUTH, 210, "S'authentifier")

# Responsable Environnement
saisir = cas(COL_A, 380, "Saisir un\nsignalement")
gps_cas = cas(COL_B, 455, "Obtenir les\ncoordonnées GPS")
sync = cas(COL_A, 530, "Synchroniser\nhors ligne")
histo = cas(COL_B, 605, "Consulter\nl'historique")

# Expert HSE
traiter = cas(COL_A, 720, "Traiter un\nsignalement")
alerte_recue = cas(COL_B, 795, "Recevoir\nune alerte")
valider = cas(COL_A, 870, "Valider une\naction corrective")

# Specialiste Suivi Environnemental
bord_cas = cas(COL_A, 1060, "Visualiser le\ntableau de bord")
gerer_alertes = cas(COL_B, 1135, "Gérer\nles alertes")
rapport = cas(COL_A, 1210, "Générer le rapport\nde suivi")
histo_rapports = cas(COL_B, 1285, "Consulter l'historique\ndes rapports")
export = cas(COL_A, 1360, "Exporter\nles données")
satellite = cas(COL_B, 1435, "Lancer une\nanalyse satellitaire")
# La transmission reglementaire est exercee par le specialiste et consultee
# par les organismes de controle : elle appartient donc a cette bande, ou les
# trois acteurs concernes se trouvent voisins.
transmettre = cas(COL_A, 1510, "Transmettre un\nrapport réglementaire")
# Le referentiel des chantiers et les seuils d'alerte relevent du specialiste
# et non de l'administrateur : ce sont des parametres metier, qui engagent
# l'interpretation environnementale et non l'exploitation du systeme.
config = cas(COL_B, 1585, "Configurer chantiers\net seuils")

# Specialiste Suivi du P.A.R
plaintes = cas(COL_A, 1700, "Traiter les\nplaintes (MGP)")
affecter = cas(COL_B, 1775, "Affecter une\naction corrective")

# Administrateur
users = cas(COL_A, 1960, "Gérer les\nutilisateurs")
types_nuisance = cas(COL_B, 2035, "Paramétrer les\ntypes de nuisance")
modele_ia = cas(COL_A, 2110, "Mettre à jour\nle modèle IA")

# Volet citoyen
deposer = cas(COL_A, 2370, "Déposer une\ndoléance")
suivre_dol = cas(COL_B, 2445, "Suivre ses\ndoléances")


# ─── Acteurs principaux ─────────────────────────────────────────────────
acteurs = [
    (450, "Responsable\nEnvironnement", [saisir, sync, histo, alerte_recue]),
    (760, "Expert HSE", [traiter, valider, sync, alerte_recue]),
    (1150, "Spécialiste Suivi\nEnvironnemental", [bord_cas, gerer_alertes, rapport,
                                                  histo_rapports, export, satellite,
                                                  transmettre, config]),
    # Les organismes de controle suivent immediatement le specialiste dont ils
    # consultent les ecrans : leurs associations restent ainsi courtes, et le
    # voisinage traduit visuellement leur role d'observateurs de son travail.
    (1390, "ANDE", [bord_cas, histo_rapports, satellite, transmettre]),
    (1600, "BAD", [bord_cas, histo_rapports, satellite, transmettre, plaintes]),
    (1830, "Spécialiste\nSuivi du P.A.R", [plaintes, affecter]),
    (2080, "Administrateur", [users, types_nuisance, modele_ia]),
    (2400, "Riverain", [deposer, suivre_dol]),
]
for y, nom, ses_cas in acteurs:
    acteur(X_ACTEURS, y, nom)
    point = (X_ACTEURS + 40, y + 20)
    association(point, auth)          # tous s'authentifient
    for c in ses_cas:
        association(point, c)

tracer_ellipses()
include(saisir, gps_cas)

# ─── Acteurs secondaires ────────────────────────────────────────────────
acteur(X_SECOND, 435, "GPS")
association((X_SECOND - 40, 455), gps_cas)
acteur(X_SECOND, 1415, "Google Earth\nEngine")
association((X_SECOND - 40, 1435), satellite)

CHEMIN = (r"C:\Users\DELL\AppData\Local\Temp\claude"
          r"\d--etude-soutenance-SI-ENV\3233866b-194c-446a-b8f6-65c65b911c25"
          r"\scratchpad\cas_utilisation.png")
img.save(CHEMIN)
print("Image generee :", img.size)
