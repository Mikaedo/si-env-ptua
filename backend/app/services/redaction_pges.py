"""
redaction_pges.py
-----------------
Redaction du commentaire accompagnant le rapport de suivi environnemental.

Un rapport remis a une agence de tutelle ou a un bailleur ne se resume pas a
des tableaux. Les chiffres disent combien, jamais ce qu'il faut en penser :
trente signalements sur un trimestre peuvent traduire une vigilance accrue
comme une degradation reelle, et rien ne permet de trancher sans commentaire.
Les textes fixes qui figuraient auparavant en introduction et en conclusion ne
repondaient pas a ce besoin, puisqu'ils restaient identiques d'un rapport a
l'autre, quelles que soient les donnees.

Ce module produit donc des paragraphes qui varient avec la situation decrite.
Il ne s'agit pas de generation de langage au sens statistique : les tournures
sont ecrites a la main, et le code choisit celle qui correspond a la
configuration rencontree. Un rapport ou tout est clos ne peut pas se lire
comme un rapport ou la moitie des dossiers reste ouverte.

Deux precautions guident la redaction. La premiere est de ne jamais affirmer
plus que ce que les donnees etablissent : le systeme constate des volumes et
des delais, il ne se prononce pas sur la qualite environnementale reelle d'un
chantier, qui releve d'une expertise de terrain. La seconde est de nommer les
choses, un rapport qui parlerait de « nuisances » sans jamais dire lesquelles
n'apprendrait rien a son lecteur.
"""
from __future__ import annotations

from datetime import datetime

# ── Vocabulaire ───────────────────────────────────────────────────────────

MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

#: Designation des organismes destinataires, telle qu'elle doit apparaitre
#: dans un document officiel.
ORGANISMES = {
    "ANDE": "l'Agence Nationale de l'Environnement",
    "BAD": "la Banque Africaine de Développement",
    "AGEROUTE": "l'Agence de Gestion des Routes",
    "CC-PTUA": "la Cellule de Coordination du PTUA",
    "BEIE": "le Bureau d'Études d'Impact Environnemental",
}


def _date_lisible(valeur: str | None) -> str | None:
    """Transforme une date ISO en formulation courante.

    « 2026-01-01 » devient « 1er janvier 2026 », le format ISO n'ayant sa
    place que dans un fichier, pas dans une phrase.
    """
    if not valeur:
        return None
    try:
        d = datetime.strptime(valeur, "%Y-%m-%d")
    except ValueError:
        return valeur
    jour = "1er" if d.day == 1 else str(d.day)
    return f"{jour} {MOIS[d.month - 1]} {d.year}"


def periode_redigee(debut: str | None, fin: str | None) -> str:
    """Formule la periode couverte, en s'adaptant aux bornes disponibles."""
    d, f = _date_lisible(debut), _date_lisible(fin)
    if d and f:
        return f"du {d} au {f}"
    if f:
        return f"jusqu'au {f}"
    if d:
        return f"depuis le {d}"
    return "sur l'ensemble de la période disponible"


def _accord(n: int, singulier: str, pluriel: str | None = None) -> str:
    """Accorde un substantif avec son effectif."""
    if n <= 1:
        return f"{n} {singulier}"
    return f"{n} {pluriel or singulier + 's'}"


def _enumerer(elements: list[str]) -> str:
    """Enumere en francais, avec « et » avant le dernier terme."""
    if not elements:
        return ""
    if len(elements) == 1:
        return elements[0]
    return ", ".join(elements[:-1]) + " et " + elements[-1]


# ── Agregats ──────────────────────────────────────────────────────────────

def totaliser(chantiers: list[dict]) -> dict:
    """Cumule les chiffres de tous les chantiers du perimetre."""
    cles = (
        "nb_signalements", "nb_alertes", "nb_plaintes", "nb_non_conformites",
        "nb_traites", "nb_en_cours", "nb_nouveaux", "nb_eleves",
        "nb_plaintes_ouvertes", "nb_plaintes_mobile", "nb_nc_ouvertes",
    )
    total = {c: sum(ch.get(c, 0) or 0 for ch in chantiers) for c in cles}
    total["nb_chantiers"] = len(chantiers)

    signalements = total["nb_signalements"]
    total["taux_traitement"] = (
        round(100 * total["nb_traites"] / signalements) if signalements else 0
    )

    # Nuisances dominantes sur l'ensemble du perimetre.
    cumul: dict[str, int] = {}
    for ch in chantiers:
        for t in ch.get("types_frequents") or []:
            cumul[t["type"]] = cumul.get(t["type"], 0) + t["n"]
    total["types_dominants"] = sorted(
        cumul.items(), key=lambda x: x[1], reverse=True
    )[:3]
    return total


