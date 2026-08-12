"""
alert_service.py
-----------------
Relie les mesures satellite (GEE) aux seuils configures par l'administrateur
(AlerteSeuil) : quand une valeur mesuree depasse un seuil actif, une Alerte
est creee en base et un email est envoye aux responsables environnement.

Sans ce module, la configuration de seuils (CRUD /admin/seuils) et
l'affichage des alertes existaient mais rien ne les reliait : aucune Alerte
n'etait jamais creee automatiquement a partir d'une mesure reelle.
"""
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from .. import models
from . import journal_service

DEDUP_WINDOW_HOURS = 24


def _send_alert_email(destinataires: list[str], alerte: models.Alerte) -> None:
    """Envoie l'alerte par email (Gmail SMTP), ou logue si non configure."""
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    email_from = os.getenv("EMAIL_FROM", smtp_user)

    if not smtp_user or not smtp_pass or not destinataires:
        print(f"[SI-ENV ALERTE] {alerte.niveau} - {alerte.message} "
              f"(email non envoye : SMTP non configure ou aucun destinataire)")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[SI-ENV AGEROUTE] Alerte {alerte.niveau} : {alerte.message}"
    msg["From"] = email_from
    msg["To"] = ", ".join(destinataires)

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f4f5;padding:30px">
      <div style="max-width:480px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;border:1px solid #e4e4e7">
        <div style="background:#B91C1C;padding:24px;text-align:center">
          <h1 style="color:white;font-size:20px;margin:0">SI-ENV · AGEROUTE</h1>
          <p style="color:rgba(255,255,255,0.85);font-size:12px;margin:6px 0 0">Alerte {alerte.niveau}</p>
        </div>
        <div style="padding:32px">
          <p style="color:#18181B;font-size:15px;margin:0 0 12px">{alerte.message}</p>
          <p style="color:#71717A;font-size:13px;margin:0">Valeur mesuree : {alerte.valeur}</p>
        </div>
      </div>
    </body></html>
    """
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(email_from, destinataires, msg.as_string())
        print(f"[SI-ENV SMTP] Alerte envoyee a {destinataires}")
    except Exception as e:
        print(f"[SI-ENV SMTP ERREUR] {e}")


def _resoudre_chantier_id(db: Session, chantier_id_statique: int, nom_indicatif: str) -> int | None:
    """
    Les indices satellite s'appuient sur une liste fixe de chantiers
    (gee_service.CHANTIERS) dont les identifiants ne correspondent pas
    toujours aux lignes reelles de la table `chantiers`. On tente une
    correspondance par id, puis par nom, sinon on rattache l'alerte a
    aucun chantier plutot que d'echouer sur une contrainte de cle etrangere.
    """
    chantier = db.query(models.Chantier).filter(models.Chantier.id == chantier_id_statique).first()
    if chantier:
        return chantier.id
    premier_mot = nom_indicatif.split()[0] if nom_indicatif else None
    if premier_mot:
        chantier = db.query(models.Chantier).filter(models.Chantier.nom.ilike(f"%{premier_mot}%")).first()
        if chantier:
            return chantier.id
    return None


def evaluer_et_creer_alerte(
    db: Session,
    chantier_id_statique: int,
    chantier_nom: str,
    indicateur: str,
    valeur: float,
    statut: str,
) -> models.Alerte | None:
    """
    Compare `valeur` aux AlerteSeuil actifs pour cet indicateur. A defaut de
    seuil configure par l'admin, se rabat sur le statut deja calcule par les
    regles metier existantes (MAUVAIS => alerte). Deduplique sur une fenetre
    de DEDUP_WINDOW_HOURS pour ne pas spammer a chaque appel de l'API.
    """
    seuils = db.query(models.AlerteSeuil).filter(
        models.AlerteSeuil.indicateur == indicateur,
        models.AlerteSeuil.actif == True,  # noqa: E712
    ).all()

    declenche = False
    niveau = "WARNING"
    seuil_valeur = None
    if seuils:
        for s in seuils:
            if valeur > s.seuil:
                declenche = True
                niveau = s.niveau
                seuil_valeur = s.seuil
                break
    elif statut == "MAUVAIS":
        declenche = True
        niveau = "CRITIQUE"

    if not declenche:
        return None

    chantier_id = _resoudre_chantier_id(db, chantier_id_statique, chantier_nom)

    fenetre = datetime.utcnow() - timedelta(hours=DEDUP_WINDOW_HOURS)
    filtre_chantier = (
        models.Alerte.chantier_id == chantier_id
        if chantier_id is not None
        else models.Alerte.chantier_id.is_(None)
    )
    existe = db.query(models.Alerte).filter(
        filtre_chantier,
        models.Alerte.message.like(f"%{indicateur}%"),
        models.Alerte.cree_le >= fenetre,
    ).first()
    if existe:
        return None

    seuil_txt = f" (seuil configure : {seuil_valeur})" if seuil_valeur is not None else ""
    message = f"{chantier_nom} — indicateur {indicateur} en niveau {statut}{seuil_txt} : valeur mesuree {valeur:.2f}"
    alerte = models.Alerte(message=message, niveau=niveau, valeur=valeur, chantier_id=chantier_id)
    db.add(alerte)
    # Trace d'audit : l'alerte etant declenchee par le systeme et non par un
    # operateur, l'auteur est le service lui-meme et il n'y a pas d'adresse IP.
    journal_service.journaliser(
        db,
        f"Alerte {niveau} déclenchée automatiquement : {indicateur} = {valeur:.2f} "
        f"sur {chantier_nom}",
        niveau=journal_service.NIVEAU_WARNING,
        utilisateur="système (évaluation des seuils)")
    db.commit()
    db.refresh(alerte)

    destinataires = [
        u.email for u in db.query(models.Utilisateur).filter(
            models.Utilisateur.role.in_([models.RoleEnum.RESP_ENV, models.RoleEnum.EXPERT_HSE])
        ).all()
    ]
    _send_alert_email(destinataires, alerte)
    return alerte
