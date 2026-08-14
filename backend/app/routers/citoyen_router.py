"""
citoyen_router.py
-----------------
Points d'entree de l'application mobile destinee aux riverains des chantiers.

Le Mecanisme de Gestion des Plaintes du PTUA reposait jusqu'ici sur un recueil
au guichet ou lors des reunions de quartier, ce qui suppose qu'un habitant se
deplace et tombe sur une permanence ouverte. Beaucoup de nuisances ne
remontaient donc jamais. Ce routeur ouvre un second canal, depuis le telephone
de la personne concernee, sans rien changer au traitement en aval : les
doleances rejoignent la meme file que les plaintes classiques, instruite par
le specialiste du suivi du Plan d'Action de Reinstallation.

L'acces est conditionne a la proximite geographique. Une plainte
environnementale n'a de sens que si elle emane de quelqu'un qui subit
reellement la nuisance, et le dispositif serait vite sature s'il acceptait des
signalements depuis n'importe ou. La verification s'appuie sur le rayon
d'influence propre a chaque chantier, notion que le PGES manipule deja sous le
nom de zone d'influence directe.
"""
import math
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services.email_service import envoyer_email

router = APIRouter(prefix="/citoyen", tags=["Application citoyenne"])

#: Rayon terrestre moyen, en metres.
_RAYON_TERRE_M = 6_371_000.0


def distance_metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance orthodromique entre deux points, formule de haversine.

    Le calcul est fait en Python plutot qu'en SQL avec ST_Distance pour une
    raison pratique : il doit fonctionner a l'identique sous PostgreSQL en
    production et sous SQLite pendant les tests, ou PostGIS n'existe pas. La
    precision de la formule, de l'ordre de quelques metres sur ces distances,
    est tres largement suffisante face a l'incertitude du GPS d'un telephone,
    qui se compte plutot en dizaines de metres en milieu urbain.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    return 2 * _RAYON_TERRE_M * math.asin(math.sqrt(a))


def _coordonnees_chantier(chantier: models.Chantier) -> tuple[float, float] | None:
    """Extrait la latitude et la longitude d'un chantier.

    La geometrie est lue depuis la colonne PostGIS quand elle est disponible,
    et depuis sa representation textuelle sous SQLite. Retourne None si le
    chantier n'a pas encore ete positionne sur la carte.
    """
    if chantier.geom is None:
        return None
    try:
        from geoalchemy2.shape import to_shape
        point = to_shape(chantier.geom)
        return point.y, point.x
    except Exception:
        # Repli sur le format texte "POINT(lon lat)" rencontre hors PostGIS.
        try:
            brut = str(chantier.geom)
            interieur = brut[brut.index("(") + 1:brut.index(")")]
            lon, lat = (float(v) for v in interieur.split())
            return lat, lon
        except Exception:
            return None


def chantier_le_plus_proche(
    db: Session, latitude: float, longitude: float
) -> tuple[models.Chantier | None, float]:
    """Retourne le chantier le plus proche d'une position et la distance.

    La distance vaut l'infini lorsqu'aucun chantier n'est positionne, ce qui
    conduit naturellement au refus d'acces en aval.
    """
    plus_proche, plus_courte = None, float("inf")
    for chantier in db.query(models.Chantier).all():
        coords = _coordonnees_chantier(chantier)
        if coords is None:
            continue
        distance = distance_metres(latitude, longitude, coords[0], coords[1])
        if distance < plus_courte:
            plus_proche, plus_courte = chantier, distance
    return plus_proche, plus_courte


def riverain_courant(
    courant: models.Utilisateur = Depends(auth.utilisateur_courant),
) -> models.Utilisateur:
    """Restreint l'acces aux comptes riverains."""
    if courant.role != models.RoleEnum.PLAIGNANT:
        raise HTTPException(
            status_code=403,
            detail="Cet espace est reserve aux riverains des chantiers.",
        )
    return courant


