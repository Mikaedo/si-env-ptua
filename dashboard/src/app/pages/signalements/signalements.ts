import { Component, signal, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription, timer } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { Signalement, Chantier } from '../../core/models';
import { LucideAngularModule, Search, Filter, MapPin, ChevronRight, FileSearch, BarChart2, Clock, CheckCircle, AlertTriangle } from 'lucide-angular';
import { CustomSelect } from '../../shared/custom-select';

@Component({
  selector: 'app-signalements',
  imports: [CommonModule, LucideAngularModule, CustomSelect],
  templateUrl: './signalements.html',
  styleUrl: './signalements.scss'
})
export class Signalements implements OnInit, OnDestroy {
  private api = inject(ApiService);
  public auth = inject(AuthService);
  isAdmin = () => this.auth.user()?.role === 'ADMIN';
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  readonly Search = Search;
  readonly Filter = Filter;
  readonly MapPin = MapPin;
  readonly ChevronRight = ChevronRight;
  readonly FileSearch = FileSearch;
  readonly BarChart2 = BarChart2;
  readonly Clock = Clock;
  readonly CheckCircle = CheckCircle;
  readonly AlertTriangle = AlertTriangle;

  allSignalements = signal<Signalement[]>([]);
  chantiers = signal<Chantier[]>([]);
  loading = signal(true);

  searchTerm = signal('');
  filterStatut = signal('');
  filterCriticite = signal('');
  filterChantier = signal('');

  private refreshSub?: Subscription;

  ngOnInit() {
    // Une alerte de la cloche mène ici en désignant son chantier :
    // sans cette lecture, le clic ouvrait la liste complète et le
    // spécialiste devait retrouver lui-même le chantier concerné.
    const chantier = this.route.snapshot.queryParamMap.get('chantier');
    if (chantier) this.filterChantier.set(chantier);

    this.loadData();
    this.refreshSub = timer(10000, 10000).subscribe(() => this.loadData());
  }

  private loadData() {
    this.api.getSignalements().subscribe({
      next: (data) => { this.allSignalements.set(data); this.loading.set(false); },
      error: () => this.loading.set(false)
    });
    this.api.getChantiers().subscribe({
      next: (data) => this.chantiers.set(data),
      error: () => {}
    });
  }

  ngOnDestroy() {
    if (this.refreshSub) {
      this.refreshSub.unsubscribe();
    }
  }

  get filteredSignalements(): Signalement[] {
    return this.allSignalements().filter(s => {
      if (this.searchTerm() && !s.type_nuisance.toLowerCase().includes(this.searchTerm().toLowerCase()) &&
          !(s.description ?? '').toLowerCase().includes(this.searchTerm().toLowerCase()) &&
          !(s.chantier?.nom ?? '').toLowerCase().includes(this.searchTerm().toLowerCase())) return false;
      if (this.filterStatut() && s.statut !== this.filterStatut()) return false;
      if (this.filterCriticite() && s.criticite !== this.filterCriticite()) return false;
      if (this.filterChantier() && s.chantier?.id !== +this.filterChantier()) return false;
      return true;
    });
  }

  goToDetail(id: number) {
    this.router.navigate(['/signalements', id]);
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  get statutColors(): Record<string, string> {
    return {
      'NOUVEAU': '#F37021',
      'EN_TRAITEMENT': '#1565C0',
      'CLOTURE': '#16A34A',
      'REJETE': '#D32F2F',
      'PENDING_SYNC': '#757575',
    };
  }

  get criticiteColors(): Record<string, string> {
    return { 'FAIBLE': '#16A34A', 'MODERE': '#F37021', 'ELEVE': '#D32F2F' };
  }

  get statutLabels(): Record<string, string> {
    return {
      'NOUVEAU': 'Nouveau',
      'EN_TRAITEMENT': 'En cours',
      'CLOTURE': 'Clôturé',
      'REJETE': 'Rejeté',
      'PENDING_SYNC': 'Sync.',
    };
  }

  get quickStats() {
    const all = this.allSignalements();
    return [
      { label: 'Total', count: all.length, color: '#004F9F', icon: 'bar', pct: 100 },
      { label: 'Nouveaux', count: all.filter(s => s.statut === 'NOUVEAU').length, color: '#F37021', icon: 'clock', pct: all.length ? (all.filter(s => s.statut === 'NOUVEAU').length / all.length * 100) : 0 },
      { label: 'En cours', count: all.filter(s => s.statut === 'EN_TRAITEMENT').length, color: '#1565C0', icon: 'alert', pct: all.length ? (all.filter(s => s.statut === 'EN_TRAITEMENT').length / all.length * 100) : 0 },
      { label: 'Résolus', count: all.filter(s => s.statut === 'CLOTURE').length, color: '#16A34A', icon: 'check', pct: all.length ? (all.filter(s => s.statut === 'CLOTURE').length / all.length * 100) : 0 },
    ];
  }

  get statutOptions() {
    return [
      { value: '', label: 'Tous statuts' },
      { value: 'NOUVEAU', label: 'Nouveau' },
      { value: 'EN_TRAITEMENT', label: 'En cours' },
      { value: 'CLOTURE', label: 'Résolu' },
      { value: 'REJETE', label: 'Rejeté' }
    ];
  }

  get criticiteOptions() {
    return [
      { value: '', label: 'Toutes criticités' },
      { value: 'FAIBLE', label: 'Faible' },
      { value: 'MODERE', label: 'Modéré' },
      { value: 'ELEVE', label: 'Élevé' }
    ];
  }

  get chantierOptions() {
    return [
      { value: '', label: 'Tous chantiers' },
      ...this.chantiers().map(c => ({ value: String(c.id), label: c.nom }))
    ];
  }
}
