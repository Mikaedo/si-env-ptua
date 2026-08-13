# -*- coding: utf-8 -*-
"""
erreur_service.py
-----------------
Capture les exceptions non gerees des endpoints FastAPI et les stocke en base
pour consultation par l'administrateur.

Equivalent minimal et auto-heberge de Sentry, sans compte externe ni cle API.
Chaque erreur retient le contexte utile au diagnostic : chemin, methode,
utilisateur, IP, type, message, trace.
"""
from __future__ import annotations

import logging
import traceback
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from ..database import SessionLocal
from .. import models

logger = logging.getLogger("erreurs")


def enregistrer(erreur: Exception, request: Request | None = None,
                utilisateur: str | None = None) -> None:
    """Persiste une erreur en base. Silencieux en cas d'echec (le vrai
    probleme est deja remonte a l'utilisateur, on ne veut pas masquer)."""
    db = SessionLocal()
    try:
        ip = None
        methode = None
        chemin = None
        if request is not None:
            xff = request.headers.get("x-forwarded-for")
            ip = (xff.split(",")[0].strip() if xff else None) or \
                 (request.client.host if request.client else None)
            methode = request.method
            chemin = request.url.path
        db.add(models.ErreurApp(
            methode=methode, chemin=chemin,
            utilisateur=utilisateur, ip_source=ip,
            type_erreur=type(erreur).__name__,
            message=str(erreur)[:1000],
            trace=traceback.format_exc()[:5000],
        ))
        db.commit()
    except SQLAlchemyError as e:
        logger.warning("Impossible de persister l'erreur : %s", e)
        db.rollback()
    finally:
        db.close()


def gestionnaire_exceptions(app):
    """Installe un handler qui persiste chaque exception non geree."""
    @app.exception_handler(Exception)
    async def _handler(request: Request, exc: Exception):
        # On tente d'extraire l'email a partir de l'en-tete Authorization,
        # sans importer les modules d'auth pour eviter les dependances
        # circulaires.
        utilisateur = None
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            try:
                import jose.jwt as jwt
                import os
                cle = os.getenv("SECRET_KEY", "")
                if cle:
                    payload = jwt.decode(auth[7:], cle, algorithms=["HS256"])
                    utilisateur = payload.get("sub") or payload.get("email")
            except Exception:
                pass
        enregistrer(exc, request, utilisateur)
        logger.error("Exception sur %s %s : %s", request.method,
                     request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Erreur interne. L'incident a ete journalise."},
        )