@router.post("/verifier-zone", response_model=schemas.ZoneVerifiee)
def verifier_zone(data: schemas.PositionGps, db: Session = Depends(get_db)):
    """Indique si une position ouvre droit a l'inscription, et sur quel chantier.

    Appele avant meme le formulaire d'inscription : mieux vaut prevenir la
    personne tout de suite que la laisser saisir ses informations pour lui
    opposer un refus ensuite.
    """
    chantier, distance = chantier_le_plus_proche(db, data.latitude, data.longitude)
    if chantier is None:
        raise HTTPException(
            status_code=404,
            detail="Aucun chantier n'est actuellement referencé sur la carte.",
        )

    autorise = distance <= chantier.rayon_influence_m
    return schemas.ZoneVerifiee(
        autorise=autorise,
        chantier_id=chantier.id,
        chantier_nom=chantier.nom,
        commune=chantier.commune,
        distance_m=round(distance),
        rayon_m=chantier.rayon_influence_m,
    )


@router.post("/inscription", response_model=schemas.Token)
def inscription(
    data: schemas.InscriptionCitoyen,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Cree un compte riverain a partir d'une position verifiee.

    Contrairement aux agents AGEROUTE, dont les comptes sont ouverts par
    l'administrateur, un habitant s'inscrit lui-meme : attendre une creation
    manuelle reviendrait a fermer le dispositif a ceux-la memes qu'il vise.
    Le rattachement au chantier est deduit de la position et non choisi dans
    une liste, un riverain n'ayant aucune raison de connaitre les
    denominations administratives des ouvrages.
    """
    adresse = data.email.strip().lower()

    if db.query(models.Utilisateur).filter(models.Utilisateur.email == adresse).first():
        raise HTTPException(status_code=400, detail="Un compte existe deja pour cette adresse.")

    chantier, distance = chantier_le_plus_proche(db, data.latitude, data.longitude)
    if chantier is None:
        raise HTTPException(
            status_code=404,
            detail="Aucun chantier n'est actuellement referencé sur la carte.",
        )
    if distance > chantier.rayon_influence_m:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Vous vous trouvez à {round(distance / 1000, 1)} km du chantier le plus "
                "proche. Cette application est réservée aux riverains des chantiers du PTUA."
            ),
        )

    riverain = models.Utilisateur(
        nom=data.nom.strip(),
        email=adresse,
        mot_de_passe_hash=auth.hasher_mot_de_passe(data.mot_de_passe),
        role=models.RoleEnum.PLAIGNANT,
        premiere_connexion=False,
        telephone=data.telephone,
        chantier_rattachement_id=chantier.id,
    )
    db.add(riverain)
    db.commit()
    db.refresh(riverain)

    background_tasks.add_task(
        _envoyer_confirmation_inscription,
        adresse, riverain.nom, chantier.nom, chantier.commune or "",
    )

    jeton = auth.creer_token({"sub": str(riverain.id), "role": riverain.role.value})
    return {
        "access_token": jeton,
        "token_type": "bearer",
        "premiere_connexion": False,
        "role": riverain.role.value,
    }


@router.get("/mon-chantier", response_model=schemas.ChantierOut)
def mon_chantier(
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(riverain_courant),
):
    """Chantier auquel le riverain est rattache."""
    chantier = db.query(models.Chantier).filter(
        models.Chantier.id == courant.chantier_rattachement_id
    ).first()
    if chantier is None:
        raise HTTPException(status_code=404, detail="Aucun chantier de rattachement.")
    return chantier


@router.post("/doleances", response_model=schemas.DoleanceOut)
def deposer_doleance(
    data: schemas.DoleanceCreate,
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(riverain_courant),
):
    """Enregistre une doleance et l'oriente vers le chantier concerne.

    Le chantier retenu est celui le plus proche du lieu de la nuisance, qui
    n'est pas forcement celui du rattachement : une personne peut constater un
    probleme en se rendant a son travail. A defaut de position transmise, on
    retombe sur son chantier de rattachement.
    """
    chantier_id = courant.chantier_rattachement_id
    if data.latitude is not None and data.longitude is not None:
        proche, _ = chantier_le_plus_proche(db, data.latitude, data.longitude)
        if proche is not None:
            chantier_id = proche.id

    doleance = models.Plainte(
        nom_plaignant=courant.nom or courant.email,
        contact=courant.telephone or courant.email,
        description=data.description.strip(),
        statut="OUVERTE",
        chantier_id=chantier_id,
        plaignant_id=courant.id,
        categorie=data.categorie,
        canal="MOBILE",
        cree_le=datetime.utcnow(),
    )
    if data.latitude is not None and data.longitude is not None:
        doleance.geom = f"SRID=4326;POINT({data.longitude} {data.latitude})"

    db.add(doleance)
    db.commit()
    db.refresh(doleance)
    return doleance


@router.get("/doleances", response_model=list[schemas.DoleanceOut])
def mes_doleances(
    db: Session = Depends(get_db),
    courant: models.Utilisateur = Depends(riverain_courant),
):
    """Historique des doleances deposees par le riverain connecte."""
    return (
        db.query(models.Plainte)
        .filter(models.Plainte.plaignant_id == courant.id)
        .order_by(models.Plainte.cree_le.desc())
        .all()
    )


def _envoyer_confirmation_inscription(
    email_dest: str, nom: str, chantier: str, commune: str
) -> None:
    """Accuse reception de l'inscription d'un riverain."""
    sujet = "[SI-ENV] Votre compte riverain est actif"
    lieu = f"{chantier}, {commune}" if commune else chantier

    texte = (
        f"SI-ENV AGEROUTE\n\n"
        f"Bonjour {nom},\n\n"
        f"Votre compte riverain est actif. Vous etes rattache au chantier\n"
        f"suivant : {lieu}.\n\n"
        f"Vous pouvez desormais signaler depuis votre telephone toute nuisance\n"
        f"liee aux travaux : bruit, poussiere, circulation, eaux stagnantes.\n"
        f"Chaque doleance est transmise au specialiste charge du suivi social\n"
        f"du projet, qui en assure le traitement.\n\n"
        f"--\n"
        f"AGEROUTE - Projet de Transport Urbain d'Abidjan\n"
    )

    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:#0F172A;line-height:1.55">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:32px 16px">
    <tr><td align="center">
      <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFFFF;border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.06);border:1px solid #E2E8F0">
        <tr><td style="background:linear-gradient(135deg,#004F9F 0%,#003063 100%);padding:32px;text-align:center">
          <div style="color:#FFFFFF;font-size:20px;font-weight:700">SI-ENV Citoyen</div>
          <div style="color:rgba(255,255,255,0.72);font-size:12px;margin-top:4px">Votre voix dans le suivi environnemental du PTUA</div>
        </td></tr>
        <tr><td style="padding:36px 36px 28px">
          <h1 style="margin:0 0 10px;font-size:20px;font-weight:700">Bienvenue {nom}</h1>
          <p style="margin:0 0 22px;font-size:14px;color:#475569">
            Votre compte est actif. Vous êtes rattaché au chantier
            <strong>{lieu}</strong>.
          </p>
          <p style="margin:0 0 22px;font-size:14px;color:#475569">
            Vous pouvez désormais signaler depuis votre téléphone toute nuisance
            liée aux travaux : bruit, poussière, circulation ou eaux stagnantes.
            Chaque doléance parvient au spécialiste chargé du suivi social du
            projet, qui en assure le traitement et vous en communique l'avancement.
          </p>
          <div style="padding:14px 16px;background:#F8FAFC;border-radius:10px;border:1px solid #E2E8F0;font-size:13px;color:#64748B">
            Ce dispositif s'inscrit dans le Mécanisme de Gestion des Plaintes du
            Projet de Transport Urbain d'Abidjan.
          </div>
        </td></tr>
        <tr><td style="background:#F8FAFC;padding:18px 32px;border-top:1px solid #E2E8F0;text-align:center">
          <div style="font-size:12px;color:#64748B;font-weight:600">AGEROUTE &middot; Agence de Gestion des Routes</div>
          <div style="font-size:11px;color:#94A3B8;margin-top:4px">Projet de Transport Urbain d'Abidjan</div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""

    envoyer_email(email_dest, sujet, html, texte)
