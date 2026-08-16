# -*- coding: utf-8 -*-
"""
Diagramme de classes (figure 4.3) en lignes droites simples (pas de detours
en escalier) : chaque relation part du bord d'une boite, va directement au
bord de l'autre, avec les multiplicites aux deux extremites et le verbe au
milieu. Les croisements eventuels sont acceptes, comme sur un diagramme UML
dessine a la main.
"""
from PIL import Image, ImageDraw, ImageFont
import math

W, H = 2680, 1450
BG = (255, 255, 255)
FG = (0, 0, 0)
LINE_W = 2

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

F_TITLE = ImageFont.truetype("arialbd.ttf", 17)
F_ATTR = ImageFont.truetype("arial.ttf", 14)
F_LABEL = ImageFont.truetype("ariali.ttf", 14)
F_CARD = ImageFont.truetype("arial.ttf", 14)


class Box:
    def __init__(self, name, attrs, methods, x, y, w, abstract=False):
        self.name = name
        self.attrs = attrs
        self.methods = methods
        self.x, self.y, self.w = x, y, w
        self.abstract = abstract
        self.h = 34 + 22 * len(attrs) + 22 * len(methods) + 16

    def draw(self):
        x, y, w, h = self.x, self.y, self.w, self.h
        d.rectangle([x, y, x + w, y + h], outline=FG, width=LINE_W, fill=(255, 255, 255))
        tw = d.textlength(self.name, font=F_TITLE)
        d.text((x + (w - tw) / 2, y + 8), self.name, font=F_TITLE, fill=FG)
        y0 = y + 34
        d.line([x, y0, x + w, y0], fill=FG, width=1)
        yy = y0 + 4
        for a in self.attrs:
            d.text((x + 8, yy), "- " + a, font=F_ATTR, fill=FG)
            yy += 22
        y1 = yy + 2
        d.line([x, y1, x + w, y1], fill=FG, width=1)
        yy = y1 + 4
        for m in self.methods:
            d.text((x + 8, yy), "+ " + m, font=F_ATTR, fill=FG)
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


def fleche_triangle(p_avant, p_pointe):
    ang = math.atan2(p_pointe[1] - p_avant[1], p_pointe[0] - p_avant[0])
    size = 18
    a1 = ang + math.radians(160)
    a2 = ang - math.radians(160)
    p1 = (p_pointe[0] + size * math.cos(a1), p_pointe[1] + size * math.sin(a1))
    p2 = (p_pointe[0] + size * math.cos(a2), p_pointe[1] + size * math.sin(a2))
    d.polygon([p_pointe, p1, p2], outline=FG, fill=(255, 255, 255))


def losange(p_bord, p_vers, plein):
    """Losange UML place du cote du conteneur (b1), pointe sur sa boite.

    Plein  : composition forte, le composant disparait avec le conteneur et
             n'est jamais partage.
    Vide   : agregation, le composant survit a la disparition du conteneur.
    """
    ang = math.atan2(p_vers[1] - p_bord[1], p_vers[0] - p_bord[0])
    L, W = 20, 8   # longueur sur l'axe, demi-largeur
    cx = p_bord[0] + (L / 2) * math.cos(ang)
    cy = p_bord[1] + (L / 2) * math.sin(ang)
    pts = [
        p_bord,
        (cx + W * math.sin(ang), cy - W * math.cos(ang)),
        (p_bord[0] + L * math.cos(ang), p_bord[1] + L * math.sin(ang)),
        (cx - W * math.sin(ang), cy + W * math.cos(ang)),
    ]
    d.polygon(pts, outline=FG, fill=FG if plein else (255, 255, 255))


def ligne_pointillee(p1, p2, tiret=12, blanc=8):
    """Trait discontinu, PIL ne sachant pas le faire nativement."""
    lg = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    if lg == 0:
        return
    ux, uy = (p2[0] - p1[0]) / lg, (p2[1] - p1[1]) / lg
    pos = 0.0
    while pos < lg:
        fin = min(pos + tiret, lg)
        d.line([(p1[0] + ux * pos, p1[1] + uy * pos),
                (p1[0] + ux * fin, p1[1] + uy * fin)], fill=FG, width=LINE_W)
        pos = fin + blanc