# ── Paragraphes ───────────────────────────────────────────────────────────

def introduction(chantiers: list[dict], debut, fin, organisme: str) -> str:
    """Rappelle l'objet du document, son perimetre et sa provenance."""
    t = totaliser(chantiers)
    destinataire = ORGANISMES.get((organisme or "").upper(), organisme or "l'organisme destinataire")
    periode = periode_redigee(debut, fin)

    if t["nb_chantiers"] == 1:
        perimetre = f"le chantier de {chantiers[0]['nom']}"
        if chantiers[0].get("commune"):
            perimetre += f", dans la commune de {chantiers[0]['commune']}"
    else:
        communes = sorted({c["commune"] for c in chantiers if c.get("commune")})
        perimetre = f"{t['nb_chantiers']} chantiers du programme"
        if communes:
            perimetre += f", répartis sur {_enumerer(communes)}"

    return (
        f"Le présent rapport rend compte du suivi environnemental et social conduit "
        f"{periode} sur {perimetre}. Il est établi à l'intention de {destinataire}, "
        f"au titre du Plan de Gestion Environnementale et Sociale du Projet de Transport "
        f"Urbain d'Abidjan.<br/><br/>"
        f"Les éléments qui suivent proviennent du système d'information environnemental "
        f"de l'AGEROUTE, alimenté en continu par les agents de terrain depuis leur "
        f"téléphone, par les riverains au titre du mécanisme de gestion des plaintes, "
        f"et par le traitement automatisé d'images satellitaires. Chaque signalement y "
        f"est horodaté et géolocalisé au moment de sa saisie, ce qui garantit la "
        f"traçabilité des constats rapportés ici."
    )


