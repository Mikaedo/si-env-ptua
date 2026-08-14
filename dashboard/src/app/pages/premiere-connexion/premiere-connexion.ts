import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { LucideAngularModule, Eye, EyeOff, AlertCircle, Mail, Lock, User, Phone, ArrowRight, CheckCircle2 } from 'lucide-angular';

/**
 * Page de premiere connexion, atteinte depuis le lien du courriel de bienvenue.
 *
 * Elle repond a un defaut precis : le courriel pointait auparavant vers la
 * racine du tableau de bord. Quand le navigateur portait deja une session
 * ouverte, le garde d'authentification la laissait passer et l'utilisateur
 * atterrissait sur le tableau de bord de cette session, pas sur son propre
 * parcours d'activation. La page ci-dessous ferme donc systematiquement toute
 * session en cours avant d'afficher quoi que ce soit.
 *
 * Le parcours se deroule en deux etapes. La premiere echange l'adresse contre
 * un jeton : le serveur l'accorde sans verifier de mot de passe tant que le
 * compte n'en possede pas. La seconde recueille le nom, le telephone et le
 * mot de passe choisi.
 */
@Component({
  selector: 'app-premiere-connexion',
  imports: [CommonModule, LucideAngularModule, FormsModule],
  templateUrl: './premiere-connexion.html',
  styleUrl: './premiere-connexion.scss'
})
export class PremiereConnexion implements OnInit {
  private auth = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  readonly Eye = Eye;
  readonly EyeOff = EyeOff;
  readonly AlertCircle = AlertCircle;
  readonly Mail = Mail;
  readonly Lock = Lock;
  readonly User = User;
  readonly Phone = Phone;
  readonly ArrowRight = ArrowRight;
  readonly CheckCircle2 = CheckCircle2;

  etape = signal<0 | 1 | 2>(0);
  email = signal('');
  nom = signal('');
  telephone = signal('');
  motDePasse = signal('');
  confirmation = signal('');
  afficherMotDePasse = signal(false);
  chargement = signal(false);
  erreur = signal('');

  ngOnInit(): void {
    // Toute session existante est fermee : c'est la correction du defaut
    // decrit en tete de fichier.
    this.auth.logout();

    const email = this.route.snapshot.queryParamMap.get('email');
    if (email) {
      this.email.set(email);
    }
  }

  verifierAdresse(): void {
    if (!this.email().trim()) {
      this.erreur.set('Veuillez saisir votre adresse e-mail.');
      return;
    }
    this.chargement.set(true);
    this.erreur.set('');

    // Le mot de passe transmis ici n'a aucune importance : le serveur ne le
    // consulte pas tant que le compte n'a pas de mot de passe enregistre.
    this.auth.login(this.email().trim(), 'premiere-connexion').subscribe({
      next: (res) => {
        this.chargement.set(false);
        if (!res.premiere_connexion) {
          this.auth.logout();
          this.erreur.set('Ce compte est deja actif. Utilisez la page de connexion habituelle.');
          return;
        }
        this.etape.set(1);
      },
      error: () => {
        this.chargement.set(false);
        this.erreur.set('Aucun compte ne correspond a cette adresse.');
      }
    });
  }

  activerCompte(): void {
    if (!this.nom().trim()) {
      this.erreur.set('Veuillez saisir votre nom complet.');
      return;
    }
    if (this.motDePasse().length < 8) {
      this.erreur.set('Le mot de passe doit compter au moins 8 caracteres.');
      return;
    }
    if (this.motDePasse() !== this.confirmation()) {
      this.erreur.set('Les deux mots de passe ne correspondent pas.');
      return;
    }

    this.chargement.set(true);
    this.erreur.set('');

    this.auth.firstLogin(this.nom().trim(), this.telephone().trim(), this.motDePasse()).subscribe({
      next: () => {
        this.chargement.set(false);
        this.etape.set(2);
        setTimeout(() => this.router.navigate(['/login']), 2600);
      },
      error: () => {
        this.chargement.set(false);
        this.erreur.set('L\'activation a echoue. Reessayez dans un instant.');
      }
    });
  }

  retourConnexion(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
