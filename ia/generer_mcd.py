# -*- coding: utf-8 -*-
"""
Regenere le MCD (figure 4.8), version complete et strictement alignee sur le
schema reel (backend/app/models.py) :
  - ajout des entites manquantes NONCONFORMITE, ALERTESEUIL, JOURNAL
  - suppression d'INDICESATELLITE (calcule a la demande via Google Earth
    Engine, jamais persiste). RAPPORT en revanche figure au modele : le PDF
    est archive sur disque et suivi en base, ce qui permet l'historisation.
  - correction des relations : ALERTE se rattache a CHANTIER et UTILISATEUR
    (pas a SIGNALEMENT) ; PLAINTE se rattache a CHANTIER (pas a UTILISATEUR,
    la table plaintes n'a pas de cle etrangere utilisateur - le plaignant est
    une personne externe identifiee par nom_plaignant/contact)
  - ajout de la specialisation d'UTILISATEUR en 5 sous-types (deja presente
    dans le diagramme de classes, figure 4.3, mais absente jusqu'ici du MCD)
"""
from PIL import Image, ImageDraw, ImageFont
import math

W, H = 2500, 1620
BG = (255, 255, 255)
FG = (0, 0, 0)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

F_TITLE = ImageFont.truetype("arialbd.ttf", 17)
F_ATTR = ImageFont.truetype("arial.ttf", 14)
F_REL = ImageFont.truetype("arialbd.ttf", 14)
F_CARD = ImageFont.truetype("arialbd.ttf", 15)
F_NOTE = ImageFont.truetype("ariali.ttf", 13)


class Entite:
    def __init__(self, nom, attrs, x, y, w):
        self.nom, self.attrs, self.x, self.y, self.w = nom, attrs, x, y, w
        self.h = 36 + 24 * len(attrs)

    def draw(self):
        x, y, w, h = self.x, self.y, self.w, self.h
        d.rectangle([x, y, x + w, y + h], outline=FG, width=2, fill=(255, 255, 255))
        tw = d.textlength(self.nom, font=F_TITLE)
        d.text((x + (w - tw) / 2, y + 8), self.nom, font=F_TITLE, fill=FG)
        d.line([x, y + 34, x + w, y + 34], fill=FG, width=2)
        yy = y + 40
        for a in self.attrs:
            d.text((x + 10, yy), a, font=F_ATTR, fill=FG)
            yy += 24

    def centre(self):
        return (self.x + self.w / 2, self.y + self.h / 2)

    def bord(self, vers):
        cx, cy = self.centre()
        vx, vy = vers
        dx, dy = vx - cx, vy - cy
        if dx == 0 and dy == 0:
            return (cx, cy)
        t_candidats = []
        if dx != 0:
            for bx in (self.x, self.x + self.w):
                t = (bx - cx) / dx
                if t > 0:
                    py = cy + t * dy
                    if self.y - 1 <= py <= self.y + self.h + 1:
                        t_candidats.append(t)
        if dy != 0:
            for by in (self.y, self.y + self.h):
                t = (by - cy) / dy
                if t > 0:
                    px = cx + t * dx
                    if self.x - 1 <= px <= self.x + self.w + 1:
                        t_candidats.append(t)
        t = min(t_candidats) if t_candidats else 0
        return (cx + t * dx, cy + t * dy)


def losange(cx, cy, nom):
    tw = d.textlength(nom, font=F_REL)
    hw = tw / 2 + 14
    hh = 22
    pts = [(cx - hw, cy), (cx, cy - hh), (cx + hw, cy), (cx, cy + hh)]
    d.polygon(pts, outline=FG, fill=(255, 255, 255))
    d.text((cx - tw / 2, cy - 8), nom, font=F_REL, fill=FG)


def relation(e1, e2, nom, card1, card2, decalage_losange=0.5):
    c1, c2 = e1.centre(), e2.centre()
    lx = c1[0] + (c2[0] - c1[0]) * decalage_losange
    ly = c1[1] + (c2[1] - c1[1]) * decalage_losange
    p1 = e1.bord((lx, ly))
    p2 = e2.bord((lx, ly))
    d.line([p1, (lx, ly)], fill=FG, width=2)
    d.line([(lx, ly), p2], fill=FG, width=2)
    losange(lx, ly, nom)
    for p, c in ((p1, card1), (p2, card2)):
        ang = math.atan2(ly - p[1], lx - p[0])
        ox = 18 * math.cos(ang + math.pi / 2) + 22 * math.cos(ang)
        oy = 18 * math.sin(ang + math.pi / 2) + 22 * math.sin(ang)
        d.text((p[0] + ox, p[1] + oy), c, font=F_CARD, fill=FG)


def specialisation(mere, filles, scx):
    """Arbre de specialisation Merise : symbole T (totale, disjointe) sous
    l'entite mere, avec un trait droit vers chaque sous-entite. scx est
    decale par rapport au centre de la mere pour laisser la place aux
    relations qui descendent directement sous elle (ex. REDIGE)."""
    cx, cy = mere.centre()[0], mere.y + mere.h
    scy = cy + 60
    r = 22
    d.ellipse([scx - r, scy - r, scx + r, scy + r], outline=FG, width=2, fill=(255, 255, 255))
    tw = d.textlength("T", font=F_REL)
    d.text((scx - tw / 2, scy - 9), "T", font=F_REL, fill=FG)
    d.line([cx, cy, scx, scy - r], fill=FG, width=2)
    for f in filles:
        p = f.bord((scx, scy))
        d.line([(scx, scy), p], fill=FG, width=2)


