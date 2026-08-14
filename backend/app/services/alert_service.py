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
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models
from . import journal_service
from .email_service import envoyer_email

DEDUP_WINDOW_HOURS = 24


def _send_alert_email(destinataires: list[str], alerte: models.Alerte) -> None:
    """Envoie l'alerte a la liste de destinataires via le service email
    (Resend en prod, SMTP en dev). Un envoi par destinataire pour respecter
    la contrainte Resend « un seul To par requete »."""
    if not destinataires:
        print(f"[SI-ENV ALERTE] {alerte.niveau} - {alerte.message} "
              f"(aucun destinataire configure)")
        return

    dashboard_url = os.getenv("FRONTEND_URL", "https://si-env-ptua.pages.dev")
    couleur = "#B91C1C" if alerte.niveau in ("CRITIQUE", "ERROR") else "#D97706"
    libelle_niveau = alerte.niveau or "WARNING"

    sujet = f"[SI-ENV] Alerte {libelle_niveau} : {alerte.message[:60]}"

    texte = (
        f"SI-ENV AGEROUTE\n"
        f"Alerte {libelle_niveau}\n"
        f"-------------------\n\n"
        f"{alerte.message}\n\n"
        f"Valeur mesuree : {alerte.valeur}\n"
        f"Date : {alerte.cree_le.strftime('%d/%m/%Y %H:%M UTC') if alerte.cree_le else '-'}\n\n"
        f"Consultez le tableau de bord pour reagir :\n{dashboard_url}\n\n"
        f"--\nAGEROUTE - Projet de Transport Urbain d'Abidjan\n"
    )

    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:#0F172A;line-height:1.55">
  <span style="display:none;visibility:hidden;opacity:0;height:0;width:0;overflow:hidden">
    Alerte {libelle_niveau} SI-ENV : {alerte.message[:80]}
  </span>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:32px 16px">
    <tr><td align="center">
      <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFFFF;border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.06);border:1px solid #E2E8F0">
        <tr><td style="background:{couleur};padding:28px 32px;text-align:center">
          <div style="color:#FFFFFF;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1.4px;opacity:0.9">SI-ENV &middot; AGEROUTE</div>
          <div style="color:#FFFFFF;font-size:22px;font-weight:800;margin-top:8px">Alerte {libelle_niveau}</div>
        </td></tr>
        <tr><td style="padding:32px 36px 24px">
          <p style="margin:0 0 18px;font-size:15px;color:#0F172A;font-weight:600">{alerte.message}</p>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px">
            <tr>
              <td style="padding:12px 14px;background:#F8FAFC;border-radius:8px;font-size:12px;color:#64748B;width:50%">
                <div style="text-transform:uppercase;font-size:10px;letter-spacing:0.8px;margin-bottom:4px">Valeur mesuree</div>
                <div style="font-size:16px;font-weight:700;color:#0F172A">{alerte.valeur}</div>
              </td>
              <td style="width:10px"></td>
              <td style="padding:12px 14px;background:#F8FAFC;border-radius:8px;font-size:12px;color:#64748B;width:50%">
                <div style="text-transform:uppercase;font-size:10px;letter-spacing:0.8px;margin-bottom:4px">Date</div>
                <div style="font-size:13px;font-weight:600;color:#0F172A">{alerte.cree_le.strftime('%d/%m/%Y %H:%M') if alerte.cree_le else '-'}</div>
              </td>
            </tr>
          </table>
          <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto" align="center">
            <tr><td style="background:#004F9F;border-radius:10px">
              <a href="{dashboard_url}/alertes" style="display:inline-block;padding:12px 28px;color:#FFFFFF;font-size:14px;font-weight:600;text-decoration:none;border-radius:10px">Consulter les alertes</a>
            </td></tr>
          </table>
        </td></tr>
        <tr><td style="background:#F8FAFC;padding:18px 32px;border-top:1px solid #E2E8F0;text-align:center">
          <div style="font-size:11px;color:#94A3B8">AGEROUTE &middot; Projet de Transport Urbain d'Abidjan &middot; Cellule de Coordination</div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""

    for dest in destinataires:
        envoyer_email(dest, sujet, html, texte)


def _resoudre_chantier_id(db: Session, chantier_id: int, nom_indicatif: str) -> int | None:
    """Verifie que le chantier designe existe bien en base.

    Cette fonction compensait autrefois un decalage : les indices satellite
    reposaient sur une liste ecrite en dur, dont les identifiants ne
    correspondaient pas necessairement aux lignes reelles de la table. Le
    referentiel etant desormais unique, la correspondance est directe. Le repli
    par nom subsiste pour les alertes issues d'anciens caches, ou le rapport a
    un chantier disparu n'est plus garanti.
    """
    chantier = db.query(models.Chantier).filter(models.Chantier.id == chantier_id).first()
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
    # Portee des seuils. Un seuil sans chantier vaut pour l'ensemble du
    # programme ; un seuil rattache a un chantier ne concerne que celui-ci.
    # Les deux se cumulent, un ouvrage sensible pouvant etre soumis a la fois
    # a la regle generale et a une regle qui lui est propre.
    chantier_reel = _resoudre_chantier_id(db, chantier_id_statique, chantier_nom)
    seuils = db.query(models.AlerteSeuil).filter(
        models.AlerteSeuil.indicateur == indicateur,
        models.AlerteSeuil.actif == True,  # noqa: E712
        or_(
            models.AlerteSeuil.chantier_id.is_(None),
            models.AlerteSeuil.chantier_id == chantier_reel,
        ),
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

    chantier_id = chantier_reel

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
