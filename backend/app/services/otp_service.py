# -*- coding: utf-8 -*-
"""
otp_service.py
--------------
Emission et verification de codes a usage unique persistes en base.

Remplace le dict Python en memoire du prototype, qui perdait les codes a
chaque redemarrage du service. La table `otp_codes` survit aux redemarrages
Render, aux redeploiements, et se purge automatiquement.
"""
from __future__ import annotations

import random
import string
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import models

DUREE_DEFAUT_MIN = 10


def _generer_code(longueur: int = 6) -> str:
    return "".join(random.choice(string.digits) for _ in range(longueur))


def emettre(db: Session, email: str, motif: str = "reset",
            duree_min: int = DUREE_DEFAUT_MIN) -> str:
    """Genere un code, l'enregistre en base, purge les codes obsoletes."""
    email = email.strip().lower()
    # Purge preventive : evite que la table grossisse indefiniment.
    _purger(db)
    # Invalide les codes precedents encore actifs pour ce meme motif :
    # un utilisateur qui redemande un code veut invalider l'ancien.
    db.query(models.OtpCode).filter(
        models.OtpCode.email == email,
        models.OtpCode.motif == motif,
        models.OtpCode.consomme_le.is_(None),
    ).update({"consomme_le": datetime.utcnow()})

    code = _generer_code()
    otp = models.OtpCode(
        email=email, code=code, motif=motif,
        expire_le=datetime.utcnow() + timedelta(minutes=duree_min),
    )
    db.add(otp)
    db.commit()
    return code


def verifier(db: Session, email: str, code: str, motif: str = "reset") -> bool:
    """Retourne True si le code est valide, non expire, non consomme."""
    email = email.strip().lower()
    otp = db.query(models.OtpCode).filter(
        models.OtpCode.email == email,
        models.OtpCode.motif == motif,
        models.OtpCode.code == code.strip(),
        models.OtpCode.consomme_le.is_(None),
        models.OtpCode.expire_le >= datetime.utcnow(),
    ).order_by(models.OtpCode.cree_le.desc()).first()
    if not otp:
        return False
    otp.consomme_le = datetime.utcnow()
    db.commit()
    return True


def _purger(db: Session) -> None:
    """Supprime les codes expires depuis plus d'une heure."""
    limite = datetime.utcnow() - timedelta(hours=1)
    db.query(models.OtpCode).filter(models.OtpCode.expire_le < limite).delete()
    db.commit()
