import { Component, signal, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Subscription, timer } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { Signalement, Alerte, Plainte, Chantier } from '../../core/models';
import { LucideAngularModule, BarChart2, Clock, CheckCircle, AlertTriangle, Bell,
  ShieldAlert, FileText, ChevronRight, MapPin, Building2, User, Phone,
  Eye, Users, Activity, TrendingUp, X, Filter, Calendar } from 'lucide-angular';
import { CustomSelect } from '../../shared/custom-select';

type Tab = 'overview' | 'signalements' | 'plaintes' | 'alertes';

@Component({
  selector: 'app-admin-dashboard',
  imports: [CommonModule, LucideAngularModule, CustomSelect],
  templateUrl: './admin-dashboard.html',
  styleUrl: './admin-dashboard.scss'
})
export class AdminDashboard implements OnInit, OnDestroy {
  private api = inject(ApiService);
  public auth = inject(AuthService);
  private router = inject(Router);

  readonly BarChart2 = BarChart2;
  readonly Clock = Clock;
  readonly CheckCircle = CheckCircle;
  readonly AlertTriangle = AlertTriangle;
  readonly Bell = Bell;
  readonly ShieldAlert = ShieldAlert;
  readonly FileText = FileText;
  readonly ChevronRight = ChevronRight;
  readonly MapPin = MapPin;
  readonly Building2 = Building2;
  readonly User = User;
  readonly Phone = Phone;
  readonly Eye = Eye;
  readonly Users = Users;
  readonly Activity = Activity;
  readonly TrendingUp = TrendingUp;
  readonly X = X;
  readonly Filter = Filter;
  readonly Calendar = Calendar;

  activeTab = signal<Tab>('overview');
  signalements = signal<Signalement[]>([]);
  alertes = signal<Alerte[]>([]);
  plaintes = signal<Plainte[]>([]);
  chantiers = signal<Chantier[]>([]);
  loading = signal(true);

  filterChantier = signal('');
  filterStatut = signal('');
  searchTerm = signal('');

  selectedSignalement = signal<Signalement | null>(null);
  selectedPlainte = signal<Plainte | null>(null);
  selectedAlerte = signal<Alerte | null>(null);

  private sub?: Subscription;

  ngOnInit() {
    this.loadData();
    this.sub = timer(0, 15000).subscribe(() => this.loadData());
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }

  private loadData() {
    this.api.getSignalements().subscribe({ next: d => this.signalements.set(d), error: () => {} });
    this.api.getAlertes().subscribe({ next: d => this.alertes.set(d), error: () => {} });
    this.api.getPlaintes().subscribe({ next: d => { this.plaintes.set(d); this.loading.set(false); }, error: () => this.loading.set(false) });
    this.api.getChantiers().subscribe({ next: d => this.chantiers.set(d), error: () => {} });
  }

  setTab(tab: Tab) {
    this.activeTab.set(tab);
    this.searchTerm.set('');
    this.filterStatut.set('');
  }

  get filteredSignalements(): Signalement[] {
    const term = this.searchTerm().toLowerCase();
    const statut = this.filterStatut();
    const chantier = this.filterChantier();
    return this.signalements().filter(s =>
      (!term || s.type_nuisance?.toLowerCase().includes(term) || s.description?.toLowerCase().includes(term)) &&
      (!statut || s.statut === statut) &&
      (!chantier || String(s.chantier?.id) === chantier)
    );
  }

  get filteredPlaintes(): Plainte[] {
    const term = this.searchTerm().toLowerCase();
    const statut = this.filterStatut();
    return this.plaintes().filter(p =>
      (!term || p.nom_plaignant?.toLowerCase().includes(term) || p.description?.toLowerCase().includes(term)) &&
      (!statut || p.statut === statut)
    );
  }

  get filteredAlertes(): Alerte[] {
    const chantier = this.filterChantier();
    return this.alertes().filter(a =>
      (!chantier || String(a.chantier?.id) === chantier)
    );
  }

  get sigStats() {
    const all = this.signalements();
    const actifs = all.filter(s => s.statut !== 'REJETE').length;
    return [
      { label: 'Total', count: all.length, color: '#004F9F', icon: 'bar', pct: 100 },
      { label: 'Nouveaux', count: all.filter(s => s.statut === 'NOUVEAU').length, color: '#F37021', icon: 'clock', pct: actifs ? all.filter(s => s.statut === 'NOUVEAU').length / actifs * 100 : 0 },
      { label: 'En cours', count: all.filter(s => s.statut === 'EN_TRAITEMENT').length, color: '#1565C0', icon: 'alert', pct: actifs ? all.filter(s => s.statut === 'EN_TRAITEMENT').length / actifs * 100 : 0 },
      { label: 'Résolus', count: all.filter(s => s.statut === 'CLOTURE').length, color: '#16A34A', icon: 'check', pct: actifs ? all.filter(s => s.statut === 'CLOTURE').length / actifs * 100 : 0 },
    ];
  }

