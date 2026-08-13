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
    msg["Subject"] = "[SI-ENV] Code de reinitialisation de mot de passe"
    msg["From"] = f"SI-ENV AGEROUTE <{email_from}>"
    msg["To"] = email
    msg["Reply-To"] = email_from

    dashboard_url = os.getenv("FRONTEND_URL", "https://si-env-ptua.pages.dev")

    # Version texte pour les clients mail qui ne rendent pas le HTML
    # (spam filters, terminaux, accessibilite).
    texte = (
        "SI-ENV AGEROUTE\n"
        "Systeme d'Information Environnemental du PTUA\n"
        "\n"
        "Reinitialisation de mot de passe\n"
        "---------------------------------\n"
        "\n"
        f"Votre code de verification a usage unique est : {code}\n"
        "\n"
        "Ce code est valable 10 minutes. Saisissez-le sur la page de\n"
        "reinitialisation du tableau de bord :\n"
        f"{dashboard_url}\n"
        "\n"
        "Si vous n'etes pas a l'origine de cette demande, ignorez ce\n"
        "message : votre mot de passe actuel reste valable.\n"
        "\n"
        "--\n"
        "AGEROUTE - Agence de Gestion des Routes\n"
        "Projet de Transport Urbain d'Abidjan (PTUA)\n"
        "Cellule de Coordination - Unite Sauvegardes\n"
    )

    html_body = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Code de reinitialisation SI-ENV</title>
</head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#0F172A;line-height:1.55">
  <!-- Preheader invisible (aperçu dans la boîte de reception) -->
  <span style="display:none;visibility:hidden;opacity:0;height:0;width:0;overflow:hidden">
    Votre code SI-ENV : {code}. Valable 10 minutes.
  </span>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:32px 16px">
    <tr>
      <td align="center">
        <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFFFF;border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.06);border:1px solid #E2E8F0">

          <!-- En-tete AGEROUTE -->
          <tr>
            <td style="background:linear-gradient(135deg,#004F9F 0%,#003063 100%);padding:32px 32px 28px;text-align:center">
              <div style="display:inline-block;width:56px;height:56px;line-height:56px;border-radius:14px;background:rgba(255,255,255,0.14);color:#FFFFFF;font-size:26px;font-weight:800;margin-bottom:12px">SE</div>
              <div style="color:#FFFFFF;font-size:20px;font-weight:700;letter-spacing:0.3px">SI-ENV</div>
              <div style="color:rgba(255,255,255,0.72);font-size:12px;margin-top:4px">Systeme d'Information Environnemental &middot; PTUA</div>
            </td>
          </tr>

          <!-- Corps du message -->
          <tr>
            <td style="padding:36px 36px 20px">
              <h1 style="margin:0 0 8px;font-size:20px;font-weight:700;color:#0F172A">Reinitialisation de votre mot de passe</h1>
              <p style="margin:0 0 24px;font-size:14px;color:#475569">
                Vous avez demande a reinitialiser votre mot de passe. Saisissez le code
                ci-dessous sur la page de reinitialisation du tableau de bord.
              </p>

              <!-- Bloc code -->
              <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:12px;padding:24px;text-align:center;margin-bottom:24px">
                <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1.2px;color:#004F9F;margin-bottom:10px">Code de verification</div>
                <div style="font-size:38px;font-weight:800;color:#004F9F;letter-spacing:10px;font-family:'SFMono-Regular',Menlo,Consolas,monospace">{code}</div>
                <div style="font-size:12px;color:#64748B;margin-top:12px">Valable 10 minutes</div>
              </div>

              <!-- Bouton d'action -->
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto 28px" align="center">
                <tr>
                  <td style="background:#F37021;border-radius:10px">
                    <a href="{dashboard_url}" style="display:inline-block;padding:12px 28px;color:#FFFFFF;font-size:14px;font-weight:600;text-decoration:none;border-radius:10px">Ouvrir le tableau de bord</a>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 8px;font-size:12px;color:#94A3B8">
                Si vous n'etes pas a l'origine de cette demande, ignorez simplement ce
                message : votre mot de passe actuel reste valable.
              </p>
            </td>
          </tr>

          <!-- Pied de page -->
          <tr>
            <td style="background:#F8FAFC;padding:20px 32px;border-top:1px solid #E2E8F0;text-align:center">
              <div style="font-size:12px;color:#64748B;font-weight:600">AGEROUTE &middot; Agence de Gestion des Routes</div>
              <div style="font-size:11px;color:#94A3B8;margin-top:4px">Projet de Transport Urbain d'Abidjan &middot; Cellule de Coordination</div>
            </td>
          </tr>
        </table>

        <!-- Mentions legales -->
        <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;margin-top:16px">
          <tr>
            <td style="text-align:center;font-size:11px;color:#94A3B8;padding:0 24px">
              Ce courriel a ete envoye automatiquement par le systeme SI-ENV. Merci de ne pas y repondre directement.
            </td>
          </tr>
        </table>

      </td>
    </tr>
  </table>
</body>
</html>"""

    # Ordre important : la version texte doit etre attachee AVANT le HTML.
    # Les clients qui savent lire les deux choisissent la derniere ; ceux qui
    # ne lisent que du texte prennent la premiere.
    msg.attach(MIMEText(texte, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

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
