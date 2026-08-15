import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { LucideAngularModule, Eye, EyeOff, LogIn, AlertCircle, X, Mail, KeyRound, Lock } from 'lucide-angular';

@Component({
  selector: 'app-login',
  imports: [CommonModule, LucideAngularModule, FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class Login {
  private auth = inject(AuthService);
  private router = inject(Router);

  readonly Eye = Eye;
  readonly EyeOff = EyeOff;
  readonly LogIn = LogIn;
  readonly AlertCircle = AlertCircle;
  readonly X = X;
  readonly Mail = Mail;
  readonly KeyRound = KeyRound;
  readonly Lock = Lock;

  // Connexion
  email = signal('');
  password = signal('');
  showPassword = signal(false);
  loading = signal(false);
  error = signal('');

  // Mot de passe oublié
  showForgot = signal(false);
  forgotStep = signal(0); // 0=email, 1=code, 2=nouveau mdp
  forgotEmail = signal('');
  forgotCode = signal('');
  forgotNewPassword = signal('');
  forgotConfirm = signal('');
  forgotLoading = signal(false);
  forgotError = signal('');
  forgotSuccess = signal('');

  openForgot() {
    this.showForgot.set(true);
    this.forgotStep.set(0);
    this.forgotEmail.set(this.email()); // pré-remplir avec l'email saisi
    this.forgotError.set('');
    this.forgotSuccess.set('');
  }

  closeForgot() {
    this.showForgot.set(false);
    this.forgotError.set('');
    this.forgotSuccess.set('');
  }

  onForgotStep1() {
    if (!this.forgotEmail()) { this.forgotError.set('Veuillez saisir votre email'); return; }
    this.forgotLoading.set(true);
    this.forgotError.set('');
    this.auth.forgotPassword(this.forgotEmail()).subscribe({
      next: () => {
        this.forgotLoading.set(false);
        this.forgotStep.set(1);
      },
      error: () => {
        this.forgotLoading.set(false);
        this.forgotError.set('Aucun compte associé à cet email');
      }
    });
  }

  onForgotStep2() {
    if (!this.forgotCode() || this.forgotCode().length < 4) { this.forgotError.set('Code invalide'); return; }
    this.forgotLoading.set(true);
    this.forgotError.set('');
    this.auth.verifyCode(this.forgotEmail(), this.forgotCode()).subscribe({
      next: () => {
        this.forgotLoading.set(false);
        this.forgotStep.set(2);
      },
      error: () => {
        this.forgotLoading.set(false);
        this.forgotError.set('Code incorrect ou expiré');
      }
    });
  }

  onForgotStep3() {
    if (!this.forgotNewPassword() || this.forgotNewPassword().length < 8) {
      this.forgotError.set('Le mot de passe doit contenir au moins 8 caractères');
      return;
    }
    if (this.forgotNewPassword() !== this.forgotConfirm()) {
      this.forgotError.set('Les mots de passe ne correspondent pas');
      return;
    }
    this.forgotLoading.set(true);
    this.forgotError.set('');
    this.auth.resetPassword(this.forgotEmail(), this.forgotCode(), this.forgotNewPassword()).subscribe({
      next: () => {
        this.forgotLoading.set(false);
        this.forgotSuccess.set('Mot de passe réinitialisé avec succès !');
        setTimeout(() => this.closeForgot(), 2500);
      },
      error: () => {
        this.forgotLoading.set(false);
        this.forgotError.set('Erreur lors de la réinitialisation');
      }
    });
  }

  onLogin() {
    if (!this.email() || !this.password()) {
      this.error.set('Veuillez saisir vos identifiants');
      return;
    }

    this.loading.set(true);
    this.error.set('');

    // Profils admis sur le tableau de bord. Les agents de terrain passent par
    // l'application mobile, les riverains par l'application citoyenne.
    const allowedRoles = ['ADMIN', 'SPEC_ENV', 'SPEC_PAR', 'ANDE', 'BAD'];

    this.auth.login(this.email(), this.password()).subscribe({
      next: (res) => {
        this.loading.set(false);
        if (res.premiere_connexion) {
          // Un compte web n'a pas forcement d'homologue mobile : renvoyer
          // l'utilisateur vers le telephone le laissait sans issue. On
          // l'oriente desormais vers le parcours d'activation du tableau
          // de bord, en lui evitant de ressaisir son adresse.
          const adresse = this.email().trim();
          this.auth.logout();
          this.router.navigate(['/premiere-connexion'], { queryParams: { email: adresse } });
          return;
        }
        if (!allowedRoles.includes(res.role)) {
          this.error.set('Email ou mot de passe incorrect');
          this.auth.logout();
          return;
        }
        this.router.navigate(['/dashboard']);
      },
      error: () => {
        this.loading.set(false);
        this.error.set('Email ou mot de passe incorrect');
      }
    });
  }
}
