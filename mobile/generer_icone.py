# -*- coding: utf-8 -*-
"""
Genere l'icone de lancement de l'application mobile SI-ENV.

L'application portait encore l'icone par defaut de Flutter.

Choix du motif. Une premiere version juxtaposait une feuille et une chaussee :
a 48 px, les deux formes se disputaient la place et la feuille symetrique se
lisait comme un ballon. Le motif retenu ne presente donc qu'une seule
silhouette, le reperage cartographique, qui resume l'acte central de
l'application : signaler une nuisance geolocalisee. Le volet environnemental
tient dans la feuille posee au centre du repere.

Les trois couches (repere blanc, pastille orange, feuille blanche) sont
concentriques : la silhouette percue reste unique quelle que soit la taille,
alors qu'une forme rapportee a cote du repere aurait ajoute un contour a
dechiffrer.

La feuille est volontairement asymetrique, base arrondie et pointe franche,
sinon elle ne se lit pas comme une feuille.

Charte AGEROUTE : bleu #004F9F, bleu fonce #003063, orange #F37021.
Tout est trace a 8x puis reduit en LANCZOS.

Sorties :
  - res/mipmap-*/ic_launcher.png             icone historique (48 a 192 px)
  - res/mipmap-*/ic_launcher_foreground.png  calque avant de l'icone adaptative
  - res/mipmap-anydpi-v26/ic_launcher.xml    icone adaptative Android 8+
  - res/values/ic_launcher_background.xml    couleur du calque arriere
  - icone_si_env_512.png                     version haute definition
"""
import math
import os

from PIL import Image, ImageDraw

BLEU = (0, 79, 159)
BLEU_FONCE = (0, 48, 99)
ORANGE = (243, 112, 33)
BLANC = (255, 255, 255)

SS = 8          # facteur de surechantillonnage
BASE = 512      # cote de reference du dessin

ANDROID = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "android", "app", "src", "main", "res")

DENSITES = [
    ("mipmap-mdpi",    48,  108),
    ("mipmap-hdpi",    72,  162),
    ("mipmap-xhdpi",   96,  216),
    ("mipmap-xxhdpi",  144, 324),
    ("mipmap-xxxhdpi", 192, 432),
]


def _degrade(d, cote):
    for y in range(cote):
        t = y / max(1, cote - 1)
        c = tuple(round(BLEU[i] + (BLEU_FONCE[i] - BLEU[i]) * t) for i in range(3))
        d.line([(0, y), (cote, y)], fill=c)


def _repere(d, cx, cy, larg, haut, couleur):
    """Trace le repere cartographique comme reunion d'un disque et d'un triangle.

    Une premiere version calculait un contour unique par arc parametre ; le sens
    de parcours se refermait mal et la silhouette se scindait en deux ailes. La
    reunion de deux primitives est plus sure et donne le meme resultat.

    Les coins du triangle sont pris aux points de tangence depuis la pointe, de
    sorte que les flancs prolongent le disque sans cassure visible. Retourne le
    centre et le rayon du disque, pour y inscrire le motif interieur.
    """
    r = larg / 2.0
    centre_y = cy - haut / 2.0 + r
    pointe_y = cy + haut / 2.0
    dist = max(pointe_y - centre_y, r * 1.001)
    alpha = math.asin(r / dist)
    # tangentes depuis la pointe : direction centre -> pointe verticale, donc
    # les points de contact sont a +-(90 - alpha) de cette direction.
    tx, ty = r * math.cos(alpha), r * math.sin(alpha)

    d.ellipse([cx - r, centre_y - r, cx + r, centre_y + r], fill=couleur)
    d.polygon([(cx - tx, centre_y + ty), (cx + tx, centre_y + ty), (cx, pointe_y)],
              fill=couleur)
    return cx, centre_y, r


