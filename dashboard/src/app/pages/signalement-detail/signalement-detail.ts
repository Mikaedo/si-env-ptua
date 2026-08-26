import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ToastService } from '../../core/toast.service';
import { Signalement } from '../../core/models';
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

  get canUpdate(): boolean {
    return this.auth.hasRole('SPEC_ENV', 'EXPERT_HSE', 'RESP_ENV');
  }

  get isAdmin(): boolean {
    return this.auth.user()?.role === 'ADMIN';
  }

  get gpsUrl(): string {
    const s = this.signalement();
    if (!s?.geom?.coordinates) return '';
    const [lon, lat] = s.geom.coordinates;
    return `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=16/${lat}/${lon}`;
  }

  ngOnInit() {
    const id = +this.route.snapshot.paramMap.get('id')!;
    this.api.getSignalement(id).subscribe({
      next: (data) => { this.signalement.set(data); this.loading.set(false); },
      error: () => this.loading.set(false)
    });
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
      error: () => {
        this.updating.set(false);
        this.toast.error('Échec de la mise à jour du statut');
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