def dependance(b1, b2, stereotype):
    """Dependance UML : trait pointille et fleche ouverte, sans multiplicite.

    Journal conserve le login de l'auteur d'une action sous forme de libelle
    recopie, non de cle etrangere, afin que la trace survive a la suppression
    du compte. Ce n'est donc pas une association, et lui en donner une
    contredirait le schema. Mais laisser la classe isolee la faisait passer
    pour un oubli : la dependance dit le lien sans mentir sur sa nature.
    """
    p1 = b1.bord(b2.centre())
    p2 = b2.bord(b1.centre())
    ligne_pointillee(p1, p2)
    ang = math.atan2(p1[1] - p2[1], p1[0] - p2[0])
    for signe in (1, -1):
        a = ang + signe * 0.42
        d.line([p2, (p2[0] + 20 * math.cos(a), p2[1] + 20 * math.sin(a))],
               fill=FG, width=LINE_W)
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    tw = d.textlength(stereotype, font=F_LABEL)
    d.text((mx - tw / 2, my - 22), stereotype, font=F_LABEL, fill=FG)


def relation(b1, b2, verbe_txt, card1, card2, heritage=False, frac=0.5,
             agregation=None):
    """Ligne droite simple de b1 a b2, cardinalites aux extremites, verbe a
    la fraction "frac" de la ligne (0.5 = milieu ; decalable si une autre
    relation croise exactement au milieu, pour ne pas superposer les mots).

    agregation : None pour une association simple, 'composition' pour un
    losange plein ou 'agregation' pour un losange vide, toujours dessine du
    cote de b1 qui joue le role de conteneur.
    """
    p1 = b1.bord(b2.centre())
    p2 = b2.bord(b1.centre())
    d.line([p1, p2], fill=FG, width=LINE_W)
    if heritage:
        fleche_triangle(p1, p2)
        return
    if agregation:
        losange(p1, p2, plein=(agregation == 'composition'))
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    longueur = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    ox, oy = 14 * math.sin(ang), -14 * math.cos(ang)
    # decalage le long de la ligne proportionnel a sa longueur (jamais plus de
    # 22 % de chaque cote), pour que les deux cardinalites ne se chevauchent
    # jamais meme quand les deux boites sont tres proches l'une de l'autre
    dist1 = min(24, longueur * 0.22)
    dist2 = min(40, longueur * 0.30)
    # Le losange occupe les 20 premiers pixels : la cardinalite est repoussee
    # au-dela, sinon elle se superpose au symbole.
    if agregation:
        dist1 = max(dist1, 26)
    if card1:
        d.text((p1[0] + dist1 * math.cos(ang) + ox, p1[1] + dist1 * math.sin(ang) + oy),
              card1, font=F_CARD, fill=FG)
    if card2:
        d.text((p2[0] - dist2 * math.cos(ang) + ox, p2[1] - dist2 * math.sin(ang) * 0.85 + oy),
              card2, font=F_CARD, fill=FG)
    mx, my = p1[0] + (p2[0] - p1[0]) * frac, p1[1] + (p2[1] - p1[1]) * frac
    tw = d.textlength(verbe_txt, font=F_LABEL)
    # Le verbe est ecarte franchement de la ligne (2,3 fois le decalage des
    # cardinalites) : sur les liens courts il se superposait sinon au losange
    # et aux multiplicites.
    d.text((mx - tw / 2 + ox * 2.3, my - 8 + oy * 2.3), verbe_txt, font=F_LABEL, fill=FG)


# ─── Boîtes (mêmes positions que la version précédente) ─────────────────
resp = Box("ResponsableEnvironnement", ["zoneAffectation : Texte"],
           ["saisirSignalement()", "synchroniser()"], 20, 20, 300)
hse = Box("ExpertHSE", ["numeroAgrement : Texte"],
          ["traiterSignalement()", "validerActionCorrective()"], 340, 20, 300)
spec = Box("SpecialisteSuiviEnvironnemental", ["niveauHabilitation : Texte"],
           ["genererRapport()", "lancerAnalyseSatellite()"], 660, 20, 340)
