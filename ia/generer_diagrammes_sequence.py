# -*- coding: utf-8 -*-
"""
Regenere les trois diagrammes de sequence du chapitre 4 (figures 4.4, 4.5, 4.6).

Aucun script source n'existait pour ces figures. Les images en place
presentaient quatre defauts :
  1. le libelle des messages reflexifs debordait du cadre alt/opt et du bord
     de l'image (la largeur etait fixe, sans tenir compte du texte) ;
  2. un titre etait incruste dans l'image avec un numero errone (6.4, 6.5,
     6.6) qui contredisait la legende Word placee juste en dessous ;
  3. aucun accent ;
  4. un tiers de la hauteur etait vide.

Ici la largeur du canevas est CALCULEE a partir du libelle le plus long, et
la hauteur a partir du contenu reellement dessine : plus aucun debordement
possible. Aucun titre n'est incruste, la legende du document fait foi.
"""
from PIL import Image, ImageDraw, ImageFont

FG = (0, 0, 0)
GRIS = (128, 128, 128)
GRIS_CLAIR = (242, 242, 242)
BLANC = (255, 255, 255)

F_NOM = ImageFont.truetype("arialbd.ttf", 19)
F_MSG = ImageFont.truetype("arial.ttf", 17)
F_FRAG = ImageFont.truetype("arialbd.ttf", 17)
F_COND = ImageFont.truetype("ariali.ttf", 17)

MARGE = 30
X_ACTEUR = 210          # axe de vie de l'acteur
LARGEUR_MIN_MSG = 620   # longueur mini d'une fleche acteur <-> systeme
LOOP_W = 60             # largeur du crochet d'un message reflexif
H_MSG = 78              # pas vertical entre deux messages
PAD_FRAG = 22           # marge interne d'un fragment
H_GARDE = 46            # espace sous une garde avant le 1er message


def _mes(txt, font):
    img = Image.new("RGB", (1, 1))
    return ImageDraw.Draw(img).textlength(txt, font=font)


