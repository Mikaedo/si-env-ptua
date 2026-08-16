# -*- coding: utf-8 -*-
"""
Regenere le MLD (figure 4.9), version complete et strictement alignee sur le
schema reel (backend/app/models.py), en coherence avec le MCD corrige :
  - memes entites persistees que le MCD (hors ALERTESEUIL/JOURNAL, retirees
    des deux diagrammes car sans lien avec le reste du modele)
  - suppression d'INDICESATELLITE (non persiste) ; RAPPORT est present,
    le PDF etant archive sur disque et suivi en base (historisation)
  - correction des cles etrangeres : alertes.chantier_id / alertes.utilisateur_id
    (pas de FK vers signalement) ; plaintes.chantier_id (pas de FK utilisateur)
  - la specialisation d'UTILISATEUR (visible au niveau conceptuel du MCD) est
    resolue ici en une table unique avec discriminant (colonne role), fidele
    a l'implementation reelle (un seul modele Utilisateur, role: RoleEnum)
  - traits pleins, sans pointe de fleche
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 2350, 1450
BG = (255, 255, 255)
FG = (0, 0, 0)
ORANGE = (196, 90, 17)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

F_TITLE = ImageFont.truetype("arialbd.ttf", 16)
F_PK = ImageFont.truetype("arialbd.ttf", 14)
F_ATTR = ImageFont.truetype("arial.ttf", 14)
F_FK = ImageFont.truetype("arialbd.ttf", 14)
F_LEGEND = ImageFont.truetype("ariali.ttf", 13)
F_NOTE = ImageFont.truetype("ariali.ttf", 13)


class Table:
    def __init__(self, nom, pk, attrs, fks, x, y, w):
        self.nom, self.pk, self.attrs, self.fks = nom, pk, attrs, fks
        self.x, self.y, self.w = x, y, w
        self.h = 34 + 22 * (1 + len(attrs) + len(fks)) + 6

    def draw(self):
        x, y, w, h = self.x, self.y, self.w, self.h
        d.rectangle([x, y, x + w, y + h], outline=FG, width=2, fill=(255, 255, 255))
        tw = d.textlength(self.nom, font=F_TITLE)
        d.text((x + (w - tw) / 2, y + 9), self.nom, font=F_TITLE, fill=FG)
        y0 = y + 34
        d.line([x, y0, x + w, y0], fill=FG, width=1)
        yy = y0 + 4
        d.text((x + 8, yy), "# " + self.pk, font=F_PK, fill=FG)
        yy += 22
        for a in self.attrs:
            d.text((x + 8, yy), a, font=F_ATTR, fill=FG)
            yy += 22
        for fk in self.fks:
            d.text((x + 8, yy), "## " + fk, font=F_FK, fill=ORANGE)
            yy += 22

    def centre(self):
        return (self.x + self.w / 2, self.y + self.h / 2)

    def bord(self, vers):
        cx, cy = self.centre()
        vx, vy = vers
        dx, dy = vx - cx, vy - cy
        if dx == 0 and dy == 0:
            return (cx, cy)
        candidats = []
        if dx != 0:
            for bx in (self.x, self.x + self.w):
                t = (bx - cx) / dx
                if t > 0:
                    py = cy + t * dy
                    if self.y - 1 <= py <= self.y + self.h + 1:
                        candidats.append(t)
        if dy != 0:
            for by in (self.y, self.y + self.h):
                t = (by - cy) / dy
                if t > 0:
                    px = cx + t * dx
                    if self.x - 1 <= px <= self.x + self.w + 1:
                        candidats.append(t)
        t = min(candidats) if candidats else 0
        return (cx + t * dx, cy + t * dy)


def relation_fk(t_source, t_cible):
    p1 = t_source.bord(t_cible.centre())
    p2 = t_cible.bord(t_source.centre())
    d.line([p1, p2], fill=FG, width=2)


# ─── Tables (deux « hubs » en haut, references par plusieurs tables) ────
util = Table("UTILISATEUR", "idUtilisateur",
             ["nom", "email", "motDePasseHash", "role", "premiereConnexion",
              "telephone", "dateInscription", "tokenInvitation",
              "tokenInvitationExpire", "twofaEmailActif"],
             ["idChantierRattachement (nullable)"],
             20, 20, 360)

chantier = Table("CHANTIER", "idChantier",
                 ["nom", "commune", "geom", "rayonInfluence"], [],
                 1900, 20, 300)

# Archive des rapports de suivi : place en haut, a cote d'UTILISATEUR, pour que le
# trait de sa cle etrangere reste court et ne traverse aucune autre table.
rapport = Table("RAPPORT", "idRapport",
               ["periodeDebut", "periodeFin", "cheminFichier", "destinataire",
                "nbChantiers", "dateGeneration"],
               ["idUtilisateur"], 520, 20, 360)

plainte = Table("PLAINTE", "idPlainte",
                ["nomPlaignant", "contact", "description", "statut", "dateCreation",
                 "canal", "categorie", "geom"],
                ["idChantier (nullable)", "idPlaignant (nullable)"], 20, 500, 340)

signalement = Table("SIGNALEMENT", "idSignalement",
                    ["uuidMobile", "typeNuisance", "description", "criticite",
                     "criticiteIA", "confianceIA", "gpsSource", "statut", "geom",
                     "dateCreation"],
                    ["idUtilisateur", "idChantier"], 950, 500, 380)

alerte = Table("ALERTE", "idAlerte",
              ["message", "niveau", "valeur", "dateCreation", "recue"],
              ["idChantier", "idUtilisateur (nullable)"], 1900, 500, 340)

photo = Table("PHOTO", "idPhoto", ["chemin"], ["idSignalement"], 400, 950, 280)

action = Table("ACTIONCORRECTIVE", "idAction",
              ["description", "echeance", "dateCreation"],
              ["idSignalement"], 750, 950, 320)

nc = Table("NONCONFORMITE", "idNonConformite",
          ["description", "severite", "resolue", "dateCreation"],
          ["idSignalement"], 1140, 950, 340)

# La trace de remise ne reference pas son emetteur par une cle etrangere :
# elle conserve son adresse en clair afin de survivre a la suppression du
# compte, sans quoi la preuve disparaitrait avec son auteur.
transmission = Table("TRANSMISSION", "idTransmission",
                     ["emetteurEmail", "destinataireEmail", "organisme",
                      "periodeDebut", "periodeFin", "chantiers", "nomFichier",
                      "tailleOctets", "succes", "dateTransmission"],
                     [], 1560, 950, 360)

tables = [util, chantier, plainte, signalement, alerte, photo, action, nc,
          rapport, transmission]
for t in tables:
    t.draw()

# ─── Références de clé étrangère (trait plein, fidèles au modèle SQLAlchemy) ──
relation_fk(plainte, chantier)
relation_fk(signalement, util)
relation_fk(signalement, chantier)
relation_fk(alerte, chantier)
relation_fk(alerte, util)
relation_fk(photo, signalement)
relation_fk(action, signalement)
relation_fk(nc, signalement)
relation_fk(rapport, util)
relation_fk(plainte, util)
relation_fk(util, chantier)

d.text((20, H - 90),
      "Note : la spécialisation d'UTILISATEUR en huit sous-types (cf. figure 4.8) est résolue en table unique",
      font=F_NOTE, fill=FG)
d.text((20, H - 70),
      "avec discriminant (colonne role), conformément au modèle Utilisateur du code (backend/app/models.py).",
      font=F_NOTE, fill=FG)
d.text((20, H - 48),
      "Chaque table ne porte que des attributs dépendant uniquement de sa clé primaire (aucune dépendance transitive) : le MLD est déjà en 3NF.",
      font=F_NOTE, fill=FG)
d.text((20, H - 25),
      "Légende : # clé primaire · ## clé étrangère (trait plein = référence FK)",
      font=F_LEGEND, fill=FG)

img.save(r"C:\Users\DELL\AppData\Local\Temp\claude\d--etude-soutenance-SI-ENV\3233866b-194c-446a-b8f6-65c65b911c25\scratchpad\mld_regenere.png")
print("Image generee.")