par = Box("SpecialisteSuiviPAR", ["secteurAffecte : Texte"],
          ["traiterPlainte()"], 1020, 20, 300)
admin = Box("Administrateur", ["niveauAcces : Texte"],
            ["gererUtilisateurs()", "configurerSeuils()", "majModeleIA()"], 1340, 20, 300)

# Organismes de controle : aucune operation d'ecriture, ce que traduit
# l'absence de methode modifiant l'etat du systeme.
ande = Box("ANDE", ["referenceAgrement : Texte"],
           ["consulterConformite()", "recevoirRapport()"], 1660, 20, 300)
bad = Box("BAD", ["codeMission : Texte"],
          ["consulterSauvegardes()", "recevoirRapport()"], 1980, 20, 300)
riverain = Box("Riverain", ["chantierRattachement : Entier"],
               ["deposerDoleance()", "suivreDoleances()"], 2300, 20, 300)

util = Box("Utilisateur",
           ["idUtilisateur : Entier", "emailPro : Texte", "hashMdp : Texte",
            "dateInscription : Date"],
           ["authentifier() : Booléen", "consulterProfil()", "modifierMotDePasse()"],
           780, 260, 320, abstract=True)

plainte = Box("Plainte",
              ["idPlainte : Entier", "descriptionPlainte : Texte",
               "statutPlainte : Texte", "dateDepot : Horodatage",
               "canal : Texte", "categorie : Texte"],
              ["qualifierPlainte()", "cloturerPlainte()"], 20, 620, 200)

chantier = Box("Chantier", ["idChantier : Entier", "nomChantier : Texte", "commune : Texte",
                            "rayonInfluence : Entier"],
               ["genererIndicateurs()", "archiver()"], 380, 620, 300)

# Signalement est decale plus bas que Plainte/Chantier/Rapport pour laisser
# un couloir degage aux relations Utilisateur/Chantier -> Alerte (ligne 3),
# qui sinon traverseraient sa boite.
signalement = Box("Signalement",
                   ["idSignalement : Entier", "typeNuisance : Texte", "niveauCriticite : Texte",
                    "geom : Geometry", "dateObservation : Horodatage", "statutSignalement : Texte"],
                   ["qualifierSignalement()", "cloturerSignalement()"], 740, 820, 320)

rapport = Box("Rapport",
              ["idRapport : Entier", "periodeDebut : Date", "periodeFin : Date",
               "cheminFichier : Texte", "dateGeneration : Horodatage"],
              ["exporter()", "envoyerAuxBailleurs()"], 1140, 620, 300)

indice = Box("IndiceSatellite", ["idIndice : Entier", "typeIndice : Texte",
                                 "valeur : Decimal", "dateCalcul : Date"],
             ["calculer()", "comparerPeriodes()"], 20, 1170, 300)

alerte = Box("Alerte", ["idAlerte : Entier", "seuilDepasse : Texte",
                        "dateDeclenchement : Horodatage", "statutAlerte : Texte"],
             ["notifier()", "accuserReception()"], 360, 1170, 280)

photo = Box("Photo", ["idPhoto : Entier", "cheminStockage : Texte"],
            ["afficher()", "supprimer()"], 680, 1170, 260)

action = Box("ActionCorrective",
             ["idAction : Entier", "descriptionAction : Texte", "echeance : Date"],
             ["cloturerAction()", "assigner(responsable)"], 980, 1170, 280)

nc = Box("NonConformite",
         ["idNonConformite : Entier", "descriptionNC : Texte", "severite : Texte",
          "resolue : Booléen"],
         ["marquerResolue()"], 1300, 1170, 320)

# Le parametrage des seuils et la journalisation figuraient au schema et au
# memoire mais pas au modele. AlerteSeuil est passe a gauche : place a droite de
# Rapport, le trait venant de Chantier traversait cette boite et rayait ses
# attributs. Journal reste isole, sa colonne utilisateur etant un libelle
# recopie et non une cle etrangere : aucune association ne s'y rattache.
seuil = Box("AlerteSeuil",
            ["idSeuil : Entier", "indicateur : Texte", "seuil : Decimal",
             "actif : Booleen"],
            ["evaluer(mesure)", "activer()"], 20, 380, 300)

