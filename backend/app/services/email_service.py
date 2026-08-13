# -*- coding: utf-8 -*-
"""
email_service.py
----------------
Envoi d'email avec deux backends interchangeables :

  1. RESEND_API_KEY defini  → envoi via API HTTPS Resend (prod)
  2. sinon SMTP_USER/PASS   → envoi via SMTP direct (dev local)
  3. sinon                  → journalisation locale, aucun envoi

Le tier gratuit de Render bloque les connexions SMTP sortantes (ports 25, 465,
587 fermes). Resend, dont l'API est en HTTPS, contourne cette limitation. Le
compte gratuit Resend offre 100 mails/jour et 3 000/mois sans carte bancaire,
ce qui est amplement suffisant pour la validation academique du SI-ENV.
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("email_service")


def envoyer_email(destinataire: str, sujet: str, html: str, texte: str) -> bool:
    """Envoie un email. Retourne True en cas de succes, False sinon.

    Le journal reflete precisement quel backend a ete utilise et pourquoi,
    pour faciliter le diagnostic en production (cf. logs Render).
    """
    # Resend et beaucoup de MTA exigent une adresse strictement en minuscules
    # (la partie locale d'un email est theoriquement sensible a la casse mais
    # aucun fournisseur grand public ne la respecte). On normalise ici pour
    # eviter les 403 "validation_error" quand un utilisateur s'est inscrit
    # avec des majuscules.
    destinataire = destinataire.strip().lower()

    cle_resend = (os.getenv("RESEND_API_KEY") or "").strip()
    if cle_resend:
        return _envoyer_via_resend(cle_resend, destinataire, sujet, html, texte)

    smtp_user = (os.getenv("SMTP_USER") or "").strip()
    smtp_pass = (os.getenv("SMTP_PASSWORD") or "").strip()
    if smtp_user and smtp_pass and "@gmail.com" in smtp_user:
        return _envoyer_via_smtp(destinataire, sujet, html, texte, smtp_user, smtp_pass)

    logger.warning(
        "[email] aucun backend configure (ni RESEND_API_KEY, ni SMTP_USER). "
        "Message pour %s non envoye.", destinataire
    )
    return False


def _envoyer_via_resend(cle: str, dest: str, sujet: str, html: str, texte: str) -> bool:
    """POST https://api.resend.com/emails, HTTPS uniquement.

    L'adresse d'expedition par defaut est celle du bac a sable Resend
    (onboarding@resend.dev), qui ne necessite aucune verification de domaine
    et permet d'envoyer immediatement vers l'email du proprietaire du compte
    Resend. Pour envoyer vers n'importe quel destinataire, verifier un domaine
    dans la console Resend et passer EMAIL_FROM en variable d'environnement.
    """
    import requests

    expediteur = (os.getenv("EMAIL_FROM") or
                  "SI-ENV AGEROUTE <onboarding@resend.dev>").strip()
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {cle}",
                "Content-Type": "application/json",
            },
            json={
                "from": expediteur,
                "to": [dest],
                "subject": sujet,
                "html": html,
                "text": texte,
            },
            timeout=15,
        )
        if r.status_code in (200, 202):
            id_msg = ""
            try:
                id_msg = r.json().get("id", "")
            except Exception:
                pass
            logger.info("[email/Resend] envoye a %s (id=%s)", dest, id_msg)
            return True
        logger.error("[email/Resend] echec HTTP %s : %s",
                     r.status_code, r.text[:200])
        return False
    except Exception as e:  # pragma: no cover
        logger.error("[email/Resend] exception : %s", e)
        return False


def _envoyer_via_smtp(dest: str, sujet: str, html: str, texte: str,
                      user: str, pwd: str) -> bool:
    """SMTP direct. Fonctionne en dev local, pas sur Render Free (SMTP bloque)."""
    hote = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    expediteur = os.getenv("EMAIL_FROM", user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"] = expediteur
    msg["To"] = dest
    msg.attach(MIMEText(texte, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(hote, port, timeout=15) as serveur:
            serveur.ehlo()
            serveur.starttls()
            serveur.login(user, pwd)
            serveur.sendmail(expediteur, dest, msg.as_string())
        logger.info("[email/SMTP] envoye a %s", dest)
        return True
    except Exception as e:
        logger.error("[email/SMTP] echec : %s", e)
        return False
