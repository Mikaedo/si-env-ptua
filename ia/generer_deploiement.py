# -*- coding: utf-8 -*-
"""
Regenere le diagramme de deploiement (figure 4.7).

Aucun script source n'existait pour cette figure, et l'image en place decrivait
un dispositif a trois composants applicatifs. Il en compte quatre depuis que
l'application citoyenne a ete separee de celle des agents : les deux sont
issues du meme depot mais se deploient independamment, avec des identifiants
distincts, et ne peuvent donc pas figurer comme un seul artefact.

Le diagramme distingue deux zones. A gauche, les terminaux des utilisateurs,
qui n'hebergent que du logiciel client. A droite, l'infrastructure, elle-meme
partagee entre ce qui est heberge pour le projet et les services externes
sollicites. Cette separation compte pour la lecture : elle montre qu'aucune
donnee du projet ne reside sur un terminal en dehors du cache de
synchronisation, et que les dependances externes se limitent a deux services
interroges en lecture.

Convention UML retenue : les noeuds sont des parallelepipedes, les artefacts
qu'ils hebergent des rectangles simples marques du stereotype correspondant,
et les liens de communication portent le protocole employe.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 2400, 1500
BLANC = (255, 255, 255)
FG = (0, 0, 0)
GRIS = (110, 110, 110)
FOND_ZONE = (248, 248, 250)

img = Image.new("RGB", (W, H), BLANC)
d = ImageDraw.Draw(img)

F_NOEUD = ImageFont.truetype("arialbd.ttf", 23)
F_ART = ImageFont.truetype("arial.ttf", 20)
F_STEREO = ImageFont.truetype("ariali.ttf", 17)
F_LIEN = ImageFont.truetype("arial.ttf", 18)
F_ZONE = ImageFont.truetype("arialbd.ttf", 21)

PROF = 26          # profondeur de la perspective des noeuds


def zone(x1, y1, x2, y2, titre):
    """Cadre pointille regroupant des noeuds de meme nature."""
    pas = 14
    for x in range(x1, x2, pas * 2):
        d.line([x, y1, min(x + pas, x2), y1], fill=GRIS, width=2)
        d.line([x, y2, min(x + pas, x2), y2], fill=GRIS, width=2)
    for y in range(y1, y2, pas * 2):
        d.line([x1, y, x1, min(y + pas, y2)], fill=GRIS, width=2)
        d.line([x2, y, x2, min(y + pas, y2)], fill=GRIS, width=2)
    d.text((x1 + 16, y1 + 12), titre, font=F_ZONE, fill=GRIS)


def noeud(x, y, larg, haut, nom, artefacts, stereotype="device"):
    """Noeud UML en perspective, avec les artefacts qu'il heberge."""
    # Face avant
    d.rectangle([x, y, x + larg, y + haut], outline=FG, width=3, fill=BLANC)
    # Aretes de profondeur
    d.line([x, y, x + PROF, y - PROF], fill=FG, width=3)
    d.line([x + larg, y, x + larg + PROF, y - PROF], fill=FG, width=3)
    d.line([x + larg, y + haut, x + larg + PROF, y + haut - PROF], fill=FG, width=3)
    d.line([x + PROF, y - PROF, x + larg + PROF, y - PROF], fill=FG, width=3)
    d.line([x + larg + PROF, y - PROF, x + larg + PROF, y + haut - PROF], fill=FG, width=3)

    st = f"« {stereotype} »"
    tw = d.textlength(st, font=F_STEREO)
    d.text((x + larg / 2 - tw / 2, y + 12), st, font=F_STEREO, fill=GRIS)
    tw = d.textlength(nom, font=F_NOEUD)
    d.text((x + larg / 2 - tw / 2, y + 34), nom, font=F_NOEUD, fill=FG)

    # Artefacts heberges
    ay = y + 76
    for libelle, stereo_art in artefacts:
        d.rectangle([x + 22, ay, x + larg - 22, ay + 62], outline=FG, width=2, fill=BLANC)
        s = f"« {stereo_art} »"
        tw = d.textlength(s, font=F_STEREO)
        d.text((x + larg / 2 - tw / 2, ay + 7), s, font=F_STEREO, fill=GRIS)
        tw = d.textlength(libelle, font=F_ART)
        d.text((x + larg / 2 - tw / 2, ay + 30), libelle, font=F_ART, fill=FG)
        ay += 76

    return (x, y, x + larg, y + haut)