journal = Box("Journal",
              ["idJournal : Entier", "niveau : Texte", "message : Texte",
               "utilisateur : Texte", "ipSource : Texte", "horodatage : Horodatage"],
              ["tracer()", "purger(anciennete)"], 1900, 300, 320)

transmission = Box("TransmissionRapport",
                   ["idTransmission : Entier", "emetteur : Texte",
                    "destinataire : Texte", "organisme : Texte",
                    "dateTransmission : Horodatage", "succes : Booleen"],
                   ["tracer()"], 1660, 1170, 330)

boxes = [resp, hse, spec, par, admin, ande, bad, riverain, util, plainte,
        chantier, signalement, rapport, indice, alerte, photo, action, nc,
        transmission, seuil, journal]
for b in boxes:
    b.draw()

# ─── Héritage : ligne droite de chaque acteur vers Utilisateur ─────────
for b in (resp, hse, spec, par, admin, ande, bad, riverain):
    relation(b, util, "", None, None, heritage=True)

# ─── Associations : ligne droite, multiplicités correctes (1 côté "un",
#     0..* côté "plusieurs", comme un vrai diagramme de classes UML).
#     Fideles aux cles etrangeres reelles (backend/app/models.py) : Plainte
#     n'a pas de FK utilisateur (deposee par un tiers externe, nom_plaignant),
#     Alerte reference chantier_id et utilisateur_id (pas signalement_id),
#     ActionCorrective ne reference jamais Plainte. ─────────────────────
#   Associations simples : aucune dependance existentielle. Un signalement, un
#   rapport ou une alerte ne sont pas des "parties" de l'utilisateur qui les
#   produit ou les recoit ; ils lui survivent.
relation(util, signalement, "saisit", "1", "0..*")
relation(util, rapport, "rédige", "1", "0..*")
# Un rapport peut etre remis plusieurs fois, a des organismes differents et a
# des dates differentes. La trace ne reference pas l'emetteur par une cle
# etrangere mais conserve son adresse : elle doit survivre a la suppression du
# compte qui l'a produite, sans quoi la preuve de la remise disparaitrait avec
# son auteur.
relation(rapport, transmission, "fait l'objet de", "1", "0..*")
relation(util, alerte, "reçoit", "0..1", "0..*", frac=0.6)
relation(chantier, plainte, "concerne", "1", "0..*")
# Un seuil peut etre global, sans chantier : d'ou le 0..1 de ce cote.
relation(chantier, seuil, "paramètre", "0..1", "0..*", frac=0.5)
dependance(journal, util, "«trace»")
# Un riverain est rattache au chantier dont il subit les nuisances ;
# les autres profils n'ont pas de rattachement, d'ou le 0..1.
relation(chantier, util, "rattache", "0..1", "0..*", frac=0.42)
relation(chantier, alerte, "déclenche", "1", "0..*")

#   Agregations (losange vide) : le chantier possede ses signalements et ses
#   indices, mais ils lui survivent. Le code refuse d'ailleurs de supprimer un
#   chantier encore rattache a des signalements (HTTP 409) au lieu de les
#   detruire en cascade.
relation(chantier, signalement, "se situe sur", "1", "0..*", frac=0.63, agregation='agregation')
relation(chantier, indice, "génère", "1", "0..*", agregation='agregation')

#   Compositions (losange plein) : photo, action corrective et non-conformite
#   ne peuvent exister sans le signalement qu'elles documentent et ne sont
#   jamais partagees entre plusieurs signalements. Le modele ORM le declare
#   explicitement (cascade="all, delete-orphan" dans backend/app/models.py).
relation(signalement, photo, "est illustré par", "1", "0..*", agregation='composition')
relation(signalement, action, "fait l'objet de", "1", "0..*", frac=0.58, agregation='composition')
relation(signalement, nc, "signale", "1", "0..*", frac=0.6, agregation='composition')

img.save(r"C:\Users\DELL\AppData\Local\Temp\claude\d--etude-soutenance-SI-ENV\3233866b-194c-446a-b8f6-65c65b911c25\scratchpad\classes_simple.png")
print("Image generee.")
