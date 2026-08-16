from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from .. import models, auth
from ..services.report_generator import generate_pges_pdf
from ..services.email_service import envoyer_email

router = APIRouter(
    prefix="/rapports",
    tags=["Rapports"]
)

class RapportRequest(BaseModel):
    chantier_ids: List[int]
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None
    entreprise_destinataire: Optional[str] = "ANDE"

def _collecter_donnees(db: Session, req: "RapportRequest") -> list[dict]:
    """Agrege les chiffres du rapport pour les chantiers et la periode vises.

    Extrait du corps de l'endpoint pour servir aux deux usages du rapport :
    le telechargement immediat par celui qui le consulte, et la transmission
    formelle aux organismes de controle.
    """
    # Fetch chantiers
    chantiers = db.query(models.Chantier).filter(models.Chantier.id.in_(req.chantier_ids)).all()
    
    chantiers_data = []
    
    for c in chantiers:
        # Build base query filters for dates
        date_filter = []
        if req.date_debut:
            try:
                dt_start = datetime.strptime(req.date_debut, "%Y-%m-%d")
                date_filter.append(models.Signalement.cree_le >= dt_start)
            except ValueError:
                pass
        if req.date_fin:
            try:
                dt_end = datetime.strptime(req.date_fin, "%Y-%m-%d")
                date_filter.append(models.Signalement.cree_le <= dt_end)
            except ValueError:
                pass
                
        # Count Signalements
        sig_q = db.query(models.Signalement).filter(models.Signalement.chantier_id == c.id)
        for f in date_filter: sig_q = sig_q.filter(f)
        nb_signalements = sig_q.count()
        
        # Count Alertes
        alert_q = db.query(models.Alerte).filter(models.Alerte.chantier_id == c.id)
        if req.date_debut: alert_q = alert_q.filter(models.Alerte.cree_le >= req.date_debut)
        if req.date_fin: alert_q = alert_q.filter(models.Alerte.cree_le <= req.date_fin)
        nb_alertes = alert_q.count()
        
        # Count Plaintes
        plainte_q = db.query(models.Plainte).filter(models.Plainte.chantier_id == c.id)
        if req.date_debut: plainte_q = plainte_q.filter(models.Plainte.cree_le >= req.date_debut)
        if req.date_fin: plainte_q = plainte_q.filter(models.Plainte.cree_le <= req.date_fin)
        nb_plaintes = plainte_q.count()
        
        # Count Non-Conformites (through signalements)
        nc_q = db.query(models.NonConformite).join(models.Signalement).filter(models.Signalement.chantier_id == c.id)
        if req.date_debut: nc_q = nc_q.filter(models.NonConformite.cree_le >= req.date_debut)
        if req.date_fin: nc_q = nc_q.filter(models.NonConformite.cree_le <= req.date_fin)
        nb_nc = nc_q.count()
        
        # Repartition par statut et par gravite. Ces chiffres ne servent pas
        # aux tableaux, qui se contentent des totaux, mais a la redaction du
        # rapport : sans eux, le commentaire ne pourrait qu'enoncer des
        # volumes, sans jamais dire si la situation s'assainit ou se degrade.
        nb_traites = sig_q.filter(
            models.Signalement.statut == models.StatutSignalement.CLOTURE
        ).count()
        nb_en_cours = sig_q.filter(
            models.Signalement.statut == models.StatutSignalement.EN_TRAITEMENT
        ).count()
        nb_nouveaux = sig_q.filter(
            models.Signalement.statut == models.StatutSignalement.NOUVEAU
        ).count()
        nb_eleves = sig_q.filter(
            models.Signalement.criticite == models.CriticiteEnum.ELEVE
        ).count()
        nb_plaintes_ouvertes = plainte_q.filter(
            models.Plainte.statut.in_(("OUVERTE", "EN_COURS"))
        ).count()
        nb_plaintes_mobile = plainte_q.filter(
            models.Plainte.canal == "MOBILE"
        ).count()
        nb_nc_ouvertes = nc_q.filter(
            models.NonConformite.resolue == False  # noqa: E712
        ).count()

        # Nuisances les plus frequentes, pour nommer ce dont il s'agit plutot
        # que de compter des signalements indistincts.
        types_frequents = [
            {"type": t, "n": n}
            for t, n in (
                sig_q.with_entities(
                    models.Signalement.type_nuisance,
                    func.count(models.Signalement.id),
                )
                .group_by(models.Signalement.type_nuisance)
                .order_by(func.count(models.Signalement.id).desc())
                .limit(3)
                .all()
            )
        ]

        chantiers_data.append({
            "id": c.id,
            "nom": c.nom,
            "commune": c.commune,
            "nb_signalements": nb_signalements,
            "nb_alertes": nb_alertes,
            "nb_plaintes": nb_plaintes,
            "nb_non_conformites": nb_nc,
            "nb_traites": nb_traites,
            "nb_en_cours": nb_en_cours,
            "nb_nouveaux": nb_nouveaux,
            "nb_eleves": nb_eleves,
            "nb_plaintes_ouvertes": nb_plaintes_ouvertes,
            "nb_plaintes_mobile": nb_plaintes_mobile,
            "nb_nc_ouvertes": nb_nc_ouvertes,
            "types_frequents": types_frequents,
            "plaintes_details": [
                {"nom": p.nom_plaignant, "desc": p.description, "statut": p.statut, "date": p.cree_le.strftime("%d/%m/%Y") if p.cree_le else ""}
                for p in plainte_q.limit(5).all()
            ],
            "signalements_details": [
                {"type": s.type_nuisance, "desc": s.description, "statut": s.statut, "date": s.cree_le.strftime("%d/%m/%Y") if s.cree_le else ""}
                for s in sig_q.limit(5).all()
            ]
        })

    return chantiers_data


