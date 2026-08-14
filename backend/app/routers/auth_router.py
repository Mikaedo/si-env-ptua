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
import os
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db
from ..services.email_service import envoyer_email
from ..services import otp_service

router = APIRouter(prefix="/auth", tags=["Authentification"])


def _send_reset_email(email: str, code: str):
    """Envoie le code OTP via le service email (Resend prod / SMTP dev).

    Le service choisit lui-meme le backend en fonction des variables presentes
    (RESEND_API_KEY prioritaire, sinon SMTP_USER/PASSWORD). En cas d'echec,
    le code est journalise dans les logs Render pour recuperation manuelle.
    """
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

    sujet = "[SI-ENV] Code de reinitialisation de mot de passe"
    succes = envoyer_email(email, sujet, html_body, texte)
    if not succes:
        # Aucun backend n'a reussi : on trace le code pour permettre la
        # reinitialisation manuelle depuis les logs de production.
        print(f"[SI-ENV EMAIL] Envoi impossible pour {email} — Code pour tests: {code}")



@router.post("/register", response_model=schemas.UtilisateurOut)
def register(data: schemas.UtilisateurCreate,
             background_tasks: BackgroundTasks,
             db: Session = Depends(get_db),
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

    # Notification e-mail au nouvel utilisateur pour l'informer qu'un compte a
    # ete cree a son nom. Envoi en arriere-plan pour ne pas ralentir la
    # reponse HTTP a l'administrateur. On passe des STRINGS et non l'objet ORM :
    # la session SQLAlchemy est fermee avant que le background task ne s'execute,
    # ce qui rendrait un acces .role/.nom impossible (DetachedInstanceError).
    role_str = utilisateur.role.value if hasattr(utilisateur.role, "value") else str(utilisateur.role)
    background_tasks.add_task(
        _envoyer_email_bienvenue,
        utilisateur.email,
        utilisateur.nom or utilisateur.email.split("@")[0],
        role_str,
        courant.email,
    )

    return utilisateur


def _envoyer_email_bienvenue(email_dest: str,
                             nom_affiche: str,
                             role_str: str,
                             email_admin: str) -> None:
    """Envoie un email de bienvenue au nouvel utilisateur."""
    dashboard_url = os.getenv("FRONTEND_URL", "https://si-env-ptua.pages.dev")
    libelles_role = {
        "ADMIN": "Administrateur",
        "RESP_ENV": "Responsable Environnement",
        "EXPERT_HSE": "Expert HSE",
        "SPEC_ENV": "Spécialiste Suivi Environnemental",
        "SPEC_PAR": "Spécialiste Suivi du P.A.R",
    }
    libelle = libelles_role.get(role_str, role_str)

    # Le lien vise la page d'activation et non la racine du tableau de bord.
    # Pointer vers la racine renvoyait l'utilisateur sur la session deja
    # ouverte dans son navigateur au lieu de son propre parcours.
    lien_activation = (
        f"{dashboard_url}/premiere-connexion"
        f"?email={quote(email_dest, safe='')}"
    )

    sujet = "[SI-ENV] Bienvenue - votre compte a ete cree"

    texte = (
        f"SI-ENV AGEROUTE\n\n"
        f"Bonjour {nom_affiche},\n\n"
        f"Un compte SI-ENV vient de vous etre attribue par {email_admin}.\n\n"
        f"  Email        : {email_dest}\n"
        f"  Role         : {libelle}\n\n"
        f"Pour activer votre compte et definir votre mot de passe,\n"
        f"rendez-vous sur :\n"
        f"{lien_activation}\n\n"
        f"--\n"
        f"AGEROUTE - Projet de Transport Urbain d'Abidjan\n"
    )

    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:#0F172A;line-height:1.55">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:32px 16px">
    <tr><td align="center">
      <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFFFF;border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.06);border:1px solid #E2E8F0">
        <tr><td style="background:linear-gradient(135deg,#004F9F 0%,#003063 100%);padding:32px 32px 28px;text-align:center">
          <div style="display:inline-block;width:56px;height:56px;line-height:56px;border-radius:14px;background:rgba(255,255,255,0.14);color:#FFFFFF;font-size:26px;font-weight:800;margin-bottom:12px">SE</div>
          <div style="color:#FFFFFF;font-size:20px;font-weight:700;letter-spacing:0.3px">SI-ENV</div>
          <div style="color:rgba(255,255,255,0.72);font-size:12px;margin-top:4px">Système d'Information Environnemental &middot; PTUA</div>
        </td></tr>
        <tr><td style="padding:36px 36px 24px">
          <h1 style="margin:0 0 8px;font-size:20px;font-weight:700;color:#0F172A">Bienvenue {nom_affiche}</h1>
          <p style="margin:0 0 24px;font-size:14px;color:#475569">
            L'administrateur AGEROUTE ({email_admin}) vient de vous créer un
            compte sur le Système d'Information Environnemental du PTUA.
          </p>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;background:#F8FAFC;border-radius:10px;border:1px solid #E2E8F0">
            <tr>
              <td style="padding:12px 16px;font-size:12px;color:#64748B;border-bottom:1px solid #E2E8F0;width:35%">Adresse e-mail</td>
              <td style="padding:12px 16px;font-size:13px;font-weight:600;color:#0F172A;border-bottom:1px solid #E2E8F0">{email_dest}</td>
            </tr>
            <tr>
              <td style="padding:12px 16px;font-size:12px;color:#64748B">Rôle attribué</td>
              <td style="padding:12px 16px;font-size:13px;font-weight:600;color:#0F172A">{libelle}</td>
            </tr>
          </table>
          <p style="margin:0 0 20px;font-size:14px;color:#475569">
            Cliquez sur le bouton ci-dessous pour activer votre compte
            et choisir votre mot de passe.
          </p>
          <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto" align="center">
            <tr><td style="background:#F37021;border-radius:10px">
              <a href="{lien_activation}" style="display:inline-block;padding:12px 28px;color:#FFFFFF;font-size:14px;font-weight:600;text-decoration:none;border-radius:10px">Activer mon compte</a>
            </td></tr>
          </table>
        </td></tr>
        <tr><td style="background:#F8FAFC;padding:18px 32px;border-top:1px solid #E2E8F0;text-align:center">
          <div style="font-size:12px;color:#64748B;font-weight:600">AGEROUTE &middot; Agence de Gestion des Routes</div>
          <div style="font-size:11px;color:#94A3B8;margin-top:4px">Projet de Transport Urbain d'Abidjan &middot; Cellule de Coordination</div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""

    envoyer_email(email_dest, sujet, html, texte)