def _feuille(cx, cy, longueur, largeur, angle_deg):
    """Feuille asymetrique : base arrondie, pointe franche.

    L'enveloppe de demi-largeur est deformee par t**0.68, ce qui repousse le
    maximum vers la base ; les deux flancs recoivent des exposants differents
    pour eviter la symetrie parfaite qui faisait lire un ballon.
    """
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    gauche, droite = [], []
    PAS = 260
    for i in range(PAS + 1):
        t = i / PAS
        s = (t - 0.46) * longueur
        env = math.sin(math.pi * (t ** 0.68))
        wg = (largeur / 2) * env ** 0.80
        wd = (largeur / 2) * env ** 1.05
        px, py = cx + ux * s, cy + uy * s
        gauche.append((px + nx * wg, py + ny * wg))
        droite.append((px - nx * wd, py - ny * wd))
    return gauche + droite[::-1]


def dessiner(cote, transparent=False, marge=0.0):
    grand = cote * SS
    img = Image.new("RGBA" if transparent else "RGB", (grand, grand),
                    (0, 0, 0, 0) if transparent else BLEU)
    d = ImageDraw.Draw(img)
    if not transparent:
        _degrade(d, grand)

    k = grand / BASE * (1.0 - marge)
    cx, cy = grand / 2, grand / 2

    # ── Repere cartographique, blanc ───────────────────────────────────────
    hcx, hcy, r = _repere(d, cx, cy - 22 * k, 300 * k, 400 * k, BLANC)

    # ── Pastille orange inscrite dans la tete du repere ────────────────────
    # Les trois couches restent concentriques : la silhouette percue demeure
    # unique, et la charte garde ses deux couleurs jusqu'a 48 px.
    rp = r * 0.72
    d.ellipse([hcx - rp, hcy - rp, hcx + rp, hcy + rp], fill=ORANGE)

    # ── Feuille blanche posee sur la pastille ──────────────────────────────
    d.polygon(_feuille(hcx + 2 * k, hcy + 4 * k, rp * 1.50, rp * 0.94, -58),
              fill=BLANC)
    # Nervure, tracee dans l'orange de la pastille : elle structure la feuille
    # sans ajouter de troisieme teinte.
    a = math.radians(-58)
    ux, uy = math.cos(a), math.sin(a)
    s0, s1 = -0.30 * rp * 1.50, 0.26 * rp * 1.50
    d.line([(hcx + 2 * k + ux * s0, hcy + 4 * k + uy * s0),
            (hcx + 2 * k + ux * s1, hcy + 4 * k + uy * s1)],
           fill=ORANGE, width=max(1, int(9 * k)))

    img = img.resize((cote, cote), Image.LANCZOS)

    if not transparent:
        r = int(cote * 0.22)
        m = Image.new("L", (cote * 4, cote * 4), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, cote * 4 - 1, cote * 4 - 1],
                                           radius=r * 4, fill=255)
        m = m.resize((cote, cote), Image.LANCZOS)
        sortie = Image.new("RGBA", (cote, cote), (0, 0, 0, 0))
        sortie.paste(img, (0, 0), m)
        return sortie
    return img


def main():
    racine = os.path.dirname(os.path.abspath(__file__))
    dessiner(512).save(os.path.join(racine, "icone_si_env_512.png"))

    for dossier, cote_icone, cote_avant in DENSITES:
        chemin = os.path.join(ANDROID, dossier)
        os.makedirs(chemin, exist_ok=True)
        dessiner(cote_icone).save(os.path.join(chemin, "ic_launcher.png"))
        dessiner(cote_avant, transparent=True, marge=0.30).save(
            os.path.join(chemin, "ic_launcher_foreground.png"))

    anydpi = os.path.join(ANDROID, "mipmap-anydpi-v26")
    os.makedirs(anydpi, exist_ok=True)
    with open(os.path.join(anydpi, "ic_launcher.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n'
                '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                '    <background android:drawable="@color/ic_launcher_background" />\n'
                '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n'
                '</adaptive-icon>\n')

    valeurs = os.path.join(ANDROID, "values")
    os.makedirs(valeurs, exist_ok=True)
    with open(os.path.join(valeurs, "ic_launcher_background.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n'
                '<resources>\n'
                '    <color name="ic_launcher_background">#004F9F</color>\n'
                '</resources>\n')

    print("Icones generees dans", ANDROID)


if __name__ == "__main__":
    main()
