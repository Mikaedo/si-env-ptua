import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ToastService } from '../../core/toast.service';
import { Plainte, Chantier } from '../../core/models';
import { LucideAngularModule, ShieldAlert, Search, MapPin, Plus, CheckCircle, X, Clock, User, Phone, Building2, AlertCircle, BarChart2, AlertTriangle, Smartphone } from 'lucide-angular';
import { CustomSelect } from '../../shared/custom-select';

@Component({
  selector: 'app-plaintes',
  imports: [CommonModule, LucideAngularModule, CustomSelect],
  templateUrl: './plaintes.html',
  styleUrl: './plaintes.scss'
})
export class Plaintes implements OnInit {
  private api = inject(ApiService);
  public auth = inject(AuthService);
  private toast = inject(ToastService);
  isAdmin = () => this.auth.user()?.role === 'ADMIN';
  get canManage(): boolean {
    return this.auth.hasRole('SPEC_PAR');
  }

  readonly ShieldAlert = ShieldAlert;
  readonly Search = Search;
  readonly MapPin = MapPin;
  readonly Plus = Plus;
  readonly CheckCircle = CheckCircle;
  readonly X = X;
  readonly Clock = Clock;
  readonly User = User;
  readonly Phone = Phone;
  readonly Smartphone = Smartphone;

  /**
   * Traduit la categorie declaree par le riverain.
   *
   * Le vocabulaire du depot est celui d'un habitant, non d'un technicien :
   * personne ne se plaint d'un depassement de seuil de particules, on se
   * plaint de poussiere. Le tableau de bord conserve ce vocabulaire plutot
   * que de le retraduire, pour que le specialiste lise ce que la personne
   * a effectivement voulu dire.
   */
  libelleCategorie(code: string): string {
    const libelles: Record<string, string> = {
      bruit: 'Bruit',
      poussiere: 'Poussière',
      circulation: 'Circulation',
      eau: 'Eau stagnante',
      dechets: 'Déchets',
      autre: 'Autre',
    };
    return libelles[code] ?? code;
  }
  readonly Building2 = Building2;
  readonly AlertCircle = AlertCircle;
  readonly BarChart2 = BarChart2;
  readonly AlertTriangle = AlertTriangle;

  plaintes = signal<Plainte[]>([]);
  chantiers = signal<Chantier[]>([]);
  loading = signal(true);
  saving = signal(false);
  error = signal('');
  searchTerm = signal('');
  filterStatut = signal('');
  selectedPlainte = signal<Plainte | null>(null);
  newNom = signal('');
  newContact = signal('');
  newDescription = signal('');
  newChantierId = signal('');

  // Meme trou que sur les signalements : passer « en cours » ne demandait
  // rien de plus qu'une valeur de liste deroulante. Ce formulaire capture
  // l'action engagee et son echeance avant de confirmer le passage en cours.
  showActionForm = signal(false);
  actionDescription = signal('');
  actionEcheance = signal('');
  ngOnInit() {
    this.api.getPlaintes().subscribe({
      next: (data) => { this.plaintes.set(data); this.loading.set(false); },
      error: () => { this.loading.set(false); this.error.set('Impossible de charger les plaintes pour ce profil.'); }
    });
    this.api.getChantiers().subscribe({ next: data => this.chantiers.set(data) });
  }

  createPlainte() {
    if (!this.newNom() || !this.newDescription()) {
      this.error.set('Le nom du plaignant et la description sont obligatoires.');
      return;
    }
    this.saving.set(true);
    this.error.set('');
    this.api.createPlainte({
      nom_plaignant: this.newNom(),
      contact: this.newContact() || undefined,
      description: this.newDescription(),
      chantier_id: this.newChantierId() ? Number(this.newChantierId()) : undefined
    }).subscribe({
      next: plainte => {
        this.plaintes.update(list => [plainte, ...list]);
        this.newNom.set(''); this.newContact.set(''); this.newDescription.set(''); this.newChantierId.set('');
        this.saving.set(false);
        this.toast.success('Plainte enregistrée avec succès');
      },
      error: () => { this.saving.set(false); this.error.set('La création de la plainte a échoué.'); this.toast.error('Échec de l\'enregistrement de la plainte'); }
    });
  }

