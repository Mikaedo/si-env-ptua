# -*- coding: utf-8 -*-
"""
Regenere le MLD (figure 4.9), version complete et strictement alignee sur le
schema reel (backend/app/models.py), en coherence avec le MCD corrige :
  - toutes les tables persistees, ALERTESEUIL et JOURNAL compris
  - RAPPORT en est absent : aucune table de ce nom n'existe au schema, le
    rapport produit etant un fichier archive sur le serveur dont seule la
    remise est enregistree, dans TRANSMISSION. Le MCD le represente en
    revanche comme une entite, ce qu'il est au niveau conceptuel
  - suppression d'INDICESATELLITE, calcule a la demande et non persiste
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


def lien_annote(t_source, t_cible, note):
    """Rapprochement logique entre deux tables, sans contrainte d'integrite.

    JOURNAL conserve le login de l'auteur d'une action, mais sous forme de
    libelle recopie et non de cle etrangere : une contrainte ferait disparaitre
    la trace en meme temps que le compte, ce qu'un journal d'audit doit
    justement empecher. Le lien existe donc dans les faits sans exister au
    schema. Le tracer sans le dire laisserait croire a une cle etrangere ;
    ne pas le tracer laisserait la table orpheline. L'annotation leve
    l'ambiguite.
    """
    p1 = t_source.bord(t_cible.centre())
    p2 = t_cible.bord(t_source.centre())
    d.line([p1, p2], fill=FG, width=2)
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    tw = d.textlength(note, font=F_NOTE)
    d.rectangle([mx - tw / 2 - 6, my - 20, mx + tw / 2 + 6, my - 2],
                fill=(255, 255, 255))
    d.text((mx - tw / 2, my - 18), note, font=F_NOTE, fill=FG)


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

# RAPPORT ne figure pas ici. Le modele logique decrit le schema tel qu'il
# existe, et aucune table de ce nom n'y est creee : le rapport produit est un
# fichier archive sur le serveur, dont seule la remise est enregistree, dans
# TRANSMISSION. Le modele conceptuel le represente en revanche comme une
# entite, ce qu'il est a ce niveau d'analyse.

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
                     [], 520, 20, 360)

# Le parametrage des seuils et le journal figuraient au schema sans apparaitre
# au modele logique. ALERTESEUIL porte une cle etrangere nullable vers CHANTIER,
# un seuil pouvant etre global. JOURNAL n en porte aucune : la colonne
# utilisateur y est un libelle recopie, pour que la trace survive au compte.
seuil = Table("ALERTESEUIL", "idSeuil",
              ["nom", "indicateur", "seuil", "operateur", "actif"],
              ["idChantier (nullable)"], 1500, 500, 340)

journal = Table("JOURNAL", "idJournal",
                ["niveau", "message", "utilisateurLogin", "ipSource", "horodatage"],
                [], 520, 330, 340)

tables = [util, chantier, plainte, signalement, alerte, photo, action, nc,
          transmission, seuil, journal]
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
relation_fk(plainte, util)
relation_fk(util, chantier)
relation_fk(seuil, chantier)
# Les tables sont tracees avant les liaisons : celles qui rejoignent
# UTILISATEUR depuis le bas du schema passaient donc par-dessus JOURNAL, place
# sur leur trajet. La redessiner en dernier laisse son fond blanc les masquer,
# et sa liaison est retracee ensuite pour rester visible.
journal.draw()
relation_fk(journal, util)
# TRANSMISSION ne porte aucune cle etrangere : ni vers le rapport, qui n'a pas
# de table, ni vers son emetteur, conserve en adresse pour que la trace survive
# a la suppression du compte. Elle se rattache neanmoins a UTILISATEUR par le
# meme trait que JOURNAL, qui est dans la situation identique : la note du bas
# explique pour les deux que ce rapprochement ne porte pas de contrainte.
#
# Les deux boites sont redessinees en dernier. Les tables etant tracees avant
# les liaisons, celles qui remontent du bas passaient par-dessus elles ; leur
# fond blanc les masque desormais.
journal.draw()
transmission.draw()
relation_fk(transmission, util)

d.text((20, H - 90),
      "Note : la spécialisation d'UTILISATEUR en huit sous-types (cf. figure 4.8) est résolue en table unique",
      font=F_NOTE, fill=FG)
d.text((20, H - 70),
      "avec discriminant (colonne role), conformément au modèle Utilisateur du code (backend/app/models.py).",
      font=F_NOTE, fill=FG)
d.text((20, H - 48),
      "Chaque table ne porte que des attributs dépendant uniquement de sa clé primaire (aucune dépendance transitive) : le MLD est déjà en 3NF.",
      font=F_NOTE, fill=FG)
# JOURNAL et TRANSMISSION conservent le login ou l'adresse de leur auteur en
# clair plutot qu'en cle etrangere : une contrainte ferait disparaitre la trace
# en meme temps que le compte, ce qu'un journal d'audit doit justement empecher.
d.text((20, H - 108),
      "JOURNAL et TRANSMISSION conservent le login ou l'adresse de leur auteur en clair, sans contrainte d'intégrité : la trace doit survivre à la suppression du compte.",
      font=F_NOTE, fill=FG)
d.text((20, H - 25),
      "Légende : # clé primaire · ## clé étrangère (trait plein = référence FK)",
      font=F_LEGEND, fill=FG)

img.save(r"C:\Users\DELL\AppData\Local\Temp\claude\d--etude-soutenance-SI-ENV\3233866b-194c-446a-b8f6-65c65b911c25\scratchpad\mld_regenere.png")
print("Image generee.")
