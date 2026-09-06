# -*- coding: utf-8 -*-
"""
mesures_router.py
-----------------
Les mesures instrumentees realisees par un laboratoire agree (BF-08).

Le dispositif reposait sur deux sources, l'observation de l'agent et le
satellite, dont aucune ne vaut mesure. Le memoire l'ecrit du volet
satellitaire, qui « oriente les priorites de terrain, il ne remplace pas
la mesure instrumentee exigee par la BAD et l'ANDE », et le range parmi
les limites : ni sonometre pour le bruit, ni capteur pour les
poussieres.

Ces mesures existent pourtant. Un laboratoire accredite intervient sur
les chantiers, et ses resultats sont ce que le bailleur reconnait. Ils
restaient sur papier, hors du dispositif, si bien que le rapport de
suivi ne pouvait pas les porter.

La saisie revient au Specialiste Suivi Environnemental, conformement au
BF-08 : c'est lui qui recoit le rapport du laboratoire et qui rend
compte au bailleur. La lecture est ouverte plus largement, l'ANDE et la
BAD ayant precisement ces mesures a controler.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services import mesures_reference

router = APIRouter(prefix="/mesures", tags=["Mesures prestataire"])

#: Profils habilites a verser une mesure au dossier (BF-08).
ROLES_SAISIE = (models.RoleEnum.SPEC_ENV, models.RoleEnum.ADMIN)


def _serialiser(mesure: models.MesurePrestataire) -> dict:
    """Ajoute a la mesure ce qui permet de la lire : son etat et sa limite.

    L'etat est calcule a la lecture plutot que stocke : une valeur limite
    peut evoluer avec la reglementation, et une mesure figee porterait
    alors un verdict perime.
    """
    reference = mesures_reference.PARAMETRES.get(mesure.parametre, {})
    return {
        "id": mesure.id,
        "parametre": mesure.parametre,
        "valeur": mesure.valeur,
        "unite": mesure.unite,
        "date_prelevement": mesure.date_prelevement,
        "laboratoire": mesure.laboratoire,
        "observations": mesure.observations,
        "cree_le": mesure.cree_le,
        "chantier_id": mesure.chantier_id,
        "chantier_nom": mesure.chantier.nom if mesure.chantier else None,
        "etat": (mesures_reference.evaluer(mesure.parametre, mesure.valeur)
                 if reference else None),
        "limite": reference.get("limite"),
        "source_limite": reference.get("source"),
    }


@router.get("/parametres")
def lister_parametres(
        courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    """Les grandeurs mesurables, avec leur unite et leur valeur limite.

    L'ecran de saisie s'en sert pour proposer les choix et rappeler la
    source de chaque limite : un rapport doit pouvoir dire d'ou vient le
    nombre auquel il compare la mesure.
    """
    return [
        {"code": code, **reference}
        for code, reference in mesures_reference.PARAMETRES.items()
    ]


@router.get("", response_model=list[schemas.MesurePrestataireOut])
def lister_mesures(
        chantier_id: Optional[int] = Query(None),
        parametre: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    """Les mesures versees au dossier, de la plus recente a la plus ancienne.

    Le tri suit la date de prelevement, non celle de saisie : un rapport
    de laboratoire peut arriver des semaines apres le terrain, et c'est
    le moment du prelevement qui situe la mesure.
    """
    if courant.role == models.RoleEnum.PLAIGNANT:
        raise HTTPException(
            status_code=403,
            detail="Consultez vos doléances sur /citoyen/doleances.")

    q = db.query(models.MesurePrestataire)
    if chantier_id:
        q = q.filter(models.MesurePrestataire.chantier_id == chantier_id)
    if parametre:
        code = parametre.upper()
        if not mesures_reference.parametre_valide(code):
            raise HTTPException(
                status_code=422,
                detail=f"Paramètre inconnu : « {parametre} ». Valeurs "
                       f"admises : "
                       f"{', '.join(sorted(mesures_reference.PARAMETRES))}.")
        q = q.filter(models.MesurePrestataire.parametre == code)

    mesures = q.order_by(
        models.MesurePrestataire.date_prelevement.desc()).all()
    return [_serialiser(m) for m in mesures]


@router.post("", response_model=schemas.MesurePrestataireOut)
def ajouter_mesure(
        data: schemas.MesurePrestataireCreate,
        db: Session = Depends(get_db),
        courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    """Verse au dossier une mesure realisee par un laboratoire agree."""
    if courant.role not in ROLES_SAISIE:
        raise HTTPException(
            status_code=403,
            detail="La saisie des mesures du prestataire agréé relève du "
                   "Spécialiste Suivi Environnemental.")

    code = data.parametre.upper()
    if not mesures_reference.parametre_valide(code):
        raise HTTPException(
            status_code=422,
            detail=f"Paramètre inconnu : « {data.parametre} ». Valeurs "
                   f"admises : "
                   f"{', '.join(sorted(mesures_reference.PARAMETRES))}.")

    # Une mesure negative n'existe pour aucune des grandeurs suivies :
    # c'est une faute de saisie, et l'accepter fausserait les moyennes du
    # rapport.
    if data.valeur < 0:
        raise HTTPException(
            status_code=422,
            detail="Une mesure ne peut pas être négative.")

    # Une mesure datee du futur ne peut pas avoir ete prelevee.
    if data.date_prelevement > datetime.utcnow():
        raise HTTPException(
            status_code=422,
            detail="La date de prélèvement ne peut pas être postérieure "
                   "à aujourd'hui.")

    if not db.query(models.Chantier).filter(
            models.Chantier.id == data.chantier_id).first():
        raise HTTPException(status_code=404, detail="Chantier introuvable")

    mesure = models.MesurePrestataire(
        parametre=code,
        valeur=data.valeur,
        # L'unite decoule du parametre : la laisser libre permettrait de
        # verser des decibels bruts a cote de dB(A).
        unite=mesures_reference.unite_de(code),
        date_prelevement=data.date_prelevement,
        laboratoire=data.laboratoire.strip(),
        observations=(data.observations or "").strip() or None,
        chantier_id=data.chantier_id,
        saisie_par_id=courant.id,
    )
    db.add(mesure)
    db.commit()
    db.refresh(mesure)
    return _serialiser(mesure)


@router.delete("/{mesure_id}")
def supprimer_mesure(
        mesure_id: int,
        db: Session = Depends(get_db),
        courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    """Retire une mesure versee par erreur.

    Une mesure fausse dans un rapport de conformite est pire qu'une
    mesure absente : elle se compare, se moyenne, et fonde une
    conclusion. La correction doit donc rester possible, mais reservee
    au profil qui a la responsabilite du rapport.
    """
    if courant.role not in ROLES_SAISIE:
        raise HTTPException(
            status_code=403,
            detail="La correction des mesures relève du Spécialiste "
                   "Suivi Environnemental.")
    mesure = db.query(models.MesurePrestataire).filter(
        models.MesurePrestataire.id == mesure_id).first()
    if not mesure:
        raise HTTPException(status_code=404, detail="Mesure introuvable")
    db.delete(mesure)
    db.commit()
    return {"detail": "Mesure retirée du dossier."}