@router.post("/generate")
def generate_rapport(
    req: RapportRequest,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(auth.roles_requis(models.RoleEnum.SPEC_ENV, models.RoleEnum.ADMIN,
                                                     models.RoleEnum.ANDE, models.RoleEnum.BAD))
):
    """Genere le rapport de suivi environnemental en PDF pour la periode retenue."""
    chantiers_data = _collecter_donnees(db, req)
    pdf_buffer = generate_pges_pdf(chantiers_data, req.date_debut, req.date_fin,
                                   req.entreprise_destinataire)

    filename = f"Rapport_suivi_environnemental_{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ══════════════════════════════════════════════════════════════════════════
#  Transmission formelle aux organismes de controle
# ══════════════════════════════════════════════════════════════════════════
#
# L'ANDE et la BAD disposent d'un acces en consultation et suivent le
# programme au fil de l'eau. Cela ne dispense pas de la remise periodique du
# rapport de conformite, qui reste un acte distinct : un auditeur ne demande
# pas le document, qu'il peut consulter quand il veut, il demande a quelle
# date il lui a ete officiellement adresse et par qui. C'est cette trace que
# les endpoints ci-dessous produisent, l'envoi n'en etant que le moyen.

#: Adresses institutionnelles par defaut, modifiables au moment de l'envoi.
DESTINATAIRES_PAR_DEFAUT = {
    "ANDE": "controle@ande.ci",
    "BAD": "mission@afdb.org",
}


class TransmissionRequest(RapportRequest):
    """Requete de transmission : un rapport et son destinataire."""
    # Laisse vide, l'adresse institutionnelle de l'organisme est retenue.
    destinataire_email: Optional[str] = None


class TransmissionOut(BaseModel):
    id: int
    transmis_le: datetime
    emetteur_email: str
    destinataire_email: str
    organisme: Optional[str] = None
    periode_debut: Optional[str] = None
    periode_fin: Optional[str] = None
    nom_fichier: Optional[str] = None
    taille_octets: Optional[int] = None
    succes: bool

    class Config:
        from_attributes = True


