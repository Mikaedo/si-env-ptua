"""
stats_router.py
---------------
- GET /stats : statistiques globales (totaux, repartition, evolution)
"""
from datetime import datetime, timedelta
from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/stats", tags=["Statistiques"])


@router.get("", response_model=schemas.Statistiques)
def statistiques(db: Session = Depends(get_db),
                 courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    total = db.query(func.count(models.Signalement.id)).scalar() or 0
    traites = db.query(func.count(models.Signalement.id)).filter(
        models.Signalement.statut == models.StatutSignalement.CLOTURE).scalar() or 0
    en_attente = db.query(func.count(models.Signalement.id)).filter(
        models.Signalement.statut == models.StatutSignalement.NOUVEAU).scalar() or 0
    urgents = db.query(func.count(models.Signalement.id)).filter(
        models.Signalement.criticite == models.CriticiteEnum.ELEVE).scalar() or 0

    taux = (traites / total * 100) if total > 0 else 0.0

    # Repartition par type de nuisance
    rows = db.query(models.Signalement.type_nuisance,
                    func.count(models.Signalement.id)).group_by(
        models.Signalement.type_nuisance).all()
    repartition = {r[0]: r[1] for r in rows}

    # Evolution mensuelle (3 derniers mois)
    evolution = {}
    for i in range(2, -1, -1):
        date_ref = datetime.utcnow() - timedelta(days=i * 30)
        mois = date_ref.month
        annee = date_ref.year
        count = db.query(func.count(models.Signalement.id)).filter(
            extract("month", models.Signalement.cree_le) == mois,
            extract("year", models.Signalement.cree_le) == annee,
        ).scalar() or 0
        label = f"{annee}-{mois:02d}"
        evolution[label] = count

    return {
        "total": total,
        "traites": traites,
        "en_attente": en_attente,
        "urgents": urgents,
        "taux_traitement": round(taux, 1),
        "repartition": repartition,
        "evolution": evolution,
    }