def synthese(chantiers: list[dict], debut, fin) -> str:
    """Commente les volumes globaux et l'avancement du traitement."""
    t = totaliser(chantiers)
    sig = t["nb_signalements"]

    if sig == 0:
        return (
            "Aucun signalement n'a été enregistré sur le périmètre et la période "
            "considérés. Cette absence appelle une lecture prudente : elle peut "
            "traduire une situation effectivement maîtrisée, mais également un "
            "défaut de remontée depuis le terrain. Il est recommandé de la "
            "rapprocher des comptes rendus de visite de chantier avant d'en tirer "
            "une conclusion."
        )

    phrases = []

    # Volume et nature des constats.
    ouverture = (
        f"Sur la période, {_accord(sig, 'signalement')} "
        f"{'a été enregistré' if sig == 1 else 'ont été enregistrés'} "
        f"sur {_accord(t['nb_chantiers'], 'chantier')} suivi"
        f"{'s' if t['nb_chantiers'] > 1 else ''}."
    )
    if t["types_dominants"]:
        libelles = [f"{nom.lower()} ({n})" for nom, n in t["types_dominants"]]
        ouverture += (
            f" Les constats portent principalement sur {_enumerer(libelles)}."
        )
    phrases.append(ouverture)

    # Avancement du traitement, lu comme un indicateur de reactivite.
    taux = t["taux_traitement"]
    if taux >= 80:
        appreciation = (
            f"Le taux de clôture s'établit à {taux} %, ce qui traduit une prise en "
            f"charge suivie des constats remontés."
        )
    elif taux >= 50:
        appreciation = (
            f"Le taux de clôture s'établit à {taux} %. La moitié au moins des "
            f"constats a donc trouvé une issue, mais le solde reste significatif."
        )
    else:
        appreciation = (
            f"Le taux de clôture s'établit à {taux} %, niveau qui appelle une "
            f"attention particulière : la majorité des constats demeure sans "
            f"traitement abouti à la date du présent rapport."
        )
    if t["nb_en_cours"] or t["nb_nouveaux"]:
        reste = []
        if t["nb_en_cours"]:
            reste.append(f"{t['nb_en_cours']} en cours d'instruction")
        if t["nb_nouveaux"]:
            reste.append(f"{t['nb_nouveaux']} en attente de prise en charge")
        appreciation += f" Le solde se répartit entre {_enumerer(reste)}."
    phrases.append(appreciation)

    # Gravite.
    if t["nb_eleves"]:
        part = round(100 * t["nb_eleves"] / sig)
        phrases.append(
            f"{_accord(t['nb_eleves'], 'signalement')} "
            f"{'a été classé' if t['nb_eleves'] == 1 else 'ont été classés'} en "
            f"criticité élevée, soit {part} % du total. Ces situations justifient "
            f"un traitement prioritaire et un contrôle de la levée effective des "
            f"mesures correctives."
        )
    else:
        phrases.append(
            "Aucun signalement n'a été classé en criticité élevée sur la période."
        )

    # Volet social.
    if t["nb_plaintes"]:
        social = (
            f"Au titre du mécanisme de gestion des plaintes, "
            f"{_accord(t['nb_plaintes'], 'doléance')} "
            f"{'a été reçue' if t['nb_plaintes'] == 1 else 'ont été reçues'}"
        )
        if t["nb_plaintes_mobile"]:
            social += (
                f", dont {t['nb_plaintes_mobile']} déposée"
                f"{'s' if t['nb_plaintes_mobile'] > 1 else ''} directement par des "
                f"riverains depuis l'application mobile mise à leur disposition"
            )
        social += "."
        if t["nb_plaintes_ouvertes"]:
            social += (
                f" {_accord(t['nb_plaintes_ouvertes'], 'dossier')} "
                f"{'reste ouvert' if t['nb_plaintes_ouvertes'] == 1 else 'restent ouverts'} "
                f"à ce jour."
            )
        else:
            social += " L'ensemble de ces dossiers a été clos."
        phrases.append(social)

    # Non-conformites, point le plus scruté par un auditeur.
    if t["nb_non_conformites"]:
        nc = (
            f"{_accord(t['nb_non_conformites'], 'non-conformité')} "
            f"{'a été relevée' if t['nb_non_conformites'] == 1 else 'ont été relevées'}"
        )
        if t["nb_nc_ouvertes"]:
            nc += (
                f", dont {t['nb_nc_ouvertes']} "
                f"{'demeure non résolue' if t['nb_nc_ouvertes'] == 1 else 'demeurent non résolues'}. "
                f"Leur régularisation conditionne la conformité du projet aux "
                f"engagements souscrits."
            )
        else:
            nc += ", toutes régularisées à la date du présent rapport."
        phrases.append(nc)

    return "<br/><br/>".join(phrases)


def commentaire_chantier(chantier: dict) -> str:
    """Redige l'analyse propre a un chantier, placee avant ses tableaux."""
    sig = chantier.get("nb_signalements", 0)
    nom = chantier["nom"]

    if sig == 0 and not chantier.get("nb_plaintes"):
        return (
            f"Aucun constat n'a été rapporté sur ce chantier durant la période. "
            f"Il est recommandé de vérifier que les équipes affectées à "
            f"{nom} disposent bien de l'application de terrain et l'utilisent."
        )

    elements = []

    if sig:
        phrase = f"Ce chantier totalise {_accord(sig, 'signalement')}"
        types = chantier.get("types_frequents") or []
        if types:
            principal = types[0]
            phrase += (
                f", dont la nature dominante est « {principal['type'].lower()} » "
                f"({principal['n']} occurrence{'s' if principal['n'] > 1 else ''})"
            )
        phrase += "."
        elements.append(phrase)

        traites = chantier.get("nb_traites", 0)
        if traites == sig:
            elements.append("L'intégralité de ces constats a été clôturée.")
        elif traites:
            elements.append(
                f"{traites} ont été clôturés, {sig - traites} restent à traiter."
            )
        else:
            elements.append(
                "Aucun de ces constats n'a encore été clôturé, ce qui appelle "
                "un point de situation avec l'entreprise attributaire."
            )

    if chantier.get("nb_eleves"):
        elements.append(
            f"{_accord(chantier['nb_eleves'], 'situation')} de criticité élevée "
            f"{'y a été relevée' if chantier['nb_eleves'] == 1 else 'y ont été relevées'}."
        )

    if chantier.get("nb_plaintes"):
        p = (
            f"{_accord(chantier['nb_plaintes'], 'doléance')} de riverains "
            f"{'a été enregistrée' if chantier['nb_plaintes'] == 1 else 'ont été enregistrées'}"
        )
        if chantier.get("nb_plaintes_ouvertes"):
            p += f", dont {chantier['nb_plaintes_ouvertes']} en cours de traitement"
        p += "."
        elements.append(p)

    if chantier.get("nb_alertes"):
        elements.append(
            f"Le suivi satellitaire a par ailleurs déclenché "
            f"{_accord(chantier['nb_alertes'], 'alerte')} par dépassement de seuil."
        )

    if chantier.get("nb_nc_ouvertes"):
        elements.append(
            f"{_accord(chantier['nb_nc_ouvertes'], 'non-conformité')} "
            f"{'reste à régulariser' if chantier['nb_nc_ouvertes'] == 1 else 'restent à régulariser'} "
            f"sur ce site."
        )

    return " ".join(elements)


