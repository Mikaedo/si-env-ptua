# -*- coding: utf-8 -*-
"""
mesures_reference.py
--------------------
Les grandeurs qu'un laboratoire agree mesure, et les valeurs limites
auxquelles les confronter (BF-08).

Contrairement aux seuils des indices satellitaires, calibres
empiriquement faute de norme transposable, ceux-ci sont reglementaires
ou recommandes par une autorite sanitaire. La distinction compte : le
memoire qualifie les premiers de « seuils de vigilance pour hierarchiser
les visites de terrain, non des seuils de conformite ». Ceux-ci, eux,
sont bien des seuils de conformite, et un depassement s'oppose a
l'entreprise.

Chaque valeur porte donc sa source. Un rapport transmis a la Banque
africaine de developpement doit pouvoir dire d'ou vient le nombre auquel
il compare la mesure.
"""

#: Les parametres mesurables, avec leur unite, leur limite et sa source.
#:
#: `limite` est la valeur au-dela de laquelle la mesure est non conforme.
#: `vigilance` marque l'approche du seuil : une mesure qui s'en approche
#: appelle un controle rapproche, sans etre encore un depassement.
PARAMETRES = {
    "BRUIT": {
        "libelle": "Niveau sonore",
        "unite": "dB(A)",
        "limite": 70.0,
        "vigilance": 60.0,
        "source": "Arrêté n°001164/MINEEF/CIAPOL/SDIIC du 4 novembre 2008, "
                  "zone d'habitation en période diurne",
    },
    "PM25": {
        "libelle": "Particules fines PM2,5",
        "unite": "µg/m³",
        "limite": 15.0,
        "vigilance": 10.0,
        "source": "Lignes directrices OMS 2021, moyenne sur 24 heures",
    },
    "PM10": {
        "libelle": "Particules PM10",
        "unite": "µg/m³",
        "limite": 45.0,
        "vigilance": 30.0,
        "source": "Lignes directrices OMS 2021, moyenne sur 24 heures",
    },
    "TURBIDITE": {
        "libelle": "Turbidité de l'eau",
        "unite": "NTU",
        "limite": 5.0,
        "vigilance": 3.0,
        "source": "Valeur usuelle de potabilité, OMS",
    },
}


def parametre_valide(code: str) -> bool:
    return code in PARAMETRES


def unite_de(code: str) -> str:
    """L'unite attendue pour un parametre.

    Elle n'est pas laissee au choix de celui qui saisit : une mesure de
    bruit exprimee en decibels bruts et une autre en dB(A) ne se
    comparent pas, et le rapport les additionnerait sans le savoir.
    """
    return PARAMETRES[code]["unite"]


def evaluer(code: str, valeur: float) -> str:
    """L'etat d'une mesure : CONFORME, VIGILANCE ou DEPASSEMENT.

    Le mot « depassement » est employe a dessein plutot que
    « critique » : il s'agit ici d'un depassement de valeur limite
    reglementaire, ce qui engage l'entreprise, non d'une appreciation.
    """
    reference = PARAMETRES[code]
    if valeur > reference["limite"]:
        return "DEPASSEMENT"
    if valeur > reference["vigilance"]:
        return "VIGILANCE"
    return "CONFORME"