@router.post("/transmettre", response_model=TransmissionOut)
def transmettre_rapport(
    req: TransmissionRequest,
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(auth.roles_requis(
        models.RoleEnum.SPEC_ENV, models.RoleEnum.ADMIN)),
):
    """Genere le rapport et l'adresse a l'organisme, en conservant la trace.

    Reserve au specialiste du suivi environnemental : transmettre un rapport
    engage l'AGEROUTE vis-a-vis de son regulateur et de son bailleur, ce n'est
    pas un geste que les destinataires eux-memes peuvent poser.
    """
    organisme = (req.entreprise_destinataire or "ANDE").upper()
    destinataire = (req.destinataire_email
                    or DESTINATAIRES_PAR_DEFAUT.get(organisme, "")).strip().lower()
    if not destinataire:
        raise HTTPException(
            status_code=400,
            detail=f"Aucune adresse connue pour {organisme}. Précisez un destinataire.",
        )

    chantiers_data = _collecter_donnees(db, req)
    if not chantiers_data:
        raise HTTPException(
            status_code=400,
            detail="Sélectionnez au moins un chantier avant de transmettre le rapport.",
        )

    pdf = generate_pges_pdf(chantiers_data, req.date_debut, req.date_fin, organisme)
    contenu = pdf.getvalue() if hasattr(pdf, "getvalue") else pdf.read()
    nom_fichier = f"Rapport_suivi_environnemental_{datetime.now().strftime('%Y%m%d')}.pdf"

    # La trace est constituee avant l'envoi : un acheminement qui echoue doit
    # laisser une empreinte, sans quoi la tentative passerait pour n'avoir
    # jamais eu lieu.
    trace = models.TransmissionRapport(
        emetteur_email=courant.email,
        destinataire_email=destinataire,
        organisme=organisme,
        periode_debut=req.date_debut,
        periode_fin=req.date_fin,
        chantiers=",".join(str(c["id"]) for c in chantiers_data),
        nom_fichier=nom_fichier,
        taille_octets=len(contenu),
        succes=False,
    )

    try:
        envoye = envoyer_email(
            destinataire,
            f"[SI-ENV] Rapport de suivi environnemental du {datetime.now().strftime('%d/%m/%Y')}",
            _corps_html_transmission(chantiers_data, req, organisme, courant, nom_fichier),
            _corps_texte_transmission(chantiers_data, req, organisme, courant),
            piece_jointe=(nom_fichier, contenu),
        )
        trace.succes = bool(envoye)
        if not envoye:
            trace.detail_erreur = "Le service de messagerie n'a pas confirmé l'envoi."
    except Exception as e:  # pragma: no cover
        trace.detail_erreur = str(e)[:400]

    db.add(trace)
    db.commit()
    db.refresh(trace)

    if not trace.succes:
        raise HTTPException(
            status_code=502,
            detail="Le rapport a été produit mais son acheminement a échoué. "
                   "La tentative est enregistrée dans l'historique des transmissions.",
        )
    return trace


@router.get("/transmissions", response_model=List[TransmissionOut])
def historique_transmissions(
    db: Session = Depends(get_db),
    _: models.Utilisateur = Depends(auth.roles_requis(
        models.RoleEnum.SPEC_ENV, models.RoleEnum.ADMIN,
        models.RoleEnum.ANDE, models.RoleEnum.BAD)),
):
    """Historique des remises, consultable par l'emetteur comme par les destinataires.

    Les organismes de controle y accedent egalement : verifier ce qui leur a
    ete adresse, et a quelle date, fait partie de leur mission.
    """
    return (
        db.query(models.TransmissionRapport)
        .order_by(models.TransmissionRapport.transmis_le.desc())
        .limit(100)
        .all()
    )


def _periode_lisible(req: RapportRequest) -> str:
    if req.date_debut and req.date_fin:
        return f"du {req.date_debut} au {req.date_fin}"
    return "sur l'ensemble de la période disponible"


def _corps_texte_transmission(chantiers_data, req, organisme, emetteur) -> str:
    lignes = [
        "SI-ENV AGEROUTE",
        "Transmission d'un rapport de suivi environnemental",
        "",
        f"A l'attention de : {organisme}",
        f"Emis par : {emetteur.nom or emetteur.email} ({emetteur.email})",
        f"Periode couverte : {_periode_lisible(req)}",
        f"Chantiers couverts : {len(chantiers_data)}",
        "",
        "Chantiers concernes :",
    ]
    for c in chantiers_data:
        commune = c["commune"] or "commune non renseignee"
        lignes.append(
            f"  - {c['nom']} ({commune}) : "
            f"{c['nb_signalements']} signalement(s), {c['nb_alertes']} alerte(s), "
            f"{c['nb_plaintes']} plainte(s)"
        )
    lignes += [
        "",
        "Le rapport complet est joint au format PDF.",
        "",
        "--",
        "AGEROUTE - Projet de Transport Urbain d'Abidjan",
    ]
    return "\n".join(lignes)


