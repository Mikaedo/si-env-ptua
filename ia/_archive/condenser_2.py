# -*- coding: utf-8 -*-
"""
Deuxieme passe de condensation pour ramener a 50 pages :
  - §5.13 : long paragraphe d'analyse ONNX condense (les conclusions sont
    deja dans §5.8 et §5.11)
  - §6.8 : tableau 6.7 supprime, ses infos deja decrites dans le paragraphe
    precedent
"""
import docx

CHEMIN = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_FINAL.docx"
d = docx.Document(CHEMIN)


def par(debut):
    for p in d.paragraphs:
        if p.text.strip().startswith(debut):
            return p
    raise SystemExit("INTROUVABLE : " + debut[:70])


def remplacer(p, vieux, neuf):
    if vieux not in p.text:
        raise SystemExit("FRAGMENT : " + vieux[:70])
    p.runs[0].text = p.text.replace(vieux, neuf)
    for r in p.runs[1:]:
        r.text = ""


def supprimer(p):
    p._p.getparent().remove(p._p)


# ─── §5.13 : long paragraphe d'analyse condense ────────────────────────
p513b = par("Les faux négatifs observés pour YOLOv8")
remplacer(
    p513b,
    "Les faux négatifs observés pour YOLOv8 (figure 5.6) concernent principalement la classe plastique (Rappel = 0,559), due à la transparence et au faible contraste des objets en plastique. Les faux positifs les plus probables portent sur des matériaux de chantier visuellement proches de déchets (gravats, débris de coffrage). Pour MobileNetV2, la classification est plus fiable sur la classe faible (F1 = 0,93) que sur les classes modérée (F1 = 0,59) et importante (F1 = 0,67). Le déséquilibre du corpus y contribue, et l'usage d'un WeightedRandomSampler et de poids de classe l'a atténué sans le supprimer. La cause principale tient cependant à la nature de l'étiquette : la criticité étant définie par le nombre d'objets (section 5.8), séparer cinq objets de six revient à dénombrer, ce pour quoi un classifieur d'image entière n'est pas conçu. Deux conséquences orientent la suite. La criticité peut d'abord être obtenue sans second réseau, en comptant les objets retournés par le détecteur et en leur appliquant la même règle, voie plus économe et aussi fidèle à la définition retenue : c'est le comparateur naturel du classifieur. Ensuite, la seule décision utile à l'agent est binaire, intervenir ou non ; regrouper modérée et importante en une classe élevée écarte la frontière la plus instable. Ce module doit donc être lu comme une démonstration de faisabilité de l'inférence embarquée, non comme un dispositif de mesure de la gravité, la criticité déclarée par l'agent restant la valeur de référence enregistrée.",
    "Les faux négatifs de YOLOv8 (figure 5.6) portent surtout sur la classe "
    "plastique (Rappel = 0,559), du fait de la transparence des objets. Pour "
    "MobileNetV2, la classification est fiable sur la classe faible "
    "(F1 = 0,93) mais bornée sur les classes intermédiaires (F1 = 0,59 et "
    "0,67), pour les raisons discutées à la section 5.8 : la criticité étant "
    "définie par le nombre d'objets, séparer cinq objets de six relève du "
    "dénombrement plus que de la reconnaissance de forme. La règle retenue "
    "au terme du benchmark, exposée en 5.8, écarte cette classe intermédiaire "
    "au profit du comptage direct des détections du premier réseau.",
)

# ─── §6.8 : retirer le tableau 6.7 et le paragraphe qui l'introduit ────
# Le paragraphe descriptif precedent est deja suffisant : on retire donc les
# lignes "Tableau 6.7 : ..." et le tableau lui-meme.

titre_tbl67 = par("Tableau 6.7 : Couches du dispositif de haute disponibilité")
# Trouver l'element table qui suit immediatement le titre
element_tbl = titre_tbl67._p.getnext()
if element_tbl is not None and element_tbl.tag.endswith("}tbl"):
    element_tbl.getparent().remove(element_tbl)
supprimer(titre_tbl67)

# La description textuelle des trois couches est deja dans le paragraphe
# precedent. On l'enrichit legerement pour ne rien perdre.
p_couches = par(
    "L'hébergement gratuit a une limite structurelle bien documentée"
)
remplacer(
    p_couches,
    "Un dispositif de surveillance actif a "
    "donc été ajouté, en trois couches complémentaires décrites au tableau 6.7.",
    "Un dispositif de surveillance actif a "
    "donc été ajouté, en trois couches complémentaires. Un premier processus "
    "toutes les trois minutes, sans interruption, interroge le backend et la "
    "base pour maintenir les services chauds. Un second processus horaire "
    "rejoue la chaîne complète (authentification, requête PostGIS, accès au "
    "bucket photos), ce qu'un simple ping ne détecterait pas. En cas d'échec "
    "persistant, un troisième processus tente en cascade un redémarrage doux, "
    "puis un redémarrage complet, puis une republication du backend, puis un "
    "nouveau peuplement de la base ; à défaut, une issue GitHub est ouverte "
    "automatiquement, ce qui déclenche un courriel d'alerte."
)

d.save(CHEMIN)
print("§5.13 raccourci, tableau 6.7 remplacé par du texte fluide.")
