import { Component, signal, computed, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { Plainte, Alerte, Chantier } from '../../core/models';
import {
  LucideAngularModule, Users, Clock, CheckCircle, AlertTriangle,
  Smartphone, Building2, ChevronRight, Bell, MapPin,
} from 'lucide-angular';

/**
 * L'ecran d'accueil du Specialiste Suivi du P.A.R.
 *
 * Il arrivait sur le tableau de bord du Specialiste Suivi
 * Environnemental, qui compte les nuisances constatees sur les
 * chantiers. Or son metier n'est pas celui-la : le diagramme de cas
 * d'utilisation, figure 4.2, ne lui relie que deux cas, « Traiter les
 * plaintes » et « Affecter une action corrective ». Il suit le Plan
 * d'Action de Reinstallation, c'est-a-dire les personnes affectees par
 * le projet, non les nuisances elles-memes.
 *
 * Cet ecran repond donc a sa question : combien de doleances attendent
 * une reponse, depuis combien de temps, et par quel canal elles
 * arrivent. Ce dernier point compte pour le rapport au bailleur, qui
 * mesure l'apport du canal mobile au mecanisme de gestion des plaintes.
 */
@Component({
  selector: 'app-par-dashboard',
  imports: [CommonModule, LucideAngularModule, RouterLink],
  templateUrl: './par-dashboard.html',
  styleUrl: './par-dashboard.scss',
})
export class ParDashboard implements OnInit {
  private api = inject(ApiService);

  readonly Users = Users;
  readonly Clock = Clock;
  readonly CheckCircle = CheckCircle;
  readonly AlertTriangle = AlertTriangle;
  readonly Smartphone = Smartphone;
  readonly Building2 = Building2;
  readonly ChevronRight = ChevronRight;
  readonly Bell = Bell;
  readonly MapPin = MapPin;

  plaintes = signal<Plainte[]>([]);
  alertes = signal<Alerte[]>([]);
  chantiers = signal<Chantier[]>([]);
  loading = signal(true);

  // ── Les compteurs du mecanisme de gestion des plaintes ────────────

  total = computed(() => this.plaintes().length);

  /** Les doleances qui attendent encore une reponse. */
  ouvertes = computed(() =>
    this.plaintes().filter(p => p.statut === 'OUVERTE'
                             || p.statut === 'EN_COURS').length);

  traitees = computed(() =>
    this.plaintes().filter(p => p.statut === 'RESOLU').length);

  tauxReponse = computed(() => {
    const t = this.total();
    return t ? Math.round((this.traitees() / t) * 100) : 0;
  });

  /** La part deposee depuis l'application citoyenne.
   *
   * Le canal de saisie est conserve precisement pour mesurer ce que le
   * telephone apporte au mecanisme, qui reposait jusqu'ici sur un
   * recueil au guichet ou en reunion de quartier.
   */
  parMobile = computed(() =>
    this.plaintes().filter(p => p.canal === 'MOBILE').length);

  partMobile = computed(() => {
    const t = this.total();
    return t ? Math.round((this.parMobile() / t) * 100) : 0;
  });

  /** L'anciennete de la plus vieille doleance sans reponse, en jours.
   *
   * Une plainte qui dort est le reproche le plus direct qu'un riverain
   * puisse adresser au projet : ce compteur la rend visible.
   */
  attenteMax = computed(() => {
    const ouvertes = this.plaintes().filter(
      p => p.statut === 'OUVERTE' || p.statut === 'EN_COURS');
    if (!ouvertes.length) return 0;
    const maintenant = Date.now();
    return Math.max(...ouvertes.map(p => {
      const cree = new Date(p.cree_le ?? '').getTime();
      return Number.isNaN(cree)
        ? 0 : Math.floor((maintenant - cree) / 86400000);
    }));
  });

  /** Les doleances en attente, la plus ancienne en tete.
   *
   * L'ordre n'est pas celui du depot mais celui de l'urgence : c'est la
   * plus ancienne qui expose le plus le projet.
   */
  filesDAttente = computed(() =>
    this.plaintes()
      .filter(p => p.statut === 'OUVERTE' || p.statut === 'EN_COURS')
      .sort((a, b) =>
        new Date(a.cree_le).getTime() - new Date(b.cree_le).getTime())
      .slice(0, 6));

  /** La repartition par nature declaree, la plus frequente en tete. */
  parCategorie = computed(() => {
    const cumul = new Map<string, number>();
    for (const p of this.plaintes()) {
      const cle = p.categorie || 'Non précisée';
      cumul.set(cle, (cumul.get(cle) ?? 0) + 1);
    }
    return [...cumul.entries()]
      .map(([nom, n]) => ({ nom, n }))
      .sort((a, b) => b.n - a.n)
      .slice(0, 5);
  });

  alertesNonLues = computed(() =>
    this.alertes().filter(a => !a.recue).length);

  ngOnInit(): void {
    this.loading.set(true);
    let restants = 3;
    const fini = () => { if (--restants <= 0) this.loading.set(false); };

    this.api.getPlaintes().subscribe({
      next: d => { this.plaintes.set(d); fini(); },
      error: () => fini(),
    });
    this.api.getAlertes().subscribe({
      next: d => { this.alertes.set(d); fini(); },
      error: () => fini(),
    });
    this.api.getChantiers().subscribe({
      next: d => { this.chantiers.set(d); fini(); },
      error: () => fini(),
    });
  }

  /** Le nom du chantier vise, ou une mention neutre. */
  nomChantier(p: Plainte): string {
    const c = this.chantiers().find(x => x.id === p.chantier_id);
    return c ? c.nom : 'Chantier non rattaché';
  }

  joursDepuis(valeur?: string): number {
    if (!valeur) return 0;
    const d = new Date(valeur).getTime();
    return Number.isNaN(d)
      ? 0 : Math.floor((Date.now() - d) / 86400000);
  }

  /** La couleur d'une attente : au-dela de trente jours, elle presse. */
  couleurAttente(jours: number): string {
    if (jours >= 30) return '#D32F2F';
    if (jours >= 14) return '#F37021';
    return '#71717A';
  }

  couleurTaux(taux: number): string {
    if (taux >= 80) return '#16A34A';
    if (taux >= 50) return '#F37021';
    return '#D32F2F';
  }

  libelleStatut(statut: string): string {
    const table: Record<string, string> = {
      OUVERTE: 'Reçue',
      EN_COURS: 'En cours',
      RESOLU: 'Traitée',
      REJETE: 'Classée sans suite',
    };
    return table[statut] ?? statut;
  }
}
