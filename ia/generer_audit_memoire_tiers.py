# -*- coding: utf-8 -*-
"""
Produit le rapport de conformite d'un memoire tiers.

Le document examine est celui de Toure Kinanglan Sara. La comparaison porte sur
deux references : les normes de presentation de l'UPB, telles qu'appliquees au
memoire SI-ENV, et ce memoire lui-meme pris comme mise en oeuvre de reference.

Le rapport separe volontairement ce qui est acquis de ce qui manque. Une
relecture qui n'enumere que des defauts se lit mal et se suit rarement : voir
d'abord ce qui est deja conforme situe l'effort restant, souvent plus faible
qu'il n'y parait. Ici, la mise en forme du corps est deja bonne, et l'essentiel
des corrections tient a des elements absents plutot qu'a des elements fautifs.

Les manques sont classes par gravite et non par ordre d'apparition. Un message
d'erreur de Word imprime dans le document se voit avant toute autre chose ;
une abreviation de legende, non.

Chaque constat porte son constat brut, ce qui a ete mesure et non deduit, pour
que l'interessee puisse verifier elle-meme.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (HRFlowable, KeepTogether, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

SORTIE = Path(r"C:\Users\DELL\Downloads\MEMOIRE\AUDIT_MEMOIRE_TOURE_KINANGLAN_SARA.pdf")

BLEU = colors.HexColor("#004F9F")
BLEU_SOMBRE = colors.HexColor("#003A73")
ROUGE = colors.HexColor("#B3261E")
ORANGE = colors.HexColor("#B25A00")
GRIS = colors.HexColor("#5A6B7F")
GRIS_CLAIR = colors.HexColor("#EFF3F8")
ENCRE = colors.HexColor("#101B2B")
FILET = colors.HexColor("#D7DEE9")

base = getSampleStyleSheet()

TITRE = ParagraphStyle("Titre", parent=base["Normal"], fontName="Helvetica-Bold",
                       fontSize=18, textColor=BLEU_SOMBRE, leading=22, spaceAfter=3)
SOUS = ParagraphStyle("Sous", parent=base["Normal"], fontName="Helvetica",
                      fontSize=10, textColor=GRIS, leading=14, spaceAfter=14)
H = ParagraphStyle("H", parent=base["Normal"], fontName="Helvetica-Bold",
                   fontSize=12.5, textColor=BLEU, spaceBefore=16, spaceAfter=6)
CORPS = ParagraphStyle("Corps", parent=base["Normal"], fontName="Helvetica",
                       fontSize=9.7, textColor=ENCRE, leading=14,
                       alignment=TA_JUSTIFY, spaceAfter=6)
NOTE = ParagraphStyle("Note", parent=CORPS, fontSize=8.7, textColor=GRIS,
                      spaceAfter=4)
CELL = ParagraphStyle("Cell", parent=base["Normal"], fontName="Helvetica",
                      fontSize=8.7, textColor=ENCRE, leading=12)
CELLG = ParagraphStyle("CellG", parent=CELL, fontName="Helvetica-Bold",
                       textColor=BLEU_SOMBRE)
POINT = ParagraphStyle("Point", parent=base["Normal"], fontName="Helvetica-Bold",
                       fontSize=10.5, textColor=ENCRE, spaceAfter=3)


def tableau(entetes, lignes, largeurs, couleurs_1re=None):
    donnees = [[Paragraph(e, CELLG) for e in entetes]]
    for l in lignes:
        donnees.append([Paragraph(str(c), CELL) for c in l])
    t = Table(donnees, colWidths=largeurs, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLAIR),
        ("GRID", (0, 0), (-1, -1), 0.5, FILET),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if couleurs_1re:
        for i, c in enumerate(couleurs_1re, start=1):
            style.append(("TEXTCOLOR", (0, i), (0, i), c))
            style.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
    t.setStyle(TableStyle(style))
    return t


def constat(numero, titre, mesure, pourquoi, quoi_faire):
    return KeepTogether([
        Paragraph(f"{numero}. {titre}", POINT),
        Paragraph(f"<b>Constat :</b> {mesure}", NOTE),
        Paragraph(pourquoi, CORPS),
        Paragraph(f"<b>&Agrave; faire :</b> {quoi_faire}", CORPS),
        HRFlowable(width="100%", thickness=0.5, color=FILET,
                   spaceBefore=2, spaceAfter=9),
    ])


def construire():
    doc = SimpleDocTemplate(
        str(SORTIE), pagesize=A4,
        leftMargin=2.1 * cm, rightMargin=2.1 * cm,
        topMargin=1.9 * cm, bottomMargin=1.8 * cm,
        title="Conformite du memoire, rapport de relecture",
        author="Relecture comparative")

    h = []

    h.append(Paragraph("Conformit&eacute; du m&eacute;moire", TITRE))
    h.append(Paragraph(
        "TOUR&Eacute; KINANGLAN SARA M.J. &middot; 55 pages, 9 178 mots, "
        "8 tableaux, 9 figures<br/>Relecture compar&eacute;e aux normes de "
        "pr&eacute;sentation de l'UPB", SOUS))

    h.append(Paragraph("Comment lire ce rapport", H))
    h.append(Paragraph(
        "Chaque constat indique d'abord ce qui a &eacute;t&eacute; "
        "<b>mesur&eacute;</b> dans le fichier, et non d&eacute;duit, afin que "
        "chaque point soit v&eacute;rifiable. Les manques sont class&eacute;s par "
        "gravit&eacute; et non par ordre d'apparition : un message d'erreur "
        "imprim&eacute; dans le document se voit avant tout le reste, une "
        "abr&eacute;viation de l&eacute;gende beaucoup moins.", CORPS))
    h.append(Paragraph(
        "La bonne nouvelle vient en premier, et elle compte : la mise en forme du "
        "corps est d&eacute;j&agrave; conforme. L'essentiel du travail restant "
        "porte sur des &eacute;l&eacute;ments <b>absents</b>, non sur des "
        "&eacute;l&eacute;ments &agrave; refaire.", CORPS))

    # --- Conforme -----------------------------------------------------------
    h.append(Paragraph("Ce qui est d&eacute;j&agrave; conforme", H))
    h.append(tableau(
        ["Point", "Mesur&eacute; dans le document"],
        [["Marges", "3 cm &agrave; gauche, 2,49 cm sur les trois autres c&ocirc;t&eacute;s. Conforme."],
         ["Justification", "142 paragraphes de corps sur 144 sont justifi&eacute;s."],
         ["Interligne", "1,5 sur 140 paragraphes de corps. Conforme."],
         ["Pages liminaires",
          "D&eacute;dicace, Remerciements, Avant-propos, Sommaire, Table des "
          "figures, Liste des tableaux, Liste des sigles. Toutes pr&eacute;sentes "
          "et dans le bon ordre."],
         ["Structure g&eacute;n&eacute;rale",
          "Introduction g&eacute;n&eacute;rale, trois parties, six chapitres, "
          "conclusion. Conforme au d&eacute;coupage attendu."],
         ["R&eacute;sum&eacute; et Abstract",
          "Pr&eacute;sents en fin de document, avec mots-cl&eacute;s et keywords."],
         ["Volume", "55 pages, coh&eacute;rent avec l'attendu d'un m&eacute;moire de licence."]],
        [4 * cm, 12.8 * cm]))

    # --- Bloquants ----------------------------------------------------------
    h.append(Paragraph("&Agrave; corriger en priorit&eacute;", H))
    h.append(Paragraph(
        "Ces quatre points se voient imm&eacute;diatement, avant m&ecirc;me la "
        "lecture du contenu.", CORPS))

    h.append(constat(
        1, "Un message d'erreur est imprim&eacute; dans le m&eacute;moire",
        "&agrave; l'emplacement de la Table des figures, le document affiche "
        "<i>&laquo; Erreur ! Aucune entr&eacute;e de table des illustrations n'a "
        "&eacute;t&eacute; trouv&eacute;e. &raquo;</i>",
        "C'est le d&eacute;faut le plus visible du document, et il sera remarqu&eacute; "
        "d&egrave;s les premi&egrave;res pages. Il ne vient pas d'un bug mais d'une "
        "cause simple : Word construit cette table &agrave; partir des "
        "l&eacute;gendes, et il n'en trouve aucune.",
        "corriger la cause, soit le point 2 ci-dessous, puis mettre le champ "
        "&agrave; jour (clic droit sur la table, Mettre &agrave; jour les champs)."))

    h.append(constat(
        2, "Les neuf figures n'ont aucune l&eacute;gende",
        "9 images ins&eacute;r&eacute;es, 0 l&eacute;gende. Le mot &laquo; Figure "
        "&raquo; suivi d'un num&eacute;ro n'appara&icirc;t nulle part dans le "
        "document.",
        "Une figure sans num&eacute;ro ne peut pas &ecirc;tre appel&eacute;e dans le "
        "texte. Or un lecteur doit pouvoir lire &laquo; comme le montre la figure "
        "3.2 &raquo; et s'y reporter. Sans l&eacute;gende, l'image flotte, et la "
        "table des figures reste vide.",
        "sous chaque image, ins&eacute;rer une l&eacute;gende centr&eacute;e du type "
        "<b>Figure 4.1 : Diagramme de cas d'utilisation.</b> Utiliser le style "
        "L&eacute;gende de Word pour que la table se g&eacute;n&egrave;re seule. "
        "Puis citer chaque figure au moins une fois dans le texte."))

    h.append(constat(
        3, "Aucun chapitre ne commence sur une page neuve",
        "les onze titres de partie et de chapitre s'encha&icirc;nent dans le fil du "
        "texte. Aucun saut de page n'a &eacute;t&eacute; trouv&eacute; avant eux, y "
        "compris avant l'Introduction g&eacute;n&eacute;rale et la Conclusion.",
        "La norme demande qu'une partie et un chapitre ouvrent leur propre page. "
        "C'est ce qui donne au document sa respiration et permet de le feuilleter.",
        "s&eacute;lectionner chaque titre de partie et de chapitre, puis dans "
        "Format, Paragraphe, Encha&icirc;nements, cocher <b>Saut de page avant</b>. "
        "&Eacute;viter d'ins&eacute;rer des lignes vides &agrave; la place : elles "
        "se d&eacute;calent d&egrave;s que le texte bouge."))

    h.append(constat(
        4, "Le Chapitre 5 n'est pas reconnu comme un titre",
        "&laquo; Chapitre 5 : Pr&eacute;sentation des r&eacute;sultats &raquo; porte "
        "le style Normal, alors que les cinq autres chapitres portent Titre 1.",
        "Cons&eacute;quence directe : ce chapitre n'appara&icirc;tra dans aucune "
        "table des mati&egrave;res automatique, et la hi&eacute;rarchie du document "
        "est rompue en son milieu. Ses sous-parties se retrouvent rattach&eacute;es "
        "&agrave; la troisi&egrave;me partie au lieu du chapitre.",
        "appliquer le style Titre 1 &agrave; ce paragraphe, comme aux autres "
        "chapitres."))

    # Pas de saut force ici : combine aux blocs insecables, il laissait une page
    # au quart remplie. Le texte trouve seul ses coupures.
    # --- Manquants ----------------------------------------------------------
    h.append(Paragraph("&Eacute;l&eacute;ments absents du document", H))

    h.append(constat(
        5, "Il n'y a pas de Table des mati&egrave;res",
        "aucune occurrence de &laquo; Table des mati&egrave;res &raquo;. Le "
        "document ne comporte qu'un Sommaire.",
        "Les deux ne se remplacent pas. Le Sommaire ouvre le m&eacute;moire et "
        "donne les grandes divisions ; la Table des mati&egrave;res le ferme et "
        "d&eacute;taille toutes les subdivisions avec leur pagination. Un jury s'en "
        "sert pour naviguer pendant la soutenance.",
        "en fin de document, ins&eacute;rer une table automatique par R&eacute;"
        "f&eacute;rences, Table des mati&egrave;res. Elle ne fonctionnera "
        "correctement qu'une fois le point 4 corrig&eacute;."))

    h.append(constat(
        6, "Le Sommaire ne porte aucune pagination",
        "les vingt-cinq entr&eacute;es du Sommaire sont sans num&eacute;ro de page.",
        "Un sommaire sans pagination ne remplit pas sa fonction, qui est de "
        "permettre d'atteindre une partie directement.",
        "ajouter le num&eacute;ro de page &agrave; chaque entr&eacute;e, align&eacute; "
        "&agrave; droite avec des points de conduite. Sous Word, un taquet de "
        "tabulation align&eacute; &agrave; droite avec points de suite, pos&eacute; "
        "&agrave; la marge."))

    h.append(constat(
        7, "Il n'y a pas de Bibliographie, seulement une Webographie",
        "le document se termine par une rubrique WEBOGRAPHIE. Aucune "
        "bibliographie.",
        "Un m&eacute;moire s'appuie sur des sources acad&eacute;miques et "
        "normatives, pas seulement sur des pages web. Le sujet trait&eacute; s'y "
        "pr&ecirc;te particuli&egrave;rement : la signature &eacute;lectronique, les "
        "certificats et le protocole OCSP sont d&eacute;finis par des normes "
        "publiques et cit&eacute;es partout dans la litt&eacute;rature.",
        "ajouter une Bibliographie et y faire figurer au moins les textes de "
        "r&eacute;f&eacute;rence du domaine : la norme d&eacute;crivant les "
        "certificats X.509, celle d&eacute;crivant OCSP, et le r&egrave;glement "
        "europ&eacute;en eIDAS sur l'identification &eacute;lectronique. Conserver "
        "la Webographie &agrave; part, ce qui est parfaitement admis."))

    h.append(constat(
        8, "Les trois parties n'ont pas de conclusion partielle",
        "aucune occurrence de &laquo; conclusion partielle &raquo;.",
        "Chaque partie se referme normalement sur un court bilan qui rappelle ce "
        "qui vient d'&ecirc;tre &eacute;tabli et annonce la suivante. C'est ce qui "
        "donne au m&eacute;moire sa continuit&eacute; : sans ces charni&egrave;res, "
        "les parties se juxtaposent au lieu de s'encha&icirc;ner.",
        "ajouter une dizaine de lignes en fin de chacune des trois parties. Une "
        "structure simple suffit : ce que la partie a &eacute;tabli, le point qui "
        "m&eacute;rite discussion, et ce que la partie suivante va traiter."))

    # --- Details ------------------------------------------------------------
    h.append(Paragraph("Corrections de d&eacute;tail", H))
    h.append(Paragraph(
        "Moins visibles, mais ce sont elles qui distinguent un document "
        "soign&eacute; d'un document simplement termin&eacute;.", CORPS))

    h.append(tableau(
        ["Ce qui est &eacute;crit", "Ce qu'il faut &eacute;crire", "Pourquoi"],
        [["Table 1, Table 2, ... Table 8",
          "Tableau 1, Tableau 2, ... Tableau 8",
          "&laquo; Table &raquo; est un anglicisme. La liste s'intitule d'ailleurs "
          "d&eacute;j&agrave; Liste des tableaux."],
         ["L&eacute;gendes enti&egrave;rement en capitales",
          "Capitale &agrave; l'initiale seulement",
          "Les capitales sur toute une ligne se lisent mal et perdent les accents."],
         ["Table 5: Le pattern MVC",
          "Tableau 5 : Le pattern MVC",
          "En fran&ccedil;ais, une espace pr&eacute;c&egrave;de le deux-points."],
         ["I.Historique, II.Missions",
          "I. Historique, II. Missions",
          "Une espace suit le num&eacute;ro. Et la troisi&egrave;me section du "
          "m&ecirc;me niveau, Organisations, n'est pas num&eacute;rot&eacute;e."],
         ["Digramme de s&eacute;quence",
          "Diagramme de s&eacute;quence",
          "Coquille dans un titre."],
         ["Cahier de charges",
          "Cahier des charges",
          "Coquille dans un titre, r&eacute;p&eacute;t&eacute;e dans le Sommaire."],
         ["contraintes",
          "Contraintes",
          "Titre commen&ccedil;ant par une minuscule."],
         ["Platefrome web, dans le Sommaire",
          "Plateforme web",
          "Coquille, et le Sommaire dit Conclusion g&eacute;n&eacute;rale quand le "
          "corps dit seulement Conclusion."]],
        [5.1 * cm, 4.8 * cm, 6.9 * cm]))

    # --- Ordre de travail ---------------------------------------------------
    h.append(Paragraph("Dans quel ordre proc&eacute;der", H))
    h.append(Paragraph(
        "L'ordre compte, plusieurs corrections d&eacute;pendant l'une de l'autre. "
        "Compter environ une demi-journ&eacute;e pour l'ensemble.", CORPS))
    h.append(tableau(
        ["&Eacute;tape", "Ce qu'on fait", "D&eacute;bloque"],
        [["1", "Appliquer Titre 1 au Chapitre 5",
          "La hi&eacute;rarchie du document"],
         ["2", "L&eacute;gender les neuf figures avec le style L&eacute;gende",
          "La table des figures, donc le message d'erreur"],
         ["3", "Mettre &agrave; jour la table des figures",
          "Le d&eacute;faut le plus visible dispara&icirc;t"],
         ["4", "Poser un saut de page avant chaque partie et chapitre",
          "La pagination devient stable"],
         ["5", "Ins&eacute;rer la Table des mati&egrave;res en fin de document",
          "Ne pouvait pas &ecirc;tre juste avant les &eacute;tapes 1 et 4"],
         ["6", "Paginer le Sommaire",
          "Les num&eacute;ros ne sont fiables qu'apr&egrave;s l'&eacute;tape 4"],
         ["7", "R&eacute;diger les trois conclusions partielles", ""],
         ["8", "Ajouter la Bibliographie", ""],
         ["9", "Reprendre les l&eacute;gendes et les coquilles", ""]],
        [1.5 * cm, 8.6 * cm, 6.7 * cm]))

    h.append(Spacer(1, 0.4 * cm))
    h.append(Paragraph(
        "Un dernier conseil de m&eacute;thode : apr&egrave;s l'&eacute;tape 4, "
        "relire le document en entier &agrave; l'&eacute;cran pour v&eacute;rifier "
        "qu'aucune page ne se retrouve &agrave; moiti&eacute; vide ni aucun titre "
        "seul en bas de page. Les sauts de page d&eacute;placent tout, et c'est "
        "toujours &agrave; ce moment que les d&eacute;fauts de mise en page "
        "apparaissent.", CORPS))

    doc.build(h)
    print(f"PDF genere : {SORTIE.name}")


if __name__ == "__main__":
    construire()
