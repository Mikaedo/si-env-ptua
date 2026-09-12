import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ToastService } from '../../core/toast.service';
import { Plainte, Chantier } from '../../core/models';
import { LucideAngularModule, ShieldAlert, Search, MapPin, Plus, CheckCircle, X, Clock, User, Phone, Building2, AlertCircle, BarChart2, AlertTriangle, Smartphone, Play } from 'lucide-angular';
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

  /**
   * Un traitement a-t-il ete enregistre pour cette plainte ?
   *
   * Le mecanisme de gestion des plaintes suppose qu'on puisse dire au
   * plaignant ce qui a ete fait de sa doleance : clore une plainte sans
   * cette trace priverait la reponse de son contenu.
   */
  aUnTraitement(p: Plainte): boolean {
    return (p.actions ?? []).length > 0;
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
  readonly Play = Play;

  /** Les quatre etats du mecanisme, dans l'ordre du traitement.
   *
   * La barre de progression remplace le formulaire de saisie manuelle :
   * ce que le specialiste vient verifier, c'est ou en sont les
   * doleances, non comment en retaper une que le riverain a deja
   * deposee depuis son telephone.
   */
  get etapes() {
    const compte = (s: string) =>
      this.plaintes().filter(p => p.statut === s).length;
    return [
      { cle: 'OUVERTE', libelle: 'reçues', couleur: '#F37021',
        n: compte('OUVERTE') },
      { cle: 'EN_COURS', libelle: 'en cours', couleur: '#004F9F',
        n: compte('EN_COURS') },
      { cle: 'RESOLU', libelle: 'closes', couleur: '#16A34A',
        n: compte('RESOLU') },
      { cle: 'REJETE', libelle: 'sans suite', couleur: '#A1A1AA',
        n: compte('REJETE') },
    ];
  }

  /** La part des doleances ayant recu une reponse.
   *
   * Les dossiers classes sans suite comptent comme traites : une
   * doleance examinee puis ecartee a bien recu une reponse, elle n'est
   * pas en souffrance.
   */
  get tauxTraitement(): number {
    const total = this.plaintes().length;
    if (!total) return 0;
    const closes = this.plaintes().filter(
      p => p.statut === 'RESOLU' || p.statut === 'REJETE').length;
    return Math.round((closes / total) * 100);
  }

  libelleStatut(code: string): string {
    const libelles: Record<string, string> = {
      OUVERTE: 'Ouverte',
      EN_COURS: 'En cours de traitement',
      RESOLU: 'Close',
      REJETE: 'Classée sans suite',
    };
    return libelles[code] ?? code;
  }

  couleurTaux(taux: number): string {
    if (taux >= 80) return '#16A34A';
    if (taux >= 50) return '#F37021';
    return '#D32F2F';
  }

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

  // La saisie manuelle d'une plainte a ete retiree de cet ecran.
  //
  // Elle datait d'avant l'application citoyenne : le riverain se
  // presentait au guichet, un agent recopiait sa doleance dans le
  // tableau de bord. Les doleances arrivent desormais du telephone du
  // riverain, horodatees et geolocalisees a la source. Les retaper ici
  // rouvrirait la ressaisie que tout le systeme supprime, et priverait
  // la plainte de sa position comme de son canal d'origine.
  //
  // Le point d'entree du serveur reste ouvert : il sert a l'application
  // citoyenne, et servirait a un guichet si l'AGEROUTE en remettait un
  // en place.

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
      error: (err) => {
        // Le serveur explique pourquoi il refuse, par exemple qu'aucun
        // traitement n'a ete enregistre : autant le dire a l'utilisateur
        // plutot que de lui opposer un echec sans raison.
        const motif = err?.error?.detail || 'La mise à jour du statut a échoué.';
        this.error.set(motif);
        this.toast.error(motif);
      }
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
}