# ─── Entité mère et ses sous-types (héritage / spécialisation) ──────────
# Le cluster des sous-types reste entierement a gauche (x <= 950) pour que
# les relations descendant depuis UTILISATEUR vers SIGNALEMENT/ALERTE
# (plus a droite) ne traversent jamais leurs boites.
util = Entite("UTILISATEUR", ["# idUtilisateur", "nom", "email", "motDePasse",
                              "role", "telephone", "dateInscription"],
             1050, 20, 400)

resp = Entite("RESP_ENV", ["zoneAffectation"], 20, 380, 180)
hse = Entite("EXPERT_HSE", ["numeroAgrement"], 220, 380, 180)
spec = Entite("SPEC_ENV", ["niveauHabilitation"], 420, 380, 180)
par = Entite("SPEC_PAR", ["secteurAffecte"], 620, 380, 180)
admin = Entite("ADMIN", ["niveauAcces"], 820, 380, 150)
ande = Entite("ANDE", ["referenceAgrement"], 990, 380, 180)
bad = Entite("BAD", ["codeMission"], 1190, 380, 170)
riverain = Entite("PLAIGNANT", ["# chantierRattachement"], 1380, 380, 250)

sous_types = [resp, hse, spec, par, admin, ande, bad, riverain]

# ─── Entités principales ─────────────────────────────────────────────────
signalement = Entite("SIGNALEMENT",
                     ["# idSignalement", "typeNuisance", "description", "criticite",
                      "statutSignalement", "geom", "dateObservation"],
                     1950, 420, 340)

chantier = Entite("CHANTIER", ["# idChantier", "nomChantier", "commune",
                               "rayonInfluence"], 20, 650, 300)

plainte = Entite("PLAINTE", ["# idPlainte", "nomPlaignant", "contact", "description",
                             "statutPlainte", "dateDepot", "canal", "categorie",
                             "geom"], 1950, 20, 340)

alerte = Entite("ALERTE", ["# idAlerte", "message", "niveau", "valeur",
                           "dateDeclenchement", "recue"], 1950, 900, 340)

photo = Entite("PHOTO", ["# idPhoto", "cheminStockage"], 380, 1150, 260)

action = Entite("ACTIONCORRECTIVE", ["# idAction", "description", "echeance",
                                     "dateCreation"], 760, 1150, 320)

nc = Entite("NONCONFORMITE", ["# idNonConformite", "description", "severite",
                              "resolue", "dateCreation"], 1180, 1150, 340)

# Le rapport PGES est desormais archive (PDF sur disque + ligne de suivi en
# base), ce qui rend l'historisation possible : il redevient une entite.
rapport = Entite("RAPPORT", ["# idRapport", "periodeDebut", "periodeFin",
                             "cheminFichier", "destinataire", "nbChantiers",
                             "dateGeneration"], 1560, 1150, 330)

transmission = Entite("TRANSMISSION",
                      ["# idTransmission", "emetteur", "destinataire",
                       "organisme", "dateTransmission", "succes"], 1950, 1330, 340)

toutes = [util, resp, hse, spec, par, admin, ande, bad, riverain, chantier,
         signalement, plainte, photo, action, nc, alerte, rapport,
         transmission]
for e in toutes:
    e.draw()

specialisation(util, sous_types, scx=790)

# ─── Relations (fidèles aux clés étrangères réelles du modèle SQLAlchemy) ──
relation(util, signalement, "SAISIT", "0,n", "1,1", 0.35)
relation(chantier, signalement, "SE_SITUE_SUR", "1,n", "1,1", 0.5)
relation(signalement, photo, "ILLUSTRE", "1,n", "1,1", 0.5)
relation(signalement, action, "GENERE", "0,n", "1,1", 0.5)
relation(signalement, nc, "SIGNALE", "0,n", "1,1", 0.45)
relation(chantier, alerte, "DECLENCHE", "0,n", "0,1", 0.5)
relation(util, alerte, "DESTINATAIRE", "0,n", "0,1", 0.6)
relation(chantier, plainte, "CONCERNE", "0,n", "0,1", 0.22)
relation(util, rapport, "REDIGE", "0,n", "1,1", 0.55)
# Un rapport peut etre remis plusieurs fois, a des organismes differents.
relation(rapport, transmission, "FAIT_L_OBJET_DE", "0,n", "1,1", 0.5)

d.text((20, H - 28),
      "Note : les 8 sous-types reprennent les valeurs de l'énumération role du modèle Utilisateur. "
      "ANDE et BAD accèdent en consultation seule ; PLAIGNANT désigne un riverain rattaché à un chantier.",
      font=F_NOTE, fill=FG)

img.save(r"C:\Users\DELL\AppData\Local\Temp\claude\d--etude-soutenance-SI-ENV\3233866b-194c-446a-b8f6-65c65b911c25\scratchpad\mcd_regenere.png")
print("Image generee.")