@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(),
          background_tasks: BackgroundTasks = None,
          db: Session = Depends(get_db)):
    utilisateur = db.query(models.Utilisateur).filter(
        models.Utilisateur.email == form.username).first()
    if not utilisateur:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    # Premiere connexion (mot de passe non defini) : on retourne un jeton
    # d'acces immediat pour que le client puisse appeler /auth/first-login.
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

    # 2FA activee : on ne remet pas encore de jeton. On genere un code, on
    # l'envoie par email, et le client devra completer via /auth/2fa/verifier.
    if utilisateur.twofa_email_actif:
        code = otp_service.emettre(db, utilisateur.email, motif="twofa", duree_min=10)
        if background_tasks is not None:
            background_tasks.add_task(_envoyer_email_2fa, utilisateur.email, code)
        return {
            "access_token": "",
            "token_type": "bearer",
            "premiere_connexion": False,
            "role": utilisateur.role.value,
            "twofa_requis": True,
            "twofa_email": utilisateur.email,
        }

    access = auth.creer_token({"sub": str(utilisateur.id), "role": utilisateur.role.value})
    refresh = auth.emettre_refresh_token(db, utilisateur)
    return {
        "access_token": access,
        "token_type": "bearer",
        "premiere_connexion": utilisateur.premiere_connexion,
        "role": utilisateur.role.value,
        "refresh_token": refresh,
    }


@router.post("/2fa/verifier", response_model=schemas.Token)
def verifier_2fa(data: schemas.TwoFactorVerify, db: Session = Depends(get_db)):
    """Finalise la connexion apres saisie du code 2FA recu par email."""
    if not otp_service.verifier(db, data.email, data.code, motif="twofa"):
        raise HTTPException(status_code=400, detail="Code 2FA incorrect ou expire")
    utilisateur = db.query(models.Utilisateur).filter(
        models.Utilisateur.email == data.email.lower()).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    access = auth.creer_token({"sub": str(utilisateur.id), "role": utilisateur.role.value})
    refresh = auth.emettre_refresh_token(db, utilisateur)
    return {
        "access_token": access, "token_type": "bearer",
        "premiere_connexion": utilisateur.premiere_connexion,
        "role": utilisateur.role.value, "refresh_token": refresh,
    }


@router.post("/2fa/configurer")
def configurer_2fa(data: schemas.TwoFactorConfig,
                   db: Session = Depends(get_db),
                   courant: models.Utilisateur = Depends(auth.utilisateur_courant)):
    """Active ou desactive la 2FA par email pour l'utilisateur connecte."""
    courant.twofa_email_actif = bool(data.actif)
    db.commit()
    return {"twofa_email_actif": courant.twofa_email_actif}


