"""
geo_service.py
--------------
Lecture des coordonnees des chantiers depuis la base.

Ce module existe pour une raison precise. L'analyse satellitaire s'appuyait a
l'origine sur une liste de chantiers ecrite en dur dans le code Python, ce qui
figeait le perimetre du projet au moment de la compilation : un chantier ajoute
par le specialiste environnemental depuis le tableau de bord n'apparaissait
jamais dans les indices, et un chantier supprime continuait d'etre interroge.
Les identifiants etaient de surcroit supposes contigus de un a six, hypothese
qui tombe des la premiere suppression.

Le referentiel des chantiers est desormais unique : la table `chantiers`.
Tout le reste, indices satellitaires compris, en decoule.
"""
from sqlalchemy.orm import Session

from .. import models


def coordonnees_de(chantier: models.Chantier) -> tuple[float, float] | None:
    """Latitude et longitude d'un chantier, ou None s'il n'est pas positionne.

    La geometrie est lue via GeoAlchemy en production. Les tests tournant sous
    SQLite, ou le type PostGIS n'existe pas et ou la valeur est conservee sous
    forme de chaine, un repli analyse la representation textuelle du point.
    """
    if chantier.geom is None:
        return None
    try:
        from geoalchemy2.shape import to_shape
        point = to_shape(chantier.geom)
        return point.y, point.x
    except Exception:
        try:
            brut = str(chantier.geom)
            interieur = brut[brut.index("(") + 1:brut.index(")")]
            lon, lat = (float(v) for v in interieur.split())
            return lat, lon
        except Exception:
            return None


def chantiers_geolocalises(db: Session) -> list[dict]:
    """Chantiers positionnes sur la carte, dans le format attendu par le GEE.

    Les chantiers depourvus de coordonnees sont ecartes : les interroger
    n'aurait aucun sens, Earth Engine ayant besoin d'une emprise pour extraire
    quoi que ce soit.
    """
    resultat = []
    for chantier in db.query(models.Chantier).order_by(models.Chantier.id).all():
        coords = coordonnees_de(chantier)
        if coords is None:
            continue
        resultat.append({
            "id": chantier.id,
            "nom": chantier.nom,
            "commune": chantier.commune or "",
            "lat": coords[0],
            "lon": coords[1],
        })
    return resultat


def chantier_geolocalise(db: Session, chantier_id: int) -> dict | None:
    """Un chantier precis, positionne, ou None."""
    chantier = db.query(models.Chantier).filter(
        models.Chantier.id == chantier_id
    ).first()
    if chantier is None:
        return None
    coords = coordonnees_de(chantier)
    if coords is None:
        return None
    return {
        "id": chantier.id,
        "nom": chantier.nom,
        "commune": chantier.commune or "",
        "lat": coords[0],
        "lon": coords[1],
    }