def _corps_html_transmission(chantiers_data, req, organisme, emetteur, nom_fichier) -> str:
    cellule = "padding:9px 12px;font-size:12.5px;border-bottom:1px solid #EEF2F6"
    entete = ("padding:9px 12px;font-size:10.5px;color:#64748B;font-weight:700;"
              "text-transform:uppercase;letter-spacing:0.4px")

    lignes_tableau = "".join(
        f"<tr>"
        f"<td style=\"{cellule};color:#0F172A\">{c['nom']}</td>"
        f"<td style=\"{cellule};color:#64748B\">{c['commune'] or '-'}</td>"
        f"<td style=\"{cellule};color:#0F172A;text-align:center\">{c['nb_signalements']}</td>"
        f"<td style=\"{cellule};color:#0F172A;text-align:center\">{c['nb_alertes']}</td>"
        f"<td style=\"{cellule};color:#0F172A;text-align:center\">{c['nb_plaintes']}</td>"
        f"</tr>"
        for c in chantiers_data
    )

    emetteur_affiche = emetteur.nom or emetteur.email
    periode = _periode_lisible(req)

    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:#0F172A;line-height:1.55">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:32px 16px">
    <tr><td align="center">
      <table role="presentation" width="620" cellpadding="0" cellspacing="0" style="max-width:620px;background:#FFFFFF;border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.06);border:1px solid #E2E8F0">
        <tr><td style="background:linear-gradient(135deg,#004F9F 0%,#003063 100%);padding:30px 34px">
          <div style="color:rgba(255,255,255,0.7);font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:1.3px">Transmission officielle</div>
          <div style="color:#FFFFFF;font-size:20px;font-weight:700;margin-top:7px">Rapport de suivi environnemental</div>
          <div style="color:rgba(255,255,255,0.72);font-size:12px;margin-top:5px">Projet de Transport Urbain d'Abidjan</div>
        </td></tr>

        <tr><td style="padding:30px 34px 22px">
          <p style="margin:0 0 20px;font-size:14px;color:#475569">
            À l'attention de <strong>{organisme}</strong>. Le rapport de suivi
            environnemental et social {periode} vous est adressé en pièce jointe.
          </p>

          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:22px;background:#F8FAFC;border-radius:10px;border:1px solid #E2E8F0">
            <tr>
              <td style="padding:11px 14px;font-size:11.5px;color:#64748B;width:38%">Émis par</td>
              <td style="padding:11px 14px;font-size:12.5px;font-weight:600;color:#0F172A">{emetteur_affiche}</td>
            </tr>
            <tr>
              <td style="padding:11px 14px;font-size:11.5px;color:#64748B;border-top:1px solid #E2E8F0">Période couverte</td>
              <td style="padding:11px 14px;font-size:12.5px;font-weight:600;color:#0F172A;border-top:1px solid #E2E8F0">{periode}</td>
            </tr>
            <tr>
              <td style="padding:11px 14px;font-size:11.5px;color:#64748B;border-top:1px solid #E2E8F0">Document</td>
              <td style="padding:11px 14px;font-size:12.5px;font-weight:600;color:#0F172A;border-top:1px solid #E2E8F0">{nom_fichier}</td>
            </tr>
          </table>

          <div style="font-size:11px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.7px;margin-bottom:9px">Synthèse par chantier</div>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E2E8F0;border-radius:10px;overflow:hidden;border-collapse:separate">
            <tr style="background:#F8FAFC">
              <th style="{entete};text-align:left">Chantier</th>
              <th style="{entete};text-align:left">Commune</th>
              <th style="{entete};text-align:center">Signal.</th>
              <th style="{entete};text-align:center">Alertes</th>
              <th style="{entete};text-align:center">Plaintes</th>
            </tr>
            {lignes_tableau}
          </table>

          <p style="margin:20px 0 0;font-size:12px;color:#94A3B8;line-height:1.6">
            Cette transmission est enregistrée dans l'historique du système avec
            sa date et son émetteur.
          </p>
        </td></tr>

        <tr><td style="background:#F8FAFC;padding:18px 34px;border-top:1px solid #E2E8F0;text-align:center">
          <div style="font-size:12px;color:#64748B;font-weight:600">AGEROUTE &middot; Agence de Gestion des Routes</div>
          <div style="font-size:11px;color:#94A3B8;margin-top:4px">Cellule de Coordination du Projet de Transport Urbain d'Abidjan</div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""