class Sequence:
    """Construit un diagramme de sequence a deux axes de vie (acteur, systeme).

    Les elements sont d'abord declares, puis `dessiner()` calcule les
    dimensions necessaires avant de tracer : c'est ce qui garantit qu'aucun
    libelle ne sortira du cadre.
    """

    @staticmethod
    def _lignes_nom(nom):
        mots, lignes, courant = nom.split(), [], ""
        for mot in mots:
            essai = (courant + " " + mot).strip()
            if _mes(essai, F_NOM) > 200 and courant:
                lignes.append(courant); courant = mot
            else:
                courant = essai
        lignes.append(courant)
        return lignes

    def __init__(self, acteur, systeme="Application"):
        self.acteur, self.systeme = acteur, systeme
        self.elements = []   # liste d'operations a dessiner
        self.n = 0           # numerotation des messages

    # --- declaration du contenu ---------------------------------------
    def message(self, sens, txt, retour=False):
        """sens : 'aller' (acteur vers systeme) ou 'retour' (systeme vers acteur)."""
        self.n += 1
        self.elements.append(('msg', sens, f"{self.n}: {txt}", retour))

    def reflexif(self, txt):
        self.n += 1
        self.elements.append(('self', f"{self.n}: {txt}"))

    def fragment(self, type_frag, conditions):
        """type_frag : 'alt' ou 'opt'. conditions : liste de gardes.
        Retourne un objet a remplir branche par branche."""
        frag = {'type': type_frag, 'branches': [(c, []) for c in conditions]}
        self.elements.append(('frag', frag))
        return frag

    def dans(self, frag, i_branche):
        """Bascule la declaration des messages suivants dans une branche."""
        return _Branche(self, frag['branches'][i_branche][1])

    def note(self, lignes):
        self.elements.append(('note', lignes))

    # --- calcul des dimensions ---------------------------------------
    def _largeur_requise(self):
        """Largeur du canevas : le libelle reflexif le plus long ne doit jamais
        depasser le bord droit."""
        x_sys = X_ACTEUR + LARGEUR_MIN_MSG
        besoin = x_sys + LOOP_W + 14

        def parcourir(elems):
            m = 0
            for e in elems:
                if e[0] == 'self':
                    m = max(m, _mes(e[1], F_MSG))
                elif e[0] == 'frag':
                    for cond, sous in e[1]['branches']:
                        m = max(m, parcourir(sous))
            return m

        besoin += parcourir(self.elements)
        # largeur necessaire aux gardes des fragments et aux noms d'axes
        besoin = max(besoin, x_sys + _mes(self.systeme, F_NOM) / 2 + MARGE)
        return int(besoin + MARGE), x_sys

    def _hauteur(self, elems, y):
        for e in elems:
            if e[0] in ('msg', 'self'):
                y += H_MSG
            elif e[0] == 'frag':
                y += 34                      # bandeau du fragment
                for i, (cond, sous) in enumerate(e[1]['branches']):
                    if i:
                        y += 32              # separateur + garde
                    y += H_GARDE
                    y = self._hauteur(sous, y)
                    y += 12
                y += PAD_FRAG + 30
            elif e[0] == 'note':
                y += 34 + 26 * len(e[1])
        return y

    # --- trace ---------------------------------------------------------
    def dessiner(self, chemin):
        W, x_sys = self._largeur_requise()
        y_debut = 40 + 104 + 25 * len(self._lignes_nom(self.acteur)) + 62
        H = int(self._hauteur(self.elements, y_debut) + 70)

        self.img = Image.new("RGB", (W, H), BLANC)
        self.d = ImageDraw.Draw(self.img)
        self.x_sys = x_sys
        self.W = W

        # axes de vie (pointilles) : demarrent sous le nom de l'acteur
        y_axe = 40 + 104 + 25 * len(self._lignes_nom(self.acteur)) + 8
        for x in (X_ACTEUR, x_sys):
            y = y_axe
            while y < H - 30:
                self.d.line([x, y, x, min(y + 9, H - 30)], fill=GRIS, width=2)
                y += 16

        self._acteur(X_ACTEUR, 40)
        self._systeme(x_sys, 44)

        y = self._corps(self.elements, y_debut, X_ACTEUR - 40, W - MARGE)
        self.img.save(chemin)
        return W, H

    def _acteur(self, x, y):
        r = 15
        self.d.ellipse([x - r, y, x + r, y + 2 * r], outline=FG, width=3)
        self.d.line([x, y + 2 * r, x, y + 62], fill=FG, width=3)          # tronc
        self.d.line([x - 26, y + 42, x + 26, y + 42], fill=FG, width=3)   # bras
        self.d.line([x, y + 62, x - 22, y + 96], fill=FG, width=3)        # jambes
        self.d.line([x, y + 62, x + 22, y + 96], fill=FG, width=3)
        # Un nom long est reparti sur plusieurs lignes : centre sur l'axe, il
        # empietait sinon sur le libelle du premier message.
        lignes = self._lignes_nom(self.acteur)
        for i, l in enumerate(lignes):
            tw = _mes(l, F_NOM)
            self.d.text((x - tw / 2, y + 104 + 25 * i), l, font=F_NOM, fill=FG)
        self._h_nom = 25 * len(lignes)

    def _systeme(self, x, y):
        tw = _mes(self.systeme, F_NOM)
        w, h = tw + 60, 58
        self.d.rectangle([x - w / 2, y, x + w / 2, y + h], outline=FG, width=3, fill=BLANC)
        self.d.text((x - tw / 2, y + (h - 24) / 2), self.systeme, font=F_NOM, fill=FG)

    def _fleche(self, x1, x2, y, pointillee, pleine):
        if pointillee:
            pas, xx = 14, min(x1, x2)
            while xx < max(x1, x2):
                self.d.line([xx, y, min(xx + 8, max(x1, x2)), y], fill=FG, width=2)
                xx += pas
        else:
            self.d.line([x1, y, x2, y], fill=FG, width=2)
        s = 13
        sgn = 1 if x2 > x1 else -1
        if pleine:
            self.d.polygon([(x2, y), (x2 - sgn * s, y - 6), (x2 - sgn * s, y + 6)], fill=FG)
        else:   # pointe ouverte des messages de retour
            self.d.line([x2, y, x2 - sgn * s, y - 6], fill=FG, width=2)
            self.d.line([x2, y, x2 - sgn * s, y + 6], fill=FG, width=2)

    def _corps(self, elems, y, gauche, droite):
        for e in elems:
            if e[0] == 'msg':
                _, sens, txt, retour = e
                x1, x2 = (X_ACTEUR, self.x_sys) if sens == 'aller' else (self.x_sys, X_ACTEUR)
                tw = _mes(txt, F_MSG)
                self.d.text(((X_ACTEUR + self.x_sys) / 2 - tw / 2, y - 26), txt, font=F_MSG, fill=FG)
                self._fleche(x1, x2, y, pointillee=retour, pleine=not retour)
                y += H_MSG
            elif e[0] == 'self':
                txt = e[1]
                x = self.x_sys
                self.d.line([x, y, x + LOOP_W, y], fill=FG, width=2)
                self.d.line([x + LOOP_W, y, x + LOOP_W, y + 26], fill=FG, width=2)
                self.d.line([x + LOOP_W, y + 26, x + 16, y + 26], fill=FG, width=2)
                self.d.polygon([(x + 4, y + 26), (x + 18, y + 20), (x + 18, y + 32)], fill=FG)
                self.d.text((x + 14, y - 26), txt, font=F_MSG, fill=FG)
                y += H_MSG
            elif e[0] == 'frag':
                y = self._fragment(e[1], y, gauche, droite)
            elif e[0] == 'note':
                y = self._note(e[1], y)
        return y

    def _fragment(self, frag, y, gauche, droite):
        y0 = y
        # hauteur du fragment calculee avant trace, pour dessiner le cadre
        y_fin = self._hauteur([('frag', frag)], y) - PAD_FRAG
        self.d.rectangle([gauche, y0, droite, y_fin], outline=GRIS, width=2)

        # etiquette du type (alt / opt) avec le coin coupe
        lib = frag['type']
        lw = _mes(lib, F_FRAG) + 34
        self.d.polygon([(gauche, y0), (gauche + lw, y0), (gauche + lw, y0 + 20),
                        (gauche + lw - 16, y0 + 34), (gauche, y0 + 34)],
                       outline=GRIS, fill=GRIS_CLAIR)
        self.d.text((gauche + 12, y0 + 6), lib, font=F_FRAG, fill=FG)

        yy = y0 + 34
        for i, (cond, sous) in enumerate(frag['branches']):
            if i:
                # separateur en pointille entre deux branches
                yy += 8
                xx = gauche
                while xx < droite:
                    self.d.line([xx, yy, min(xx + 10, droite), yy], fill=GRIS, width=2)
                    xx += 18
                yy += 24
                self.d.text((gauche + 14, yy - 20), f"[{cond}]", font=F_COND, fill=FG)
            else:
                # a droite de l'etiquette, sur la meme ligne qu'elle
                self.d.text((gauche + lw + 16, y0 + 7), f"[{cond}]", font=F_COND, fill=FG)
            yy += H_GARDE
            yy = self._corps(sous, yy, gauche + PAD_FRAG, droite - PAD_FRAG)
            yy += 12
        return y_fin + PAD_FRAG + 30

    def _note(self, lignes, y):
        w = max(_mes(l, F_MSG) for l in lignes) + 48
        h = 20 + 26 * len(lignes)
        x = (X_ACTEUR + self.x_sys) / 2 - w / 2
        coin = 18
        self.d.polygon([(x, y), (x + w - coin, y), (x + w, y + coin),
                        (x + w, y + h), (x, y + h)], outline=GRIS, fill=GRIS_CLAIR)
        self.d.line([x + w - coin, y, x + w - coin, y + coin], fill=GRIS, width=2)
        self.d.line([x + w - coin, y + coin, x + w, y + coin], fill=GRIS, width=2)
        for i, l in enumerate(lignes):
            self.d.text((x + 24, y + 12 + 26 * i), l, font=F_MSG, fill=FG)
        return y + h + 34


