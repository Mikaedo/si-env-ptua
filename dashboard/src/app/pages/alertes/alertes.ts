import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ToastService } from '../../core/toast.service';
import { Alerte } from '../../core/models';
import { LucideAngularModule, Bell, AlertTriangle, CheckCircle, Info, X, MapPin, Clock, Activity } from 'lucide-angular';

@Component({
  selector: 'app-alertes',
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './alertes.html',
  styleUrl: './alertes.scss'
})
export class Alertes implements OnInit {
  private api = inject(ApiService);
  public auth = inject(AuthService);
  private toast = inject(ToastService);
  isAdmin = () => this.auth.user()?.role === 'ADMIN';

  readonly Bell = Bell;
  readonly AlertTriangle = AlertTriangle;
  readonly CheckCircle = CheckCircle;
  readonly Info = Info;
  readonly X = X;
  readonly MapPin = MapPin;
  readonly Clock = Clock;
  readonly Activity = Activity;

  alertes = signal<Alerte[]>([]);
  loading = signal(true);
  error = signal('');
  selectedAlerte = signal<Alerte | null>(null);

  get canAcknowledge(): boolean {
    // La matrice des habilitations ouvre « Réception et revue des
    // alertes » à tous les profils opérationnels : accuser réception
    // retire l'alerte du compteur des non lues, c'est un geste de
    // lecture. Seuls l'agence de tutelle et le bailleur en sont exclus,
    // n'ayant sur ce domaine qu'un droit de consultation.
    return this.auth.hasRole('SPEC_ENV', 'SPEC_PAR', 'RESP_ENV',
                             'EXPERT_HSE', 'ADMIN');
  }

  ngOnInit() {
    this.api.getAlertes().subscribe({
      next: (data) => { this.alertes.set(data); this.loading.set(false); },
      error: () => { this.loading.set(false); this.error.set('Impossible de charger les alertes pour ce profil.'); }
    });
  }

  openDetail(a: Alerte) {
    this.selectedAlerte.set(a);
  }

  closeDetail() {
    this.selectedAlerte.set(null);
  }

  acknowledge(id: number) {
    this.api.acknowledgeAlerte(id).subscribe({
      next: (updated) => {
        this.alertes.update(list => list.map(a => a.id === id ? updated : a));
        if (this.selectedAlerte()?.id === id) this.selectedAlerte.set(updated);
        this.toast.success('Prise de connaissance enregistrée à votre nom');
      },
      error: () => {
        this.error.set('La réception de l\'alerte n\'a pas pu être enregistrée.');
        this.toast.error('Échec de l\'accusé de réception');
      }
    });
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  get niveauConfig(): Record<string, { bg: string; color: string; icon: any }> {
    return {
      'CRITIQUE': { bg: '#FFEBEE', color: '#C62828', icon: AlertTriangle },
      'WARNING':  { bg: '#FEF3E8', color: '#F37021', icon: AlertTriangle },
      'INFO':     { bg: '#E3F2FD', color: '#1565C0', icon: Info },
    };
  }

  get niveauLabels(): Record<string, string> {
    return {
      'CRITIQUE': '🔴 Critique',
      'WARNING':  '🟠 Avertissement',
      'INFO':     '🔵 Information',
    };
  }

  get critiqueCount() { return this.alertes().filter(a => a.niveau === 'CRITIQUE').length; }
  get warningCount()  { return this.alertes().filter(a => a.niveau === 'WARNING').length; }
  get infoCount()     { return this.alertes().filter(a => a.niveau === 'INFO').length; }
}
