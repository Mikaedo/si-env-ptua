import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { LucideAngularModule, Eye, EyeOff, AlertCircle, UserPlus, Lock, Phone, User as UserIcon, CheckCircle } from 'lucide-angular';

/**
 * Page d'activation de compte, ouverte depuis le LIEN recu par email lorsque
 * l'administrateur cree un utilisateur. Le jeton present dans l'URL sert
 * d'autorisation : la page est donc accessible sans etre connecte.
 *
 * A ne pas confondre avec le parcours "mot de passe oublie", qui repose sur un
 * code a 6 chiffres saisi manuellement.
 */
@Component({
  selector: 'app-activation',
  imports: [CommonModule, LucideAngularModule, FormsModule],
  templateUrl: './activation.html',
  styleUrl: './activation.scss'
})
export class Activation implements OnInit {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  readonly Eye = Eye;
  readonly EyeOff = EyeOff;
  readonly AlertCircle = AlertCircle;
  readonly UserPlus = UserPlus;
  readonly Lock = Lock;
  readonly Phone = Phone;
  readonly UserIcon = UserIcon;
  readonly CheckCircle = CheckCircle;

  /** Etat du chargement initial du lien */
  verification = signal(true);
  lienValide = signal(false);
  erreurLien = signal('');

  /** Informations du compte a activer, renvoyees par le backend */
  email = signal('');
  role = signal('');

  /** Formulaire */
  nom = signal('');
  telephone = signal('');
  motDePasse = signal('');
  confirmation = signal('');
  afficherMdp = signal(false);
  enregistrement = signal(false);
  erreur = signal('');

  private token = '';

  /** Libelles lisibles des profils, alignes sur ceux du reste de l'application */
  private readonly libellesRoles: Record<string, string> = {
    ADMIN: 'Administrateur',
    RESP_ENV: 'Responsable Environnement',
    EXPERT_HSE: 'Expert HSE',
    SPEC_ENV: 'Spécialiste Environnement',
    SPEC_PAR: 'Spécialiste P.A.R'
  };

  /** Les profils terrain travaillent sur le mobile, les autres sur le web */
  private readonly rolesMobile = ['RESP_ENV', 'EXPERT_HSE'];

  get libelleRole(): string {
    return this.libellesRoles[this.role()] ?? this.role();
  }

  get destinationMobile(): boolean {
    return this.rolesMobile.includes(this.role());
  }

  allerConnexion(): void {
    this.router.navigate(['/login']);
  }

  ngOnInit(): void {
    this.token = this.route.snapshot.queryParamMap.get('token') ?? '';
    if (!this.token) {
      this.verification.set(false);
      this.erreurLien.set('Lien d\'activation incomplet : le jeton est absent.');
      return;
    }
    this.api.lireInvitation(this.token).subscribe({
      next: (info) => {
        this.email.set(info.email);
        this.role.set(info.role);
        if (info.nom) this.nom.set(info.nom);
        this.lienValide.set(true);
        this.verification.set(false);
      },
      error: (e) => {
        this.verification.set(false);
        this.erreurLien.set(e?.status === 410
          ? 'Ce lien d\'activation a expiré. Demandez à l\'administrateur de vous renvoyer une invitation.'
          : 'Ce lien d\'activation est invalide ou a déjà été utilisé.');
      }
    });
  }

  activer(): void {
    this.erreur.set('');
    if (!this.nom().trim()) {
      this.erreur.set('Veuillez saisir votre nom complet.');
      return;
    }
    if (this.motDePasse().length < 6) {
      this.erreur.set('Le mot de passe doit contenir au moins 6 caractères.');
      return;
    }
    if (this.motDePasse() !== this.confirmation()) {
      this.erreur.set('Les deux mots de passe ne correspondent pas.');
      return;
    }

    this.enregistrement.set(true);
    this.api.activerCompte({
      token: this.token,
      nom: this.nom().trim(),
      telephone: this.telephone().trim() || undefined,
      mot_de_passe: this.motDePasse()
    }).subscribe({
      next: () => {
        this.enregistrement.set(false);
        // Les profils terrain doivent se connecter depuis l'application mobile :
        // on ne les fait pas entrer dans le tableau de bord, on les renvoie vers
        // l'ecran de connexion avec un message clair.
        if (this.destinationMobile) {
          this.router.navigate(['/login'], {
            queryParams: { active: 'mobile' }
          });
          return;
        }
        // Profils bureau : on les connecte directement au tableau de bord.
        this.auth.login(this.email(), this.motDePasse()).subscribe({
          next: () => this.router.navigate(['/dashboard']),
          error: () => this.router.navigate(['/login'], { queryParams: { active: '1' } })
        });
      },
      error: (e) => {
        this.enregistrement.set(false);
        this.erreur.set(e?.error?.detail ?? 'Échec de l\'activation du compte.');
      }
    });
  }
}