class _Branche:
    """Ajoute des elements dans une branche de fragment, avec la meme
    numerotation continue que le diagramme parent."""
    def __init__(self, seq, cible):
        self.seq, self.cible = seq, cible

    def message(self, sens, txt, retour=False):
        self.seq.n += 1
        self.cible.append(('msg', sens, f"{self.seq.n}: {txt}", retour))

    def reflexif(self, txt):
        self.seq.n += 1
        self.cible.append(('self', f"{self.seq.n}: {txt}"))


SC = r"C:\Users\DELL\AppData\Local\Temp\claude\d--etude-soutenance-SI-ENV\3233866b-194c-446a-b8f6-65c65b911c25\scratchpad"

# ─── Figure 4.4 : saisie d'un signalement hors ligne ────────────────────
s = Sequence("Agent terrain")
s.message('aller', "sélectionner le type de nuisance")
s.message('aller', "prendre une photo")
f = s.fragment('alt', ["GPS disponible", "GPS indisponible"])
s.dans(f, 0).reflexif("obtenir les coordonnées GPS")
s.dans(f, 1).message('aller', "saisir la position manuellement")
f2 = s.fragment('alt', ["nuisance reconnue", "nuisance non reconnue"])
s.dans(f2, 0).reflexif("predict(photo) : diagnostic IA local")
s.dans(f2, 1).message('aller', "saisir le type manuellement")
s.reflexif("enregistrer localement (statut = PENDING_SYNC)")
f3 = s.fragment('opt', ["retour du réseau détecté"])
s.dans(f3, 0).reflexif("synchroniser et mettre à jour le statut (SYNCED)")
s.note(["La saisie et l'enregistrement local fonctionnent",
        "entièrement sans connexion réseau."])