@router.post("/refresh", response_model=schemas.Token)
def refresh_access(data: schemas.RefreshInput, db: Session = Depends(get_db)):
    """Emet un nouvel access token a partir d'un refresh token valide."""
    access, utilisateur = auth.echanger_refresh_token(db, data.refresh_token)
    return {
        "access_token": access, "token_type": "bearer",
        "premiere_connexion": utilisateur.premiere_connexion,
        "role": utilisateur.role.value, "refresh_token": data.refresh_token,
    }


@router.post("/logout")
def logout(data: schemas.RefreshInput, db: Session = Depends(get_db)):
    """Revoque un refresh token (deconnexion cote client)."""
    auth.revoquer_refresh_token(db, data.refresh_token)
    return {"message": "Deconnexion effectuee"}


def _envoyer_email_2fa(email: str, code: str) -> None:
    """Email court dedie au code 2FA (different du reset mot de passe)."""
    dashboard_url = os.getenv("FRONTEND_URL", "https://si-env-ptua.pages.dev")
    sujet = "[SI-ENV] Code de verification en deux etapes"
    texte = (
        f"SI-ENV AGEROUTE\n\n"
        f"Code de verification en deux etapes : {code}\n\n"
        f"Valable 10 minutes. Si vous n'avez pas tente de vous connecter,\n"
        f"changez immediatement votre mot de passe.\n\n"
        f"{dashboard_url}\n"
    )
    html = f"""<!DOCTYPE html>
<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:#F1F5F9;padding:32px 16px;color:#0F172A">
<table role="presentation" width="100%"><tr><td align="center">
<table role="presentation" width="480" style="background:#FFFFFF;border-radius:14px;overflow:hidden;border:1px solid #E2E8F0">
  <tr><td style="background:#004F9F;padding:24px;text-align:center;color:#FFFFFF">
    <div style="font-size:11px;letter-spacing:1.2px;opacity:0.85">SI-ENV &middot; AGEROUTE</div>
    <div style="font-size:18px;font-weight:700;margin-top:6px">Verification en deux etapes</div>
  </td></tr>
  <tr><td style="padding:32px;text-align:center">
    <div style="font-size:38px;font-weight:800;color:#004F9F;letter-spacing:10px;font-family:monospace">{code}</div>
    <p style="margin:18px 0 0;font-size:12px;color:#64748B">Valable 10 minutes</p>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""
    envoyer_email(email, sujet, html, texte)


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
    # Code emis et persiste en base : survit aux redemarrages du service.
    code = otp_service.emettre(db, data.email, motif="reset", duree_min=10)
    background_tasks.add_task(_send_reset_email, data.email, code)
    return {"message": "Code de réinitialisation envoyé par email"}


@router.post("/verify-code")
def verify_code(data: schemas.VerifyCode, db: Session = Depends(get_db)):
    """Verifie sans consommer : usage informationnel. Le vrai reset consomme."""
    # On requete sans marquer consomme_le : c'est reset-password qui le fait
    from datetime import datetime
    otp = db.query(models.OtpCode).filter(
        models.OtpCode.email == data.email.strip().lower(),
        models.OtpCode.motif == "reset",
        models.OtpCode.code == data.code.strip(),
        models.OtpCode.consomme_le.is_(None),
        models.OtpCode.expire_le >= datetime.utcnow(),
    ).first()
    if not otp:
        raise HTTPException(status_code=400, detail="Code incorrect ou expire")
    return {"message": "Code verifie"}


@router.post("/reset-password")
def reset_password(data: schemas.ResetPassword, db: Session = Depends(get_db)):
    # verifier() consomme le code atomiquement, pas de course entre verify et reset.
    if not otp_service.verifier(db, data.email, data.code, motif="reset"):
        raise HTTPException(status_code=400, detail="Code incorrect ou expire")
    utilisateur = db.query(models.Utilisateur).filter(
        models.Utilisateur.email == data.email).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    utilisateur.mot_de_passe_hash = auth.hasher_mot_de_passe(data.nouveau_mot_de_passe)
    utilisateur.premiere_connexion = False
    # Revoque tous les refresh tokens : force la reconnexion partout ou l'ancien
    # mot de passe etait potentiellement en usage (session compromise).
    db.query(models.RefreshToken).filter(
        models.RefreshToken.utilisateur_id == utilisateur.id
    ).update({"revoque": True})
    db.commit()
    return {"message": "Mot de passe reinitialise avec succes"}
