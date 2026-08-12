"""
journal_service.py
------------------
Journal d'audit centralise du SI-ENV (section 5.7 du memoire).

Toutes les routes passent par `journaliser()` plutot que d'instancier
`models.Journal` directement : cela garantit que chaque entree porte le meme
jeu d'informations (horodatage UTC, niveau, utilisateur, adresse IP) quelle
que soit la partie du systeme qui l'emet.

L'ecriture ne fait qu'un `db.add()` : le `commit()` reste a la charge de la
route appelante, pour que l'evenement soit valide dans la meme transaction que
l'action qu'il decrit. Une action annulee ne laisse donc pas de trace
mensongere dans le journal.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from .. import models

# Niveaux utilises dans le systeme, du moins au plus grave.
NIVEAU_INFO = "INFO"
NIVEAU_WARNING = "WARNING"
NIVEAU_ERROR = "ERROR"

# Duree de conservation des traces d'audit (section 5.7 du memoire).
RETENTION_JOURS = 30


def adresse_ip(request: Optional[Request]) -> Optional[str]:
    """Adresse IP de l'appelant.

    Derriere le reverse proxy nginx, `request.client.host` vaut l'IP du
    conteneur nginx et non celle de l'agent : on privilegie donc l'en-tete
    X-Forwarded-For, dont le premier element est le client d'origine.
    """
    if request is None:
        return None
    transmise = request.headers.get("x-forwarded-for")
    if transmise:
        return transmise.split(",")[0].strip()
    return request.client.host if request.client else None


def journaliser(db: Session,
                message: str,
                niveau: str = NIVEAU_INFO,
                utilisateur: Optional[str] = None,
                request: Optional[Request] = None) -> None:
    """Enregistre un evenement. `utilisateur` est l'adresse electronique.

    Volontairement tolerant : une panne de journalisation ne doit jamais
    empecher l'action metier de se terminer (un signalement doit etre
    enregistre meme si la trace d'audit echoue).
    """
    try:
        db.add(models.Journal(
            niveau=niveau,
            message=message,
            utilisateur=utilisateur,
            ip_source=adresse_ip(request),
        ))
    except Exception:
        pass


def purger_anciens(db: Session, retention_jours: int = RETENTION_JOURS) -> int:
    """Supprime les entrees plus anciennes que la duree de retention.

    Retourne le nombre de lignes supprimees. Appelee a la consultation du
    journal : sans ordonnanceur dans l'architecture, c'est le point de passage
    qui garantit que la duree de conservation annoncee est bien respectee.
    """
    limite = datetime.utcnow() - timedelta(days=retention_jours)
    supprimees = db.query(models.Journal).filter(models.Journal.cree_le < limite).delete(
        synchronize_session=False)
    if supprimees:
        db.commit()
    return supprimees