  updateStatut(id: number, statut: string) {
    if (statut === 'EN_COURS') {
      const p = this.plaintes().find(x => x.id === id);
      if (p) this.selectedPlainte.set(p);
      this.showActionForm.set(true);
      return;
    }
    this.api.updatePlainteStatut(id, statut).subscribe({
      next: updated => {
        this.plaintes.update(list => list.map(plainte => plainte.id === id ? updated : plainte));
        if (this.selectedPlainte()?.id === id) this.selectedPlainte.set(updated);
        const labels: Record<string, string> = {
          'EN_COURS': 'Plainte prise en charge',
          'RESOLU': 'Plainte résolue avec succès',
          'REJETE': 'Plainte rejetée',
          'OUVERTE': 'Plainte rouverte'
        };
        this.toast.success(labels[statut] ?? 'Statut mis à jour');
      },
      error: () => { this.error.set('La mise à jour du statut a échoué.'); this.toast.error('Échec de la mise à jour du statut'); }
    });
  }

  openDetail(p: Plainte) {
    this.selectedPlainte.set(p);
  }

  closeDetail() {
    this.selectedPlainte.set(null);
    this.showActionForm.set(false);
    this.actionDescription.set('');
    this.actionEcheance.set('');
  }

  validerPriseEnCharge() {
    const p = this.selectedPlainte();
    if (!p || !this.actionDescription().trim()) {
      this.toast.error('Décrivez l\'action engagée avant de valider.');
      return;
    }
    const echeance = this.actionEcheance() ? new Date(this.actionEcheance()).toISOString() : null;
    this.api.ajouterActionPlainte(p.id, this.actionDescription().trim(), echeance).subscribe({
      next: () => {
        this.api.getPlaintes().subscribe({
          next: (data) => {
            this.plaintes.set(data);
            const misAJour = data.find(x => x.id === p.id) ?? null;
            this.selectedPlainte.set(misAJour);
            this.showActionForm.set(false);
            this.actionDescription.set('');
            this.actionEcheance.set('');
            this.toast.success('Action engagée, plainte prise en charge.');
          }
        });
      },
      error: () => this.toast.error('Échec de l\'enregistrement de l\'action')
    });
  }

  get chantierNom(): string {
    const p = this.selectedPlainte();
    if (!p?.chantier_id) return 'Non spécifié';
    const c = this.chantiers().find(c => c.id === p.chantier_id);
    return c?.nom ?? `Chantier #${p.chantier_id}`;
  }

  get filteredPlaintes(): Plainte[] {
    const term = this.searchTerm().toLowerCase();
    const statut = this.filterStatut();
    return this.plaintes().filter(p =>
      (!term || p.nom_plaignant?.toLowerCase().includes(term) ||
      p.description?.toLowerCase().includes(term) ||
      (p.contact ?? '').toLowerCase().includes(term)) &&
      (!statut || p.statut === statut)
    );
  }

  get ouvertesCount() { return this.plaintes().filter(p => p.statut === 'OUVERTE').length; }
  get enCoursCount() { return this.plaintes().filter(p => p.statut === 'EN_COURS').length; }
  get resoluesCount() { return this.plaintes().filter(p => p.statut === 'RESOLU').length; }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  get statutColors(): Record<string, string> {
    return {
      'OUVERTE': '#F37021',
      'EN_COURS': '#1565C0',
      'RESOLU': '#16A34A',
      'REJETE': '#D32F2F',
    };
  }

  get quickStats() {
    const all = this.plaintes();
    return [
      { label: 'Total', count: all.length, color: '#004F9F', icon: 'bar', pct: 100 },
      { label: 'Ouvertes', count: this.ouvertesCount, color: '#F37021', icon: 'clock', pct: all.length ? (this.ouvertesCount / all.length * 100) : 0 },
      { label: 'En cours', count: this.enCoursCount, color: '#1565C0', icon: 'alert', pct: all.length ? (this.enCoursCount / all.length * 100) : 0 },
      { label: 'Résolues', count: this.resoluesCount, color: '#16A34A', icon: 'check', pct: all.length ? (this.resoluesCount / all.length * 100) : 0 },
    ];
  }

  get statutOptions() {
    return [
      { value: '', label: 'Toutes' },
      { value: 'OUVERTE', label: 'Ouvertes' },
      { value: 'EN_COURS', label: 'En cours' },
      { value: 'RESOLU', label: 'Résolues' },
      { value: 'REJETE', label: 'Rejetées' }
    ];
  }

  get chantierOptions() {
    return [
      { value: '', label: 'Sélectionner...' },
      ...this.chantiers().map(c => ({ value: String(c.id), label: c.nom }))
    ];
  }
}