  get plainteStats() {
    const all = this.plaintes();
    return [
      { label: 'Total', count: all.length, color: '#004F9F', icon: 'bar', pct: 100 },
      { label: 'Ouvertes', count: all.filter(p => p.statut === 'OUVERTE').length, color: '#F37021', icon: 'clock', pct: all.length ? all.filter(p => p.statut === 'OUVERTE').length / all.length * 100 : 0 },
      { label: 'En cours', count: all.filter(p => p.statut === 'EN_COURS').length, color: '#1565C0', icon: 'alert', pct: all.length ? all.filter(p => p.statut === 'EN_COURS').length / all.length * 100 : 0 },
      { label: 'Résolues', count: all.filter(p => p.statut === 'RESOLU').length, color: '#16A34A', icon: 'check', pct: all.length ? all.filter(p => p.statut === 'RESOLU').length / all.length * 100 : 0 },
    ];
  }

  get alerteStats() {
    const all = this.alertes();
    return [
      { label: 'Total', count: all.length, color: '#004F9F', icon: 'bar', pct: 100 },
      { label: 'Critiques', count: all.filter(a => a.niveau === 'CRITIQUE').length, color: '#C62828', icon: 'alert', pct: all.length ? all.filter(a => a.niveau === 'CRITIQUE').length / all.length * 100 : 0 },
      { label: 'Warnings', count: all.filter(a => a.niveau === 'WARNING').length, color: '#F37021', icon: 'clock', pct: all.length ? all.filter(a => a.niveau === 'WARNING').length / all.length * 100 : 0 },
      { label: 'Non lues', count: all.filter(a => !a.recue).length, color: '#1565C0', icon: 'check', pct: all.length ? all.filter(a => !a.recue).length / all.length * 100 : 0 },
    ];
  }

  get chantierOptions() {
    return [
      { value: '', label: 'Tous les chantiers' },
      ...this.chantiers().map(c => ({ value: String(c.id), label: c.nom }))
    ];
  }

  get statutOptions() {
    return [
      { value: '', label: 'Tous les statuts' },
      { value: 'NOUVEAU', label: 'Nouveau' },
      { value: 'EN_TRAITEMENT', label: 'En cours' },
      { value: 'CLOTURE', label: 'Résolu' },
      { value: 'REJETE', label: 'Rejeté' }
    ];
  }

  get plainteStatutOptions() {
    return [
      { value: '', label: 'Tous les statuts' },
      { value: 'OUVERTE', label: 'Ouvertes' },
      { value: 'EN_COURS', label: 'En cours' },
      { value: 'RESOLU', label: 'Résolues' },
      { value: 'REJETE', label: 'Rejetées' }
    ];
  }

  openSignalement(s: Signalement) { this.selectedSignalement.set(s); }
  closeSignalement() { this.selectedSignalement.set(null); }
  openPlainte(p: Plainte) { this.selectedPlainte.set(p); }
  closePlainte() { this.selectedPlainte.set(null); }
  openAlerte(a: Alerte) { this.selectedAlerte.set(a); }
  closeAlerte() { this.selectedAlerte.set(null); }

  goToAdmin() {
    this.router.navigate(['/admin']);
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  formatDateTime(date: string): string {
    return new Date(date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
  }

  get statutColors(): Record<string, string> {
    return {
      'NOUVEAU': '#F37021',
      'EN_TRAITEMENT': '#1565C0',
      'CLOTURE': '#16A34A',
      'REJETE': '#D32F2F',
      'OUVERTE': '#F37021',
      'EN_COURS': '#1565C0',
      'RESOLU': '#16A34A',
    };
  }

  get niveauColors(): Record<string, string> {
    return {
      'CRITIQUE': '#C62828',
      'WARNING': '#F37021',
      'INFO': '#1565C0',
    };
  }

  get selectedChantierNom(): string {
    const s = this.selectedSignalement();
    if (s?.chantier) return s.chantier.nom;
    if (s?.chantier_id) {
      const c = this.chantiers().find(c => c.id === s.chantier_id);
      return c?.nom ?? `Chantier #${s.chantier_id}`;
    }
    return 'Non spécifié';
  }

  get selectedPlainteChantierNom(): string {
    const p = this.selectedPlainte();
    if (!p?.chantier_id) return 'Non spécifié';
    const c = this.chantiers().find(c => c.id === p.chantier_id);
    return c?.nom ?? `Chantier #${p.chantier_id}`;
  }
}
