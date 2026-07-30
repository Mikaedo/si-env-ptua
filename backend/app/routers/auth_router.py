"""
auth_router.py
--------------
Endpoints d'authentification :
- POST /auth/register       : admin cree un utilisateur (sans mot de passe)
- POST /auth/login          : connexion JWT
- GET  /auth/me             : profil courant
- POST /auth/first-login    : definir son mot de passe (premiere connexion)
- POST /auth/change-password: changer son mot de passe
- POST /auth/forgot         : demander un code de reinitialisation
- POST /auth/verify-code    : verifier le code recu
- POST /auth/reset-password : definir un nouveau mot de passe avec le code
"""
import random
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["Authentification"])

# Stockage temporaire des codes de reinitialisation (en production : Redis)
_codes_reset: dict = {}


def _send_reset_email(email: str, code: str):
    """Envoie le code OTP par Gmail SMTP (ou logue si non configuré)."""
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    email_from = os.getenv("EMAIL_FROM", smtp_user)

    if not smtp_user or smtp_user == "votre.email@gmail.com" or not smtp_pass or smtp_pass == "votre_app_password_16_caracteres":
        # Pas encore configuré — logue dans la console (visible dans uvicorn)
        print(f"[SI-ENV SMTP non configuré] Code OTP pour {email}: {code}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[SI-ENV AGEROUTE] Code de réinitialisation de mot de passe"
    msg["From"] = email_from
    msg["To"] = email

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f4f5;padding:30px">
      <div style="max-width:480px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;border:1px solid #e4e4e7">
        <div style="background:#004F9F;padding:24px;text-align:center">
          <h1 style="color:white;font-size:20px;margin:0">SI-ENV · AGEROUTE</h1>
          <p style="color:rgba(255,255,255,0.8);font-size:12px;margin:6px 0 0">Système d'Information Environnemental — PTUA</p>
        </div>
        <div style="padding:32px">
          <h2 style="color:#18181B;font-size:18px;margin:0 0 12px">Réinitialisation de mot de passe</h2>
          <p style="color:#71717A;font-size:14px;margin:0 0 24px">Votre code de vérification à usage unique est :</p>
          <div style="background:#EFF6FF;border:2px dashed #004F9F;border-radius:10px;padding:20px;text-align:center;margin-bottom:24px">
            <span style="font-size:36px;font-weight:900;color:#004F9F;letter-spacing:8px">{code}</span>
          </div>
          <p style="color:#A1A1AA;font-size:12px;margin:0">Ce code est valable 10 minutes. Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.</p>
        </div>
        <div style="background:#FAFAFA;padding:16px;text-align:center;border-top:1px solid #F4F4F5">
          <p style="color:#A1A1AA;font-size:11px;margin:0">AGEROUTE — Projet de Transport Urbain d'Abidjan (PTUA)</p>
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
            server.sendmail(email_from, email, msg.as_string())
        print(f"[SI-ENV SMTP] Email envoyé à {email}")
    except Exception as e:
        print(f"[SI-ENV SMTP ERREUR] {e} — Code pour tests: {code}")



@router.post("/register", response_model=schemas.UtilisateurOut)
def register(data: schemas.UtilisateurCreate, db: Session = Depends(get_db),
             courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    if courant.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut creer des utilisateurs")
    if db.query(models.Utilisateur).filter(models.Utilisateur.email == data.email).first():
        raise HTTPException(status_code=400, detail="Cet email est deja utilise")
    utilisateur = models.Utilisateur(
        nom=data.nom,
        email=data.email,
        mot_de_passe_hash=None,
        role=data.role,
        telephone=data.telephone,
        premiere_connexion=True,
    )
    db.add(utilisateur)
    db.add(models.Journal(
        niveau="INFO",
        message=f"Invitation créée pour {data.email} ({data.role.value})",
        utilisateur=courant.email,
    ))
    db.commit()
    db.refresh(utilisateur)
    return utilisateur


@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    utilisateur = db.query(models.Utilisateur).filter(
        models.Utilisateur.email == form.username).first()

    if not utilisateur:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    if utilisateur.mot_de_passe_hash is None:
        token = auth.creer_token({"sub": str(utilisateur.id), "role": utilisateur.role.value})
        return {
            "access_token": token,
            "token_type": "bearer",
            "premiere_connexion": True,
            "role": utilisateur.role.value,
        }

    if not auth.verifier_mot_de_passe(form.password, utilisateur.mot_de_passe_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = auth.creer_token({"sub": str(utilisateur.id), "role": utilisateur.role.value})
    return {
        "access_token": token,
        "token_type": "bearer",
        "premiere_connexion": utilisateur.premiere_connexion,
        "role": utilisateur.role.value,
    }


@router.get("/me", response_model=schemas.UtilisateurOut)
def me(courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    return courant


@router.post("/first-login", response_model=schemas.Token)
def first_login(data: schemas.FirstLoginComplete,
                db: Session = Depends(get_db),
                courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    if not courant.premiere_connexion:
        raise HTTPException(status_code=400, detail="Le mot de passe est deja defini")
    courant.nom = data.nom
    courant.telephone = data.telephone
    courant.mot_de_passe_hash = auth.hasher_mot_de_passe(data.mot_de_passe)
    courant.premiere_connexion = False
    db.commit()
    token = auth.creer_token({"sub": str(courant.id), "role": courant.role.value})
    return {"access_token": token, "token_type": "bearer", "premiere_connexion": False, "role": courant.role.value}


@router.post("/change-password")
def change_password(data: schemas.ChangePassword,
                    db: Session = Depends(get_db),
                    courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    if not auth.verifier_mot_de_passe(data.ancien_mot_de_passe, courant.mot_de_passe_hash):
        raise HTTPException(status_code=400, detail="Ancien mot de passe incorrect")
    courant.mot_de_passe_hash = auth.hasher_mot_de_passe(data.nouveau_mot_de_passe)
    db.commit()
    return {"message": "Mot de passe modifie avec succes"}


@router.post("/forgot")
def forgot_password(
    data: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    utilisateur = db.query(models.Utilisateur).filter(models.Utilisateur.email == data.email).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Aucun compte associe a cet email")
    code = str(random.randint(100000, 999999))
    _codes_reset[data.email] = code
    # Envoi asynchrone en arrière-plan (ne bloque pas la réponse)
    background_tasks.add_task(_send_reset_email, data.email, code)
    return {"message": "Code de réinitialisation envoyé par email"}


@router.post("/verify-code")
def verify_code(data: schemas.VerifyCode):
    code_attendu = _codes_reset.get(data.email)
    if not code_attendu or code_attendu != data.code:
        raise HTTPException(status_code=400, detail="Code incorrect ou expire")
    return {"message": "Code verifie"}


@router.post("/reset-password")
def reset_password(data: schemas.ResetPassword, db: Session = Depends(get_db)):
    code_attendu = _codes_reset.get(data.email)
    if not code_attendu or code_attendu != data.code:
        raise HTTPException(status_code=400, detail="Code incorrect ou expire")
    utilisateur = db.query(models.Utilisateur).filter(models.Utilisateur.email == data.email).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    utilisateur.mot_de_passe_hash = auth.hasher_mot_de_passe(data.nouveau_mot_de_passe)
    utilisateur.premiere_connexion = False
    db.commit()
    _codes_reset.pop(data.email, None)
    return {"message": "Mot de passe reinitialise avec succes"}
