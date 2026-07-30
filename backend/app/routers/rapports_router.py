from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from .. import models, auth
from ..services.report_generator import generate_pges_pdf

router = APIRouter(
    prefix="/rapports",
    tags=["Rapports"]
)

class RapportRequest(BaseModel):
    chantier_ids: List[int]
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None
    entreprise_destinataire: Optional[str] = "ANDE"

@router.post("/generate")
def generate_rapport(
    req: RapportRequest,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(auth.roles_requis(models.RoleEnum.SPEC_ENV, models.RoleEnum.ADMIN))
):
    """
    Génère le rapport PGES en PDF pour les chantiers et la période sélectionnés.
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
        
        chantiers_data.append({
            "id": c.id,
            "nom": c.nom,
            "commune": c.commune,
            "nb_signalements": nb_signalements,
            "nb_alertes": nb_alertes,
            "nb_plaintes": nb_plaintes,
            "nb_non_conformites": nb_nc,
            "plaintes_details": [
                {"nom": p.nom_plaignant, "desc": p.description, "statut": p.statut, "date": p.cree_le.strftime("%d/%m/%Y") if p.cree_le else ""}
                for p in plainte_q.limit(5).all()
            ],
            "signalements_details": [
                {"type": s.type_nuisance, "desc": s.description, "statut": s.statut, "date": s.cree_le.strftime("%d/%m/%Y") if s.cree_le else ""}
                for s in sig_q.limit(5).all()
            ]
        })
        
    # Build PDF
    pdf_buffer = generate_pges_pdf(chantiers_data, req.date_debut, req.date_fin, req.entreprise_destinataire)
    
    filename = f"Rapport_PGES_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
