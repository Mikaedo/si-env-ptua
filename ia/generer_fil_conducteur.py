# -*- coding: utf-8 -*-
"""
Produit le fil conducteur d'une presentation de dix minutes.

Un expose court ne se prepare pas comme un expose long que l'on abregerait :
il se construit au chronometre. Dix minutes autorisent environ mille quatre
cents mots dits posement, soit beaucoup moins que ce qu'un memoire de
quatre-vingt-sept pages voudrait raconter. Le document ci-dessous repartit donc
le temps avant de repartir le contenu, et indique a chaque etape ce qu'il faut
abandonner si l'on prend du retard.

Deux partis pris. Le premier est de faire tenir la these en une phrase des la
premiere minute : un auditoire qui ne sait pas ou on l'emmene ecoute mal.
Le second est d'assumer les limites a l'oral plutot que d'attendre qu'on les
releve, un candidat qui devance l'objection paraissant maitriser son sujet
quand celui qui la subit parait l'avoir manquee.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (HRFlowable, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

SORTIE = Path(r"C:\Users\DELL\Downloads\MEMOIRE\FIL_CONDUCTEUR_PRESENTATION_10MIN.pdf")

BLEU = colors.HexColor("#004F9F")
ORANGE = colors.HexColor("#F37021")
GRIS = colors.HexColor("#64748B")
GRIS_CLAIR = colors.HexColor("#F1F5F9")
ENCRE = colors.HexColor("#0F172A")

base = getSampleStyleSheet()

TITRE = ParagraphStyle("Titre", parent=base["Normal"], fontName="Helvetica-Bold",
                       fontSize=20, textColor=BLEU, leading=24, spaceAfter=4)
SOUS = ParagraphStyle("Sous", parent=base["Normal"], fontName="Helvetica",
                      fontSize=11, textColor=GRIS, leading=15, spaceAfter=16)
H = ParagraphStyle("H", parent=base["Normal"], fontName="Helvetica-Bold",
                   fontSize=13, textColor=BLEU, spaceBefore=16, spaceAfter=7)
CORPS = ParagraphStyle("Corps", parent=base["Normal"], fontName="Helvetica",
                       fontSize=10, textColor=ENCRE, leading=14.5,
                       alignment=TA_JUSTIFY, spaceAfter=7)
DIRE = ParagraphStyle("Dire", parent=CORPS, fontName="Helvetica-Oblique",
                      textColor=colors.HexColor("#1E3A5F"), leftIndent=12,
                      rightIndent=6, spaceBefore=3, spaceAfter=9)
NOTE = ParagraphStyle("Note", parent=CORPS, fontSize=9,
                      textColor=GRIS, spaceAfter=5)
MINUTE = ParagraphStyle("Minute", parent=base["Normal"], fontName="Helvetica-Bold",
                        fontSize=10.5, textColor=ORANGE, spaceAfter=2)


def sequence(temps, titre, montrer, dire, notes=None):
    """Une etape du deroule : sa duree, ce qu'on montre, ce qu'on dit."""
    blocs = [
        Paragraph(f"{temps} &nbsp;&nbsp;|&nbsp;&nbsp; {titre}", MINUTE),
        Paragraph(f"<b>À l'écran :</b> {montrer}", NOTE),
        Paragraph(dire, DIRE),
    ]
    if notes:
        blocs.append(Paragraph(notes, NOTE))
    blocs.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.HexColor("#E2E8F0"),
                            spaceBefore=2, spaceAfter=8))
    return blocs


def tableau(entetes, lignes, largeurs):
    donnees = [[Paragraph(f"<b>{e}</b>", NOTE) for e in entetes]]
    for l in lignes:
        donnees.append([Paragraph(str(c), NOTE) for c in l])
    t = Table(donnees, colWidths=largeurs)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLAIR),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def construire():
    doc = SimpleDocTemplate(str(SORTIE), pagesize=A4,
                            leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title="Fil conducteur, présentation de 10 minutes",
                            author="N'GUESSAN DIBY KONANBOUO Georges Mikaël")
    h = []

    h.append(Paragraph("Présenter le SI-ENV en dix minutes", TITRE))
    h.append(Paragraph("Fil conducteur minuté &middot; N'GUESSAN DIBY Konanbouo Georges Mikaël "
                       "&middot; AGEROUTE / CC-PTUA", SOUS))

    h.append(Paragraph("Avant de commencer", H))
    h.append(Paragraph(
        "Dix minutes représentent environ mille quatre cents mots dits posément. "
        "C'est peu : à peine de quoi poser un problème, montrer une réponse et "
        "reconnaître ses limites. Tout ce qui n'entre pas dans ce cadre doit "
        "attendre les questions, où vous aurez tout loisir de développer.", CORPS))
    h.append(Paragraph(
        "La règle qui sauve un exposé court : dire dès la première minute où "
        "vous emmenez l'auditoire. Un jury qui ne sait pas où l'on va écoute "
        "mal, et rattrape rarement.", CORPS))

    h.append(Paragraph("La thèse en une phrase", H))
    h.append(Paragraph(
        "Apprenez-la par cœur. C'est votre point de retour si vous perdez le fil, "
        "et votre réponse si l'on vous demande de résumer.", NOTE))
    h.append(Paragraph(
        "« Le suivi environnemental des chantiers du PTUA reposait sur du papier "
        "alors que le bailleur exige un rendu régulier ; j'ai construit un système "
        "qui capte l'information sur le terrain même sans réseau, la consolide, et "
        "produit le rapport réglementaire de façon vérifiable. »", DIRE))

    h.append(Paragraph("Le déroulé, minute par minute", H))

    for bloc in sequence(
        "0:00 – 1:15", "Le problème, pas le projet",
        "Rien, ou la figure 2.1 (processus actuel).",
        "« Le Projet de Transport Urbain d'Abidjan représente six cent "
        "cinquante-sept milliards de francs et il est classé Catégorie 1 par la "
        "Banque Africaine de Développement. Cela impose à l'AGEROUTE un suivi "
        "environnemental régulier. Dans les faits, ce suivi se faisait sur des "
        "fiches papier et des tableurs, sans base centralisée ni géolocalisation. "
        "Un incident pouvait rester ignoré plusieurs semaines. »",
        "Ne parlez pas encore de votre solution. Installez le manque d'abord : "
        "c'est lui qui rendra la suite nécessaire.",
    ):
        h.append(bloc)

    for bloc in sequence(
        "1:15 – 2:00", "La question et la contrainte",
        "Rien.",
        "« La question était donc : comment rendre ce suivi fiable et conforme, "
        "sans budget dédié et sans connexion Internet garantie sur les chantiers ? "
        "Ces deux contraintes ont commandé toute la conception. »",
        "La contrainte est votre meilleur argument : elle explique vos choix mieux "
        "que n'importe quelle justification technique.",
    ):
        h.append(bloc)

    for bloc in sequence(
        "2:00 – 5:00", "Ce que le système fait, en trois temps",
        "Le tableau de bord en ligne, puis l'application mobile.",
        "« Trois choses. D'abord, un agent saisit un signalement sur le terrain, "
        "avec photo et position, même sans réseau : les données partent dès que la "
        "connexion revient. Ensuite, tout se consolide sur un tableau de bord, "
        "croisé avec des indices satellitaires calculés par Google Earth Engine. "
        "Enfin, le rapport réglementaire se produit en quelques secondes, et sa "
        "remise à l'agence de tutelle est tracée. »",
        "Trois temps, trois phrases. Si la démonstration en direct est possible, "
        "montrez le dépôt d'un signalement puis son apparition sur le tableau de "
        "bord : c'est la séquence qui frappe le plus.",
    ):
        h.append(bloc)

    for bloc in sequence(
        "5:00 – 6:30", "Les deux décisions qui vous distinguent",
        "L'application citoyenne, ou la matrice des habilitations.",
        "« Deux décisions méritent d'être expliquées. La première : la "
        "reconnaissance d'images tourne sur le téléphone et non sur un serveur. "
        "On y perd en précision, mais on peut travailler là où le réseau manque, "
        "c'est-à-dire justement sur les chantiers. La seconde : j'ai ouvert le "
        "dispositif aux riverains par une application distincte, qui ne s'active "
        "que si la personne se trouve dans la zone d'influence d'un chantier. »",
        "C'est ici que se joue la note. Un jury retient les arbitrages, pas les "
        "fonctionnalités.",
    ):
        h.append(bloc)

    for bloc in sequence(
        "6:30 – 7:30", "Les résultats, chiffrés",
        "Les métriques du modèle, ou rien.",
        "« Le modèle de détection atteint quatre-vingts pour cent de précision "
        "moyenne sur six classes de déchets, avec un temps d'inférence de l'ordre "
        "de vingt millisecondes. Le système compte cent dix-neuf tests automatisés, "
        "rejoués à chaque modification du code. Il est déployé et accessible en "
        "ligne. »",
        "Trois chiffres suffisent. En annoncer dix revient à n'en faire retenir "
        "aucun.",
    ):
        h.append(bloc)

    for bloc in sequence(
        "7:30 – 8:45", "Les limites, assumées avant qu'on les relève",
        "Rien.",
        "« Ce travail a des limites que je tiens à dire. Le système n'a pas été "
        "utilisé en conditions réelles par des agents qui ne l'ont pas conçu, et "
        "c'est le seul essai qui permettrait de juger de son ergonomie. Le corpus "
        "d'entraînement vient de sources ouvertes et ne reflète pas parfaitement "
        "les chantiers d'Abidjan. Et la vérification de position atteste d'une "
        "localisation, pas d'une résidence. »",
        "Un candidat qui devance l'objection paraît maîtriser son sujet. Celui qui "
        "la subit paraît l'avoir manquée.",
    ):
        h.append(bloc)

    for bloc in sequence(
        "8:45 – 10:00", "Ce que vous en retirez",
        "Rien. Regardez le jury.",
        "« Ces limites dessinent la suite : une phase pilote sur un chantier, un "
        "corpus enrichi de photographies réelles, et le passage à un hébergement "
        "de production, qui ne demande qu'un changement de paramètres. Sur le plan "
        "personnel, ce projet m'a moins appris à écrire du code qu'à décider : "
        "arbitrer entre un modèle précis et un modèle rapide, accepter qu'une "
        "fonctionnalité utile ne soit pas prioritaire. Je vous remercie. »",
        "Terminez sur le regard, pas sur l'écran. Le silence qui suit vous "
        "appartient : ne le comblez pas.",
    ):
        h.append(bloc)

    h.append(PageBreak())

    h.append(Paragraph("Si vous prenez du retard", H))
    h.append(Paragraph(
        "Sacrifiez dans cet ordre, sans hésiter. Ce qui suit peut disparaître "
        "entièrement sans que l'exposé perde son sens.", CORPS))
    h.append(tableau(
        ["À sacrifier en premier", "Pourquoi c'est possible"],
        [["Les chiffres des résultats (6:30)",
          "Ils figurent dans le mémoire ; le jury les retrouvera. Gardez-en un seul."],
         ["Le détail des trois temps (2:00)",
          "Dites « le système capte, consolide et produit le rapport », puis passez."],
         ["La deuxième décision, l'application citoyenne",
          "Gardez celle de l'intelligence artificielle embarquée, plus liée à la contrainte."]],
        [7.2 * cm, 9.4 * cm]))
    h.append(Spacer(1, 0.5 * cm))
    h.append(Paragraph(
        "Ne sacrifiez jamais la première minute ni la dernière. Le problème et "
        "l'apport personnel sont ce qu'un jury retient d'un exposé court.", CORPS))

    h.append(Paragraph("Les chiffres à connaître sans hésiter", H))
    h.append(tableau(
        ["Grandeur", "Valeur"],
        [["Coût du PTUA", "657,8 milliards de FCFA, Catégorie 1 BAD"],
         ["Profils utilisateurs", "8, dont 2 en consultation seule et 1 riverain"],
         ["Applications produites", "2 mobiles et 1 tableau de bord web"],
         ["Tests automatisés", "119, rejoués à chaque modification"],
         ["Détection de déchets", "80,7 % de mAP@0.5 sur 6 classes"],
         ["Inférence embarquée", "de 9 à 24 millisecondes"],
         ["Coût d'hébergement actuel", "nul, sans carte bancaire"]],
        [6.4 * cm, 10.2 * cm]))

    h.append(Paragraph("Trois pièges de l'exposé court", H))
    h.append(Paragraph(
        "<b>Commencer par la technique.</b> « J'ai utilisé FastAPI, Flutter et "
        "PostGIS » ne dit rien à qui ignore le problème. Les technologies viennent "
        "après le besoin, jamais avant.", CORPS))
    h.append(Paragraph(
        "<b>Vouloir tout montrer.</b> Une démonstration qui enchaîne huit écrans "
        "en trois minutes ne laisse aucune trace. Deux écrans montrés lentement "
        "valent mieux.", CORPS))
    h.append(Paragraph(
        "<b>Lire ses notes.</b> Ce document est un fil conducteur, pas un texte à "
        "réciter. Retenez l'ordre des idées et la phrase de thèse ; le reste doit "
        "sortir de vous, avec vos mots.", CORPS))

    h.append(PageBreak())

    h.append(Paragraph("La démonstration, pas à pas", H))
    h.append(Paragraph(
        "Un exposé qui commente un document se subit ; un exposé qui montre un "
        "système qui fonctionne se retient. Voici le parcours exact, calibré sur "
        "les trois minutes du bloc 2:00. Répétez-le jusqu'à ne plus avoir à "
        "chercher un bouton en direct : une hésitation de dix secondes devant un "
        "menu coûte plus qu'une phrase mal tournée.", CORPS))
    h.append(tableau(
        ["Étape", "Ce que vous faites", "Ce que cela prouve"],
        [["1. Ouvrir le tableau de bord",
          "si-env-ptua.pages.dev, compte spec.env@ageroute.ci",
          "Le système est en ligne, pas sur votre machine."],
         ["2. Montrer un signalement géolocalisé",
          "Onglet Signalements, ouvrir une fiche avec sa photo et sa position",
          "La donnée de terrain arrive complète et située."],
         ["3. Basculer sur la carte",
          "Onglet Cartographie, activer la vue satellite",
          "Les remontées se lisent dans l'espace, pas en liste."],
         ["4. Lancer une analyse satellitaire",
          "Onglet Analyse satellitaire, choisir un chantier",
          "Les indices viennent de Google Earth Engine, en direct."],
         ["5. Produire le rapport PGES",
          "Onglet Rapports, générer puis ouvrir le PDF",
          "L'obligation réglementaire est tenue en quelques secondes."],
         ["6. Ouvrir l'application citoyenne",
          "Sur le téléphone, écran d'accueil et dépôt d'une doléance",
          "Le riverain a un canal, conditionné à sa position."]],
        [4.0 * cm, 6.4 * cm, 6.2 * cm]))
    h.append(Spacer(1, 0.4 * cm))
    h.append(Paragraph(
        "Si le temps manque, gardez les étapes 1, 5 et 6. Elles suffisent à "
        "établir la chaîne complète : la donnée entre, le rapport sort, et le "
        "riverain y a sa place.", CORPS))

    h.append(Paragraph("Si la connexion vous lâche", H))
    h.append(Paragraph(
        "C'est le risque le plus banal et le plus mal encaissé. Préparez-le au "
        "lieu de l'espérer.", CORPS))
    h.append(Paragraph(
        "Ayez sur votre machine un rapport PGES déjà produit, en PDF, et les "
        "captures d'écran des annexes du mémoire. Si le réseau tombe, dites-le "
        "simplement, ouvrez ces fichiers et poursuivez : « le service est "
        "hébergé en ligne, je vous montre le résultat produit ce matin. » "
        "Un incident annoncé calmement ne coûte rien ; un blanc de trente "
        "secondes passé à recharger une page coûte beaucoup.", CORPS))
    h.append(Paragraph(
        "Pour la partie mobile, l'application fonctionne hors connexion par "
        "conception : c'est même une occasion de le prouver. Coupez les données "
        "du téléphone, déposez un signalement, montrez qu'il est enregistré. "
        "L'incident devient un argument.", CORPS))

    h.append(Paragraph("Avant d'entrer", H))
    h.append(Paragraph(
        "Ouvrez le tableau de bord et connectez-vous une fois, pour que la session "
        "soit active. Vérifiez que le téléphone est chargé et que les deux "
        "applications s'ouvrent. Ayez le PDF du mémoire accessible, au cas où l'on "
        "vous renvoie à une figure.", CORPS))
    h.append(Paragraph(
        "Répétez au moins deux fois à voix haute, chronomètre en main. On ne "
        "découvre qu'on déborde qu'en se chronométrant, jamais en relisant.", CORPS))

    doc.build(h)
    print(f"PDF genere : {SORTIE.name}")


if __name__ == "__main__":
    construire()