print("Figure 4.4 :", s.dessiner(SC + r"\seq44.png"))

# ─── Figure 4.5 : authentification JWT ─────────────────────────────────
# 12 h : valeur reellement deployee (ACCESS_TOKEN_EXPIRE_MINUTES=720 dans
# backend/docker-compose.yml), et non les 60 min du defaut de config.py.
s = Sequence("Utilisateur")
s.message('aller', "saisir(email, motDePasse)")
s.reflexif("vérifier les identifiants (hachage bcrypt)")
f = s.fragment('alt', ["identifiants valides", "identifiants invalides"])
b = s.dans(f, 0)
b.reflexif("générer le jeton d'accès (JWT HS256, 12 h)")
b.message('retour', "accès accordé, jeton transmis", retour=True)
b.message('retour', "rediriger vers l'espace applicatif", retour=True)
s.dans(f, 1).message('retour', "message d'erreur explicite", retour=True)
print("Figure 4.5 :", s.dessiner(SC + r"\seq45.png"))

# ─── Figure 4.6 : generation d'un rapport PGES ─────────────────────────
s = Sequence("Spécialiste Suivi Environnemental")
s.message('aller', "sélectionner(période, chantiers)")
s.message('aller', "demander la génération du rapport")
s.reflexif("agréger signalements, alertes et mesures")
f = s.fragment('alt', ["données disponibles pour la période", "aucune donnée disponible"])
b = s.dans(f, 0)
b.reflexif("appliquer le modèle réglementaire BAD et générer le PDF")
b.message('retour', "lien de téléchargement du rapport", retour=True)
b.message('retour', "télécharger le rapport", retour=True)
s.dans(f, 1).message('retour', "message informatif", retour=True)
print("Figure 4.6 :", s.dessiner(SC + r"\seq46.png"))