def lien(b1, b2, protocole, cote="h"):
    """Lien de communication entre deux noeuds, avec son protocole."""
    if cote == "h":
        x1, y1 = b1[2], (b1[1] + b1[3]) / 2
        x2, y2 = b2[0], (b2[1] + b2[3]) / 2
    else:
        x1, y1 = (b1[0] + b1[2]) / 2, b1[3]
        x2, y2 = (b2[0] + b2[2]) / 2, b2[1]
    d.line([x1, y1, x2, y2], fill=FG, width=3)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    tw = d.textlength(protocole, font=F_LIEN)
    # Le libelle est pose sur un fond blanc pour rester lisible par-dessus
    # le trait qu'il accompagne.
    d.rectangle([mx - tw / 2 - 6, my - 26, mx + tw / 2 + 6, my - 2], fill=BLANC)
    d.text((mx - tw / 2, my - 24), protocole, font=F_LIEN, fill=FG)


# ─── Zones ──────────────────────────────────────────────────────────────
zone(40, 90, 700, 1240, "Postes et terminaux des utilisateurs")
zone(880, 90, 1600, 1110, "Hébergement du projet")
zone(1760, 90, 2360, 900, "Services externes")

# ─── Terminaux ──────────────────────────────────────────────────────────
agent = noeud(90, 190, 520, 160,
              "Terminal Android (agent AGEROUTE)",
              [("SI-ENV agent (APK)", "artefact"),
               ("Base locale SQLite", "artefact")])

citoyen = noeud(90, 560, 520, 160,
                "Terminal Android (riverain)",
                [("SI-ENV Citoyen (APK)", "artefact")])

poste = noeud(90, 900, 520, 160,
              "Poste de travail",
              [("Navigateur web", "artefact")])

# ─── Hebergement ────────────────────────────────────────────────────────
serveur = noeud(930, 190, 560, 240,
                "Serveur d'application",
                [("API FastAPI / Uvicorn", "artefact"),
                 ("Modèles ONNX", "artefact")],
                stereotype="execution environment")

bdd = noeud(930, 590, 560, 160,
            "Serveur de données",
            [("PostgreSQL + PostGIS", "artefact")],
            stereotype="database")

# Le tableau de bord est distribue depuis un reseau de diffusion : il ne
# s'execute nulle part cote serveur, ce que le stereotype traduit.
cdn = noeud(930, 900, 560, 160,
            "Réseau de diffusion",
            [("Tableau de bord Angular", "artefact")],
            stereotype="device")

# ─── Services externes ──────────────────────────────────────────────────
gee = noeud(1800, 190, 500, 160,
            "Google Earth Engine",
            [("Imagerie satellitaire", "service")],
            stereotype="external")

mail = noeud(1800, 560, 500, 160,
             "Service de messagerie",
             [("Envoi transactionnel", "service")],
             stereotype="external")

# ─── Liens de communication ─────────────────────────────────────────────
lien(agent, serveur, "HTTPS / REST")
lien(citoyen, serveur, "HTTPS / REST")
lien(poste, cdn, "HTTPS (chargement)")
lien(serveur, bdd, "TCP 5432 / SSL", cote="v")
lien(serveur, gee, "HTTPS / API")
lien(serveur, mail, "HTTPS / API")

# Le tableau de bord, une fois charge dans le navigateur, appelle l'API et
# non la base. Le trait contourne le serveur de donnees par la droite : un
# segment vertical direct aboutirait a la base, qui s'intercale entre les
# deux, et laisserait croire a un acces direct depuis le navigateur.
PARCOURS = [(1520, 980), (1560, 980), (1560, 340), (1490, 340)]
for i in range(len(PARCOURS) - 1):
    d.line([PARCOURS[i], PARCOURS[i + 1]], fill=FG, width=3)
tw = d.textlength("HTTPS / REST", font=F_LIEN)
d.rectangle([1572, 648, 1572 + tw + 12, 674], fill=BLANC)
d.text((1578, 650), "HTTPS / REST", font=F_LIEN, fill=FG)

# ─── Note ───────────────────────────────────────────────────────────────
note = ("Note : les deux applications mobiles proviennent d'un même dépôt de code et partagent le service d'accès à l'API, "
        "les modèles de données et la géolocalisation. Elles sont compilées en deux variantes distinctes, "
        "porteuses d'identifiants applicatifs différents, et s'installent côte à côte sur un même terminal.")
d.text((40, 1330), note[:118], font=F_LIEN, fill=GRIS)
d.text((40, 1358), note[118:236], font=F_LIEN, fill=GRIS)
d.text((40, 1386), note[236:], font=F_LIEN, fill=GRIS)

CHEMIN = (r"C:\Users\DELL\AppData\Local\Temp\claude"
          r"\d--etude-soutenance-SI-ENV\3233866b-194c-446a-b8f6-65c65b911c25"
          r"\scratchpad\deploiement.png")
img.save(CHEMIN)
print("Image generee :", img.size)
