import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ToastService } from '../../core/toast.service';
import { NonConformite, Signalement } from '../../core/models';
import { environment } from '../../../environments/environment';
import { LucideAngularModule, ArrowLeft, MapPin, User, Calendar, Clock, CheckCircle, X, AlertTriangle, Building2, AlignLeft, Cpu, Image, Wrench, Info, Navigation, Smartphone } from 'lucide-angular';

@Component({
  selector: 'app-signalement-detail',
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './signalement-detail.html',
  styleUrl: './signalement-detail.scss'
})
export class SignalementDetail implements OnInit {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private toast = inject(ToastService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  readonly ArrowLeft = ArrowLeft;
  readonly MapPin = MapPin;
  readonly User = User;
  readonly Calendar = Calendar;
  readonly Clock = Clock;
  readonly CheckCircle = CheckCircle;
  readonly X = X;
  readonly AlertTriangle = AlertTriangle;
  readonly Building2 = Building2;
  readonly AlignLeft = AlignLeft;
  readonly Cpu = Cpu;
  readonly Image = Image;
  readonly Wrench = Wrench;
  readonly Info = Info;
  readonly Navigation = Navigation;
  readonly Smartphone = Smartphone;

  signalement = signal<Signalement | null>(null);
  loading = signal(true);
  updating = signal(false);

  // Prise en charge : la simple bascule de statut ne disait rien de ce qui
  // allait etre fait ni pour quand. Ces deux formulaires courts capturent
  // la meme information que le backend sait deja enregistrer (description
  // et echeance de l'action, motif du retour), jusqu'ici jamais demandee
  // par cet ecran.
  showActionForm = signal(false);
  actionDescription = signal('');
  actionEcheance = signal('');
  showRejetForm = signal(false);
  rejetMotif = signal('');

  // Non-conformites (BF-09). L'ecart constate lors du controle
  // contradictoire ne se confond pas avec l'action corrective : l'action
  // dit ce qu'il faut faire, l'ecart dit ce qui n'est pas conforme. Le
  // serveur les enregistrait sans qu'aucun ecran ne les demande, et la
  // table restait vide.
  nonConformites = signal<NonConformite[]>([]);
  showEcartForm = signal(false);
  ecartDescription = signal('');
  ecartSeverite = signal('MOYENNE');

  /** Les ecarts encore ouverts, ceux qui interdisent la cloture. */
  get ecartsOuverts(): number {
    return this.nonConformites().filter(e => !e.resolue).length;
  }

  get canUpdate(): boolean {
    // Le traitement d'un signalement revient au specialiste du suivi et a
    // l'expert HSE. Le responsable environnement, lui, saisit depuis le
    // terrain : l'ecran lui montrait des commandes que le serveur refuse,
    // et il butait sur une erreur sans comprendre pourquoi.
    return this.auth.hasRole('SPEC_ENV', 'EXPERT_HSE');
  }

  get isAdmin(): boolean {
    return this.auth.user()?.role === 'ADMIN';
  }

  /**
   * Une action corrective a-t-elle ete menee sur ce signalement ?
   *
   * Le motif d'un rejet est lui aussi consigne comme action : il retrace
   * une decision, non un traitement, et n'autorise donc pas la cloture.
   */
  get aUneActionCorrective(): boolean {
    return (this.signalement()?.actions ?? [])
      .some(a => !a.description?.startsWith('Signalement retourné à l\'agent.'));
  }

  get gpsUrl(): string {
    const s = this.signalement();
    if (!s?.geom?.coordinates) return '';
    const [lon, lat] = s.geom.coordinates;
    return `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=16/${lat}/${lon}`;
  }

  /**
   * D'ou vient la position : du capteur, ou de la main de l'agent ?
   *
   * Le champ brut vaut AUTO ou MANUEL, ce qui ne dit rien a qui ne
   * connait pas le modele. La distinction compte pourtant : une
   * position relevee par le capteur atteste que l'agent etait sur
   * place, une position saisie a la main n'atteste rien de tel. Le
   * memoire prevoit ce second cas a la figure 4.4, le GPS n'etant pas
   * garanti sous un ouvrage ; encore faut-il que le specialiste le
   * voie, sans quoi il apprecie deux constats de meme valeur alors
   * qu'ils n'en ont pas.
   */
  get positionRelevee(): boolean {
    return (this.signalement()?.gps_source ?? 'AUTO')
      .toUpperCase() !== 'MANUEL';
  }

  get libelleSourceGps(): string {
    return this.positionRelevee
      ? 'Position relevée par le capteur'
      : 'Position saisie par l\'agent';
  }

  ngOnInit() {
    const id = +this.route.snapshot.paramMap.get('id')!;
    this.api.getSignalement(id).subscribe({
      next: (data) => { this.signalement.set(data); this.loading.set(false); },
      error: () => this.loading.set(false)
    });
    this.chargerEcarts(id);
  }

  private chargerEcarts(id: number) {
    this.api.getNonConformitesDuSignalement(id).subscribe({
      next: (liste) => this.nonConformites.set(liste),
      error: () => this.nonConformites.set([]),
    });
  }

  /** Consigne un ecart releve lors du controle contradictoire. */
  validerEcart() {
    const s = this.signalement();
    if (!s || !this.ecartDescription().trim()) {
      this.toast.error('Décrivez l\'écart constaté avant de valider.');
      return;
    }
    this.updating.set(true);
    this.api.ajouterNonConformite(
      s.id, this.ecartDescription().trim(), this.ecartSeverite()).subscribe({
      next: () => {
        this.chargerEcarts(s.id);
        // Un écart ouvre le traitement côté serveur : l'écran doit
        // refléter le nouveau statut sans attendre un rechargement.
        this.api.getSignalement(s.id).subscribe({
          next: (maj) => this.signalement.set(maj),
        });
        this.updating.set(false);
        this.showEcartForm.set(false);
        this.ecartDescription.set('');
        this.ecartSeverite.set('MOYENNE');
        this.toast.success('Non-conformité consignée.');
      },
      error: (err) => {
        this.updating.set(false);
        this.toast.error(err?.error?.detail
          || 'Échec de l\'enregistrement de la non-conformité');
      }
    });
  }

  /** Leve un ecart, la mise en conformite ayant ete constatee. */
  leverEcart(ecart: NonConformite) {
    const s = this.signalement();
    if (!s) return;
    this.updating.set(true);
    this.api.resoudreNonConformite(ecart.id).subscribe({
      next: () => {
        this.chargerEcarts(s.id);
        this.updating.set(false);
        this.toast.success('Écart levé.');
      },
      error: (err) => {
        this.updating.set(false);
        this.toast.error(err?.error?.detail || 'Échec de la levée de l\'écart');
      }
    });
  }

  couleurSeverite(severite: string): string {
    if (severite === 'ELEVEE') return '#DC2626';
    if (severite === 'FAIBLE') return '#71717A';
    return '#F37021';
  }

  updateStatut(statut: string) {
    const s = this.signalement();
    if (!s) return;
    this.updating.set(true);
    this.api.updateSignalementStatut(s.id, statut).subscribe({
      next: (updated) => {
        this.signalement.set(updated);
        this.updating.set(false);
        const labels: Record<string, string> = {
          'EN_TRAITEMENT': 'Signalement pris en charge',
          'CLOTURE': 'Signalement résolu avec succès',
          'REJETE': 'Signalement rejeté'
        };
        this.toast.success(labels[statut] ?? 'Statut mis à jour');
      },
      error: (err) => {
        this.updating.set(false);
        // Le refus du serveur porte son motif : le relayer evite a
        // l'utilisateur de chercher pourquoi son action n'aboutit pas.
        this.toast.error(err?.error?.detail || 'Échec de la mise à jour du statut');
      }
    });
  }

  validerPriseEnCharge() {
    const s = this.signalement();
    if (!s || !this.actionDescription().trim()) {
      this.toast.error('Décrivez l\'action corrective avant de valider.');
      return;
    }
    this.updating.set(true);
    const echeance = this.actionEcheance() ? new Date(this.actionEcheance()).toISOString() : null;
    this.api.ajouterActionCorrective(s.id, this.actionDescription().trim(), echeance).subscribe({
      next: () => {
        this.api.getSignalement(s.id).subscribe({
          next: (updated) => {
            this.signalement.set(updated);
            this.updating.set(false);
            this.showActionForm.set(false);
            this.actionDescription.set('');
            this.actionEcheance.set('');
            this.toast.success('Action corrective enregistrée, signalement pris en charge.');
          },
          error: () => this.updating.set(false)
        });
      },
      error: () => {
        this.updating.set(false);
        this.toast.error('Échec de l\'enregistrement de l\'action corrective');
      }
    });
  }

  validerRejet() {
    const s = this.signalement();
    if (!s || !this.rejetMotif().trim()) {
      this.toast.error('Indiquez le motif du rejet avant de valider.');
      return;
    }
    this.updating.set(true);
    this.api.retournerAgent(s.id, this.rejetMotif().trim()).subscribe({
      next: (updated) => {
        this.signalement.set(updated);
        this.updating.set(false);
        this.showRejetForm.set(false);
        this.rejetMotif.set('');
        this.toast.success('Signalement rejeté, motif enregistré.');
      },
      error: () => {
        this.updating.set(false);
        this.toast.error('Échec du rejet du signalement');
      }
    });
  }

  goBack() {
    this.router.navigate(['/signalements']);
  }

  getPhotoUrl(chemin: string): string {
    // Photo Supabase Storage : le backend a deja stocke l'URL absolue.
    if (chemin.startsWith('http')) return chemin;
    // Photo servie par le backend (stockage local en dev).
    return `${environment.apiUrl}/uploads/photos/${chemin}`;
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  get statutColor(): string {
    const s = this.signalement();
    if (!s) return '#757575';
    const colors: Record<string, string> = {
      'NOUVEAU': '#F37021', 'EN_TRAITEMENT': '#1565C0', 'CLOTURE': '#16A34A', 'REJETE': '#D32F2F', 'PENDING_SYNC': '#757575'
    };
    return colors[s.statut] ?? '#757575';
  }

  get criticiteColor(): string {
    const s = this.signalement();
    if (!s) return '#757575';
    const colors: Record<string, string> = { 'FAIBLE': '#16A34A', 'MODERE': '#F37021', 'ELEVE': '#D32F2F' };
    return colors[s.criticite] ?? '#757575';
  }
}
