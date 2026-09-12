import { Component, signal, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription, timer } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { Signalement, Chantier } from '../../core/models';
import { LucideAngularModule, Search, Filter, MapPin, ChevronRight, FileSearch, BarChart2, Clock, CheckCircle, AlertTriangle } from 'lucide-angular';
import { CustomSelect } from '../../shared/custom-select';
import { BandeauMandat } from '../../shared/bandeau-mandat';

@Component({
  selector: 'app-signalements',
  imports: [CommonModule, LucideAngularModule, CustomSelect, BandeauMandat],
  templateUrl: './signalements.html',
  styleUrl: './signalements.scss'
})
export class Signalements implements OnInit, OnDestroy {
  private api = inject(ApiService);
  public auth = inject(AuthService);
  isAdmin = () => this.auth.user()?.role === 'ADMIN';

  /** L'angle sous lequel chaque organisme lit les constats.
   *
   * L'agence de tutelle regarde leur traitement au regard du Plan de
   * Gestion ; le bailleur regarde en outre ceux qui touchent la sante
   * ou les biens des riverains, qui relevent de sa sauvegarde sociale.
   */
  proposSignalements = () => {
    const role = this.auth.user()?.role;
    if (role === 'ANDE') {
      return 'Constats de terrain et suites données, au regard du Plan '
           + 'de Gestion Environnementale et Sociale';
    }
    if (role === 'BAD') {
      return 'Constats de terrain, avec une attention aux nuisances '
           + 'affectant la santé ou les biens des riverains';
    }
    return '';
  };
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

  /**
   * La date du constat sur le terrain, non celle de sa reception.
   *
   * Le tableau affichait l'heure a laquelle le serveur avait recu le
   * signalement. Hors couverture, les deux sont separees de plusieurs
   * heures : un constat releve a 7h et transmis a 18h se rangeait apres
   * un constat releve a 8h par un agent couvert, et la liste inversait
   * ainsi l'ordre des faits.
   */
  dateConstat(s: Signalement): string {
    return this.formatDate(s.saisi_le || s.cree_le);
  }

  /**
   * Le constat a-t-il ete transmis bien apres avoir ete releve ?
   *
   * L'ecart n'est pas un defaut, c'est le mode hors ligne qui
   * fonctionne. Mais le specialiste doit le savoir : un constat qui
   * arrive avec un jour de retard n'appelle pas la meme lecture qu'un
   * constat remonte dans l'heure.
   */
  transmissionDifferee(s: Signalement): boolean {
    if (!s.saisi_le) return false;
    const ecart = new Date(s.cree_le).getTime()
      - new Date(s.saisi_le).getTime();
    return ecart > 2 * 60 * 60 * 1000;
  }

  /** Depuis combien de temps le constat attendait avant d'arriver. */
  delaiTransmission(s: Signalement): string {
    if (!s.saisi_le) return '';
    const heures = Math.round(
      (new Date(s.cree_le).getTime() - new Date(s.saisi_le).getTime())
      / 3600000);
    if (heures < 24) return `transmis ${heures} h après`;
    const jours = Math.round(heures / 24);
    return `transmis ${jours} jour${jours > 1 ? 's' : ''} après`;
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
