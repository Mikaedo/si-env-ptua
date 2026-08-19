# -*- coding: utf-8 -*-
"""
Produit le texte de la soutenance, minute par minute, avec sa demonstration.

Le document precedent, FIL_CONDUCTEUR, visait dix minutes sans support. Celui-ci
part du diaporama existant de trente-deux diapositives et d'une plage de dix a
quinze minutes : il faut donc surtout dire lesquelles montrer et lesquelles
passer. Un expose qui tente les trente-deux consacre dix-neuf secondes a
chacune, ce qu'aucun auditoire ne suit.

Deux partis pris de mise en page. Le texte a prononcer est distingue du reste
par un filet et une italique, pour qu'un regard rapide le retrouve en cours de
parole. Et les minutes sont posees en marge plutot que dans le fil, afin de se
reperer sans lire.

Les huit profils ne peuvent pas etre montres un par un : quatre connexions
suffisent, les quatre autres se deduisant d'une phrase. Le tableau d'ouverture
fixe cette correspondance, qui est la vraie difficulte de l'exercice.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (HRFlowable, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

SORTIE = Path(r"C:\Users\DELL\Downloads\MEMOIRE\SPEECH_SOUTENANCE_SI-ENV.pdf")

BLEU = colors.HexColor("#004F9F")
BLEU_SOMBRE = colors.HexColor("#003A73")
ORANGE = colors.HexColor("#F37021")
GRIS = colors.HexColor("#5A6B7F")
GRIS_CLAIR = colors.HexColor("#EFF3F8")
ENCRE = colors.HexColor("#101B2B")
FILET = colors.HexColor("#D7DEE9")

base = getSampleStyleSheet()

TITRE = ParagraphStyle("Titre", parent=base["Normal"], fontName="Helvetica-Bold",
                       fontSize=19, textColor=BLEU_SOMBRE, leading=23, spaceAfter=4)
SOUS = ParagraphStyle("Sous", parent=base["Normal"], fontName="Helvetica",
                      fontSize=10.5, textColor=GRIS, leading=14, spaceAfter=14)
H = ParagraphStyle("H", parent=base["Normal"], fontName="Helvetica-Bold",
                   fontSize=12.5, textColor=BLEU, spaceBefore=15, spaceAfter=6)
CORPS = ParagraphStyle("Corps", parent=base["Normal"], fontName="Helvetica",
                       fontSize=9.6, textColor=ENCRE, leading=13.8,
                       alignment=TA_JUSTIFY, spaceAfter=6)
DIRE = ParagraphStyle("Dire", parent=base["Normal"], fontName="Helvetica-Oblique",
                      fontSize=10.2, textColor=colors.HexColor("#1E3A5F"),
                      leading=15, leftIndent=14, rightIndent=8,
                      borderPadding=0, spaceBefore=2, spaceAfter=8)
NOTE = ParagraphStyle("Note", parent=CORPS, fontSize=8.8, textColor=GRIS,
                      spaceAfter=4)
MINUTE = ParagraphStyle("Minute", parent=base["Normal"], fontName="Helvetica-Bold",
                        fontSize=10.5, textColor=ORANGE, spaceAfter=1)
CELL = ParagraphStyle("Cell", parent=base["Normal"], fontName="Helvetica",
                      fontSize=8.8, textColor=ENCRE, leading=12)
CELLG = ParagraphStyle("CellG", parent=CELL, fontName="Helvetica-Bold",
                       textColor=BLEU_SOMBRE)


def tableau(entetes, lignes, largeurs):
    donnees = [[Paragraph(e, CELLG) for e in entetes]]
    for l in lignes:
        donnees.append([Paragraph(str(c), CELL) for c in l])
    t = Table(donnees, colWidths=largeurs, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLAIR),
        ("GRID", (0, 0), (-1, -1), 0.5, FILET),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def bloc(minute, diapos, dire, avant=None, apres=None):
    """Une etape : sa minute, ses diapositives, ce qu'on dit, ce qu'on note."""
    elements = [Paragraph(f"{minute} &nbsp;&nbsp;|&nbsp;&nbsp; {diapos}", MINUTE)]
    if avant:
        elements.append(Paragraph(avant, NOTE))
    for passage in dire:
        elements.append(Paragraph(f"&laquo;&nbsp;{passage}&nbsp;&raquo;", DIRE))
    if apres:
        elements.append(Paragraph(apres, NOTE))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=FILET,
                               spaceBefore=2, spaceAfter=7))
    return KeepTogether(elements)


def construire():
    doc = SimpleDocTemplate(
        str(SORTIE), pagesize=A4,
        leftMargin=2.1 * cm, rightMargin=2.1 * cm,
        topMargin=1.9 * cm, bottomMargin=1.8 * cm,
        title="Soutenance SI-ENV, texte et demonstration",
        author="N'GUESSAN DIBY KONANBOUO Georges Mikael")

    h = []
    L = 16.8 * cm

    h.append(Paragraph("Soutenance SI-ENV", TITRE))
    h.append(Paragraph(
        "Texte minut&eacute; et parcours de d&eacute;monstration &middot; 13 minutes "
        "&middot; N'GUESSAN DIBY Konanbouo Georges Mika&euml;l", SOUS))

    # --- Les huit profils ---------------------------------------------------
    h.append(Paragraph("La r&egrave;gle des huit profils", H))
    h.append(Paragraph(
        "Vous ne connecterez jamais huit comptes en direct. Quatre suffisent, "
        "les quatre autres se d&eacute;duisant d'une phrase. Tenter les huit "
        "consommerait la moiti&eacute; du temps de parole sans rien montrer de "
        "plus.", CORPS))
    h.append(tableau(
        ["Vous d&eacute;montrez", "Vous mentionnez seulement"],
        [["RESP_ENV, application mobile agent",
          "EXPERT_HSE, m&ecirc;me application, avec le traitement en plus"],
         ["SPEC_ENV, tableau de bord web",
          "ADMIN, m&ecirc;mes &eacute;crans plus la gestion des comptes"],
         ["PLAIGNANT, application mobile citoyenne",
          "SPEC_PAR, il appara&icirc;t quand la dol&eacute;ance tombe"],
         ["ANDE, consultation seule",
          "BAD, droits strictement identiques"]],
        [8.4 * cm, 8.4 * cm]))
    h.append(Spacer(1, 0.35 * cm))
    h.append(Paragraph(
        "La phrase qui couvre les absents : &laquo;&nbsp;l'Expert HSE utilise la "
        "m&ecirc;me application avec des droits de traitement, et la Banque "
        "Africaine de D&eacute;veloppement dispose du m&ecirc;me acc&egrave;s que "
        "l'ANDE.&nbsp;&raquo;", CORPS))

    # --- Le deroule ---------------------------------------------------------
    h.append(Paragraph("Le d&eacute;roul&eacute;", H))
    h.append(Paragraph(
        "Le texte en italique est &agrave; prononcer. Les lignes grises sont des "
        "consignes, pas des paroles.", NOTE))
    h.append(Spacer(1, 0.2 * cm))

    h.append(bloc(
        "0:00 &agrave; 1:30", "diapositives 1, 4 et 7",
        ["Le Projet de Transport Urbain d'Abidjan repr&eacute;sente 657,8 "
         "milliards de francs et il est class&eacute; Cat&eacute;gorie 1 par la "
         "Banque Africaine de D&eacute;veloppement. Ce classement impose &agrave; "
         "l'AGEROUTE un suivi environnemental document&eacute;, remis &agrave; "
         "l'agence de tutelle et au bailleur.",
         "Dans les faits, ce suivi se faisait sur des fiches papier et des "
         "tableurs. Un incident pouvait rester ignor&eacute; plusieurs semaines, "
         "aucun n'&eacute;tait rattach&eacute; &agrave; un ouvrage pr&eacute;cis, "
         "et produire le rapport demandait plusieurs jours de ressaisie.",
         "D'o&ugrave; ma question : comment rendre ce suivi fiable et conforme, "
         "sans budget d&eacute;di&eacute; et sans connexion Internet garantie sur "
         "les chantiers ? Ces deux contraintes ont command&eacute; toute la "
         "conception."],
        avant="Passez la 2 et la 3, on ne lit pas un sommaire &agrave; l'oral.",
        apres="Passez aussi la 5 et la 6 : les organigrammes n'apprennent rien "
              "au jury et co&ucirc;tent trente secondes."))

    h.append(bloc(
        "1:30 &agrave; 2:30", "diapositives 10 et 11",
        ["Six limites pr&eacute;cises ont &eacute;t&eacute; identifi&eacute;es. "
         "D&eacute;tection tardive, gravit&eacute; appr&eacute;ci&eacute;e sans "
         "r&eacute;f&eacute;rentiel, absence de g&eacute;olocalisation, "
         "donn&eacute;es dispers&eacute;es, rapport manuel, aucune alerte "
         "automatique.",
         "Le tableau que vous voyez associe &agrave; chacune une r&eacute;ponse "
         "du syst&egrave;me. C'est cette grille qui a servi de cahier des "
         "charges."],
        apres="Ne les &eacute;num&eacute;rez pas une par une, laissez le tableau "
              "parler."))

    h.append(bloc(
        "2:30 &agrave; 4:00", "diapositives 15 et 16",
        ["L'architecture est en trois tiers. Trois applications clientes, un "
         "serveur, une base spatiale. Les clients ne parlent jamais directement "
         "&agrave; la base : tout passe par le serveur, qui applique les "
         "r&egrave;gles m&eacute;tier et le contr&ocirc;le des habilitations.",
         "C'est ce d&eacute;couplage qui m'a permis d'ajouter l'application "
         "citoyenne, en fin de projet, sans toucher aux clients existants.",
         "Le diagramme de cas d'utilisation montre huit profils. Deux d'entre "
         "eux m&eacute;ritent qu'on s'y arr&ecirc;te : l'Agence Nationale de "
         "l'Environnement et la Banque Africaine de D&eacute;veloppement ont un "
         "acc&egrave;s en consultation seule. Ils voient les m&ecirc;mes "
         "&eacute;crans que le sp&eacute;cialiste, sans aucune commande "
         "d'&eacute;criture, et la restriction est appliqu&eacute;e c&ocirc;t&eacute; "
         "serveur, pas seulement masqu&eacute;e dans l'interface. Celui qui "
         "contr&ocirc;le ne doit pas pouvoir modifier ce qu'il examine."],
        apres="Passez 17, 18 et 19. Les diagrammes UML sont illisibles "
              "projet&eacute;s, et ils sont dans le m&eacute;moire."))

    h.append(bloc(
        "4:00 &agrave; 5:00", "diapositive 23",
        ["Premi&egrave;re d&eacute;cision de conception : la reconnaissance "
         "d'images tourne sur le t&eacute;l&eacute;phone, pas sur un serveur.",
         "J'ai compar&eacute; trois mod&egrave;les. YOLOv8n atteint 80,7 pour "
         "cent de pr&eacute;cision moyenne, contre 68,5 pour Faster R-CNN. Mais "
         "le crit&egrave;re d&eacute;cisif n'&eacute;tait pas la pr&eacute;cision : "
         "c'est le temps d'inf&eacute;rence, 4,3 millisecondes contre 312. Sur le "
         "t&eacute;l&eacute;phone, dans la cha&icirc;ne compl&egrave;te, on est "
         "entre 8,6 et 23,4 millisecondes.",
         "On y perd un peu en pr&eacute;cision. On gagne de pouvoir travailler "
         "l&agrave; o&ugrave; le r&eacute;seau manque, c'est-&agrave;-dire "
         "justement sur les chantiers. Et le diagnostic reste une aide au "
         "classement, jamais une d&eacute;cision."],
        apres="Passez 21, 22 et 26 : la d&eacute;monstration remplacera les "
              "captures d'&eacute;cran."))

    h.append(bloc(
        "5:00 &agrave; 5:45", "diapositive 24",
        ["Quatre indices satellitaires compl&egrave;tent le terrain, "
         "calcul&eacute;s par Google Earth Engine sur les emprises r&eacute;elles "
         "des chantiers : v&eacute;g&eacute;tation, eau, dioxyde d'azote, et un "
         "indice de risque croisant pluie et relief.",
         "Cette donn&eacute;e demande de la prudence : un indice de "
         "v&eacute;g&eacute;tation d&eacute;grad&eacute; peut signaler un chantier "
         "mal ma&icirc;tris&eacute; comme une simple saison s&egrave;che."]))

    h.append(PageBreak())

    # --- Demonstration ------------------------------------------------------
    h.append(Paragraph("5:45 &agrave; 10:00 &middot; La d&eacute;monstration", H))
    h.append(Paragraph(
        "Annoncez-la : &laquo;&nbsp;je vous montre maintenant le syst&egrave;me en "
        "fonctionnement&nbsp;&raquo;. R&eacute;p&eacute;tez ce parcours jusqu'&agrave; "
        "ne plus chercher un bouton en direct : une h&eacute;sitation de dix "
        "secondes devant un menu co&ucirc;te plus qu'une phrase mal tourn&eacute;e.",
        CORPS))
    h.append(tableau(
        ["Dur&eacute;e", "Ce que vous faites", "Ce que vous dites pendant"],
        [["1:00<br/><b>Le terrain</b>",
          "T&eacute;l&eacute;phone, application SI-ENV,<br/>"
          "compte resp.env@ageroute.ci<br/><br/>"
          "Cr&eacute;ez un signalement : cat&eacute;gorie, photo. "
          "La position se prend seule.",
          "La saisie prend moins d'une minute. Si le r&eacute;seau manque, tout "
          "est stock&eacute; localement et part au retour de la connexion. "
          "L'Expert HSE utilise la m&ecirc;me application, avec en plus le "
          "traitement et la validation des actions correctives."],
         ["1:30<br/><b>Le pilotage</b>",
          "Ordinateur, compte<br/>spec.env@ageroute.ci<br/><br/>"
          "Le signalement appara&icirc;t dans la liste. Montrez la carte, puis "
          "produisez le rapport et <b>ouvrez le PDF</b>.",
          "Le rapport de suivi environnemental se produit en quelques secondes. "
          "C'est l'op&eacute;ration qui demandait plusieurs jours de ressaisie. "
          "Attention au terme : ce document n'est pas le PGES, qui est un plan "
          "&eacute;tabli en amont. C'est le rapport qui rend compte de sa mise en "
          "&oelig;uvre."],
         ["1:00<br/><b>Le riverain</b>",
          "T&eacute;l&eacute;phone, application SI-ENV Citoyen,<br/>"
          "compte riverain@yopougon.ci<br/><br/>"
          "D&eacute;posez une dol&eacute;ance.",
          "Un habitant qui subit une nuisance d&eacute;pose une dol&eacute;ance. "
          "L'application ne s'active que s'il se trouve dans la zone d'influence "
          "d'un chantier, et elle d&eacute;termine seule lequel. Cela donne un "
          "canal au M&eacute;canisme de Gestion des Plaintes exig&eacute; par la "
          "BAD, qui supposait jusqu'ici qu'un habitant se d&eacute;place "
          "jusqu'&agrave; une permanence."],
         ["1:30<br/><b>La cha&icirc;ne<br/>et le contr&ocirc;le</b>",
          "Ordinateur, compte<br/>spec.par@ageroute.ci :<br/>"
          "la dol&eacute;ance est arriv&eacute;e.<br/><br/>"
          "Puis compte controle@ande.ci.",
          "Voici ce que voit l'agence de tutelle. M&ecirc;mes donn&eacute;es, "
          "aucun bouton de modification, ni plaintes ni administration dans le "
          "menu. La Banque Africaine de D&eacute;veloppement dispose du m&ecirc;me "
          "acc&egrave;s."]],
        [2.5 * cm, 5.6 * cm, 8.7 * cm]))
    h.append(Spacer(1, 0.3 * cm))
    h.append(Paragraph(
        "S'il vous reste du temps &agrave; la derni&egrave;re &eacute;tape, tentez "
        "une modification avec le compte ANDE pour montrer que le refus vient du "
        "serveur et non d'un bouton masqu&eacute;.", NOTE))

    # --- Fin ----------------------------------------------------------------
    h.append(Paragraph("La fin", H))

    h.append(bloc(
        "10:00 &agrave; 12:00", "diapositives 29 et 30",
        ["Je tiens &agrave; dire les limites de ce travail. D'abord, le "
         "syst&egrave;me n'a pas &eacute;t&eacute; utilis&eacute; en conditions "
         "r&eacute;elles par des agents qui ne l'ont pas con&ccedil;u, et c'est le "
         "seul essai qui permettrait de juger de son ergonomie. Ensuite, le corpus "
         "d'entra&icirc;nement vient de sources ouvertes et ne refl&egrave;te pas "
         "parfaitement les chantiers d'Abidjan, ce qui limite la port&eacute;e du "
         "80,7 pour cent. Enfin, la v&eacute;rification de position atteste d'une "
         "localisation, pas d'une r&eacute;sidence.",
         "Ces limites dessinent la suite : une phase pilote sur un chantier avec "
         "les &eacute;quipes en place, un corpus enrichi de photographies du PTUA, "
         "et le passage &agrave; un h&eacute;bergement de production, qui ne "
         "demande qu'un changement de param&egrave;tres."],
        avant="Ralentissez ici. C'est ce qui distingue un bon candidat d'un "
              "candidat qui r&eacute;cite."))

    h.append(bloc(
        "12:00 &agrave; 13:00", "diapositive 31, puis regardez le jury",
        ["L'ensemble de l'h&eacute;bergement est aujourd'hui gratuit, ce qui "
         "&eacute;tait une contrainte du sujet et non un choix par d&eacute;faut. "
         "Le syst&egrave;me est en ligne, il compte 119 tests automatis&eacute;s "
         "rejou&eacute;s &agrave; chaque modification, et il co&ucirc;te "
         "z&eacute;ro franc.",
         "Sur le plan personnel, ce projet m'a moins appris &agrave; &eacute;crire "
         "du code qu'&agrave; d&eacute;cider. Arbitrer entre un mod&egrave;le "
         "pr&eacute;cis et un mod&egrave;le rapide, accepter qu'une "
         "fonctionnalit&eacute; utile ne soit pas prioritaire, reconna&icirc;tre "
         "qu'une mesure flatteuse ne prouve rien. Ils m'ont aussi appris qu'un "
         "outil techniquement irr&eacute;prochable dont personne ne se sert n'a "
         "rien r&eacute;solu.",
         "Je vous remercie."],
        apres="Terminez sur le regard, pas sur l'&eacute;cran. Le silence qui "
              "suit vous appartient : ne le comblez pas."))

    # --- Garde-fous ---------------------------------------------------------
    h.append(Paragraph("Si vous d&eacute;bordez", H))
    h.append(tableau(
        ["&Agrave; sacrifier, dans cet ordre", "Pourquoi c'est possible"],
        [["La t&eacute;l&eacute;d&eacute;tection, &agrave; 5:00",
          "Une phrase suffit : &laquo; quatre indices satellitaires "
          "compl&egrave;tent le terrain &raquo;."],
         ["La quatri&egrave;me &eacute;tape de la d&eacute;monstration",
          "La consultation seule a d&eacute;j&agrave; &eacute;t&eacute; dite "
          "&agrave; la diapositive 16."],
         ["Les perspectives, &agrave; 11:00",
          "Elles figurent au m&eacute;moire ; gardez-en une seule."]],
        [7 * cm, 9.8 * cm]))
    h.append(Spacer(1, 0.3 * cm))
    h.append(Paragraph(
        "<b>Ne sacrifiez jamais</b> la premi&egrave;re minute, les limites, ni la "
        "derni&egrave;re phrase. Le probl&egrave;me, la lucidit&eacute; et "
        "l'apport personnel sont ce qu'un jury retient.", CORPS))

    h.append(Paragraph("Avant d'entrer", H))
    h.append(Paragraph(
        "Double-cliquez sur REVEILLER_SI-ENV.bat et attendez le vert : le serveur "
        "se met en veille apr&egrave;s quinze minutes et la premi&egrave;re "
        "requ&ecirc;te paierait sinon une minute de d&eacute;marrage, qui "
        "ressemblerait &agrave; une panne. Connectez-vous une fois au tableau de "
        "bord. V&eacute;rifiez que les deux applications s'ouvrent sur le "
        "t&eacute;l&eacute;phone, charg&eacute;.", CORPS))
    h.append(Paragraph(
        "Ayez un rapport PDF d&eacute;j&agrave; produit sur votre machine. Si le "
        "r&eacute;seau l&acirc;che, dites-le simplement et ouvrez ce fichier : un "
        "incident annonc&eacute; calmement ne co&ucirc;te rien, un blanc de trente "
        "secondes pass&eacute; &agrave; recharger une page co&ucirc;te beaucoup. "
        "Pour la partie mobile, l'application fonctionne hors connexion par "
        "conception : coupez les donn&eacute;es, d&eacute;posez un signalement, et "
        "l'incident devient un argument.", CORPS))
    h.append(Paragraph(
        "R&eacute;p&eacute;tez deux fois &agrave; voix haute, chronom&egrave;tre en "
        "main. On ne d&eacute;couvre qu'on d&eacute;borde qu'en se "
        "chronom&eacute;trant, jamais en relisant.", CORPS))

    doc.build(h)
    print(f"PDF genere : {SORTIE.name}")


if __name__ == "__main__":
    construire()