def conclusion(chantiers: list[dict], debut, fin) -> str:
    """Formule les recommandations decoulant de la situation constatee."""
    t = totaliser(chantiers)
    recommandations = []

    # Chaque recommandation est formulee comme une action, avec le motif qui la
    # justifie. Une recommandation sans motif se lit comme une exigence
    # arbitraire, et le destinataire n'a aucun moyen d'en apprecier l'urgence.
    if t["nb_nc_ouvertes"]:
        recommandations.append((
            f"Régulariser {_accord(t['nb_nc_ouvertes'], 'non-conformité')} "
            f"{'encore ouverte' if t['nb_nc_ouvertes'] == 1 else 'encore ouvertes'}.",
            "Leur persistance constitue le point le plus directement opposable "
            "au projet lors d'un contrôle.",
        ))
    if t["nb_eleves"]:
        recommandations.append((
            f"Vérifier la levée effective des mesures correctives sur "
            f"{_accord(t['nb_eleves'], 'situation')} de criticité élevée.",
            "Le classement en criticité élevée suppose une action rapide, dont "
            "l'aboutissement doit être constaté sur le terrain.",
        ))
    if t["nb_plaintes_ouvertes"]:
        recommandations.append((
            f"Apporter une réponse aux {t['nb_plaintes_ouvertes']} doléances de "
            f"riverains restées sans issue.",
            "Le délai de traitement des plaintes figure parmi les indicateurs "
            "suivis au titre des sauvegardes du bailleur.",
        ))
    if t["taux_traitement"] < 50 and t["nb_signalements"]:
        recommandations.append((
            "Renforcer la chaîne de traitement des signalements.",
            f"Avec un taux de clôture de {t['taux_traitement']} %, la majorité "
            f"des constats remontés reste sans issue formalisée.",
        ))

    if recommandations:
        # Presentation verticale : au-dela de deux points, une enumeration en
        # ligne devient illisible, les justifications comportant elles-memes
        # des virgules.
        lignes = "".join(
            f"<br/><br/><b>{i}.</b> {action}<br/>"
            f"<font color='#71717A'>{motif}</font>"
            for i, (action, motif) in enumerate(recommandations, start=1)
        )
        corps = (
            "Au vu des éléments rassemblés, les actions suivantes sont "
            "recommandées pour la période à venir." + lignes
        )
    else:
        corps = (
            "Aucune situation appelant une action corrective immédiate n'a été "
            "identifiée sur la période. Les constats remontés ont tous trouvé une "
            "issue, et aucune non-conformité ne demeure ouverte."
        )

    return (
        f"{corps}<br/><br/>"
        f"Le suivi environnemental et social est un exercice continu, dont la valeur "
        f"tient à la régularité des remontées autant qu'à la rapidité des réponses "
        f"apportées. Les chiffres présentés dans ce rapport décrivent ce qui a été "
        f"consigné dans le système ; ils ne dispensent pas des visites de terrain, "
        f"qui seules permettent d'apprécier la réalité des mesures d'atténuation "
        f"mises en œuvre.<br/><br/>"
        f"Le prochain rapport couvrira la période suivante et permettra d'apprécier "
        f"l'évolution des indicateurs ici consignés."
    )
