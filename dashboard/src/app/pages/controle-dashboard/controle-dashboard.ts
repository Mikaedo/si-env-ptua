import { Component, signal, computed, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import {
  Signalement, Alerte, Chantier, IndiceSatellite, TransmissionRapport,
  Plainte,
} from '../../core/models';
import { RouterLink } from '@angular/router';
import {
  LucideAngularModule, ShieldCheck, FileCheck2, AlertTriangle, Bell,
  Satellite, MapPin, Clock, TrendingDown, Eye, Inbox, Scale, Landmark,
  Users,
} from 'lucide-angular';

/**
 * L'ecran d'accueil des organismes de controle, ANDE et BAD.
 *
 * Ils voyaient jusqu'ici le tableau de bord du Specialiste Suivi
 * Environnemental, prive de ses commandes. Un ecran ampute n'est pas un
 * ecran concu : il garde l'ordre de lecture de celui qui pilote, quand
 * un controleur ne cherche pas la meme chose.
 *
 * Le specialiste pilote : il veut savoir ce qui reste a traiter, et
 * agir dessus. Le controleur atteste : il veut savoir si le suivi est
 * tenu, si les constats graves trouvent une issue, et ce qui lui a ete
 * officiellement transmis. La difference n'est pas dans les droits,
 * elle est dans la question posee.
 *
 * Cet ecran repond donc a la question du controleur, dans son ordre :
 * le taux de traitement d'abord, puis ce qui reste ouvert, puis les
 * remises recues. Les donnees sont les memes, leur mise en scene ne
 * l'est pas.
 */
@Component({
  selector: 'app-controle-dashboard',
  imports: [CommonModule, LucideAngularModule, RouterLink],
  templateUrl: './controle-dashboard.html',
  styleUrl: './controle-dashboard.scss',
})
export class ControleDashboard implements OnInit {
  private api = inject(ApiService);
  public auth = inject(AuthService);

  readonly ShieldCheck = ShieldCheck;
  readonly FileCheck2 = FileCheck2;
  readonly AlertTriangle = AlertTriangle;
  readonly Bell = Bell;
  readonly Satellite = Satellite;
  readonly MapPin = MapPin;
  readonly Clock = Clock;
  readonly TrendingDown = TrendingDown;
  readonly Eye = Eye;
  readonly Inbox = Inbox;
  readonly Scale = Scale;
  readonly Landmark = Landmark;
  readonly Users = Users;

  signalements = signal<Signalement[]>([]);
  alertes = signal<Alerte[]>([]);
  chantiers = signal<Chantier[]>([]);
  indices = signal<IndiceSatellite[]>([]);
  transmissions = signal<TransmissionRapport[]>([]);
  plaintes = signal<Plainte[]>([]);
  loading = signal(true);

  /** Le bailleur seul suit le volet social.
   *
   * C'est la difference de fond entre les deux organismes, et elle vient
   * du tableau 3.2 : l'agence de tutelle controle la conformite
   * environnementale, le bailleur controle ses sauvegardes
   * operationnelles, « volet social compris ». Les doleances de
   * riverains relevent de ce volet, d'ou l'acces du bailleur au
   * mecanisme de gestion des plaintes, que l'agence n'a pas.
   */
  suitLeVoletSocial = computed(() => this.auth.user()?.role === 'BAD');

  plaintesOuvertes = computed(() =>
    this.plaintes().filter(p => p.statut !== 'RESOLU'
                             && p.statut !== 'REJETE').length);

  /** L'organisme connecte, nomme en toutes lettres.
   *
   * L'ANDE verifie la conformite reglementaire, la BAD le respect de
   * ses sauvegardes operationnelles : le bandeau nomme ce mandat plutot
   * que de saluer l'utilisateur, parce qu'un controleur consulte au
   * titre de son institution, non a titre personnel.
   */
  organisme = computed(() => {
    const role = this.auth.user()?.role;
    if (role === 'BAD') {
      return {
        sigle: 'BAD',
        nom: 'Banque Africaine de Développement',
        mandat: 'Contrôle du respect des sauvegardes opérationnelles, '
              + 'volet social compris',
        icone: this.Landmark,
      };
    }
    return {
      sigle: 'ANDE',
      nom: "Agence Nationale de l'Environnement",
      mandat: 'Vérification de la conformité réglementaire des chantiers '
            + 'et réception des rapports périodiques',
      icone: this.Scale,
    };
  });

  // ── Les indicateurs de conformite ──────────────────────────────────
  //
  // Un controleur ne compte pas les signalements, il mesure si le suivi
  // est tenu : la part traitee, ce qui reste ouvert, et depuis combien
  // de temps.

  total = computed(() => this.signalements().length);

  traites = computed(() =>
    this.signalements().filter(s => s.statut === 'CLOTURE').length);

  tauxTraitement = computed(() => {
    const t = this.total();
    return t ? Math.round((this.traites() / t) * 100) : 0;
  });

  /** Les constats de criticite elevee encore ouverts.
   *
   * C'est l'indicateur le plus parlant pour un controleur : un constat
   * grave qui reste ouvert engage la conformite du projet, la ou un
   * constat faible non traite ne l'engage pas de la meme facon.
   */
  gravesOuverts = computed(() =>
    this.signalements().filter(
      s => s.criticite === 'ELEVE' && s.statut !== 'CLOTURE').length);

  /** L'anciennete du plus vieux constat non clos, en jours.
   *
   * Le PGES impose un suivi regulier : un constat ouvert depuis des
   * semaines est un manquement, meme si le taux global reste bon.
   */
  ancienneteMax = computed(() => {
    const ouverts = this.signalements().filter(s => s.statut !== 'CLOTURE');
    if (!ouverts.length) return 0;
    const maintenant = Date.now();
    return Math.max(...ouverts.map(s => {
      const cree = new Date(s.cree_le ?? '').getTime();
      return Number.isNaN(cree)
        ? 0 : Math.floor((maintenant - cree) / 86400000);
    }));
  });

  alertesNonLues = computed(() =>
    this.alertes().filter(a => !a.recue).length);

  /** Les indices satellitaires au-dela de leur seuil d'alerte. */
  indicesDepasses = computed(() =>
    this.indices().filter(i => i.statut === 'MAUVAIS').length);

  /** L'etat de chaque chantier, du plus preoccupant au plus sain.
   *
   * Le controleur balaie la liste pour reperer ou porter son attention :
   * elle est donc ordonnee par nombre de constats graves ouverts, non
   * par ordre alphabetique.
   */
  etatChantiers = computed(() => {
    const parChantier = this.chantiers().map(c => {
      const siens = this.signalements().filter(s => s.chantier?.id === c.id);
      const clos = siens.filter(s => s.statut === 'CLOTURE').length;
      const graves = siens.filter(
        s => s.criticite === 'ELEVE' && s.statut !== 'CLOTURE').length;
      return {
        nom: c.nom,
        commune: c.commune ?? '',
        total: siens.length,
        clos,
        graves,
        taux: siens.length ? Math.round((clos / siens.length) * 100) : null,
      };
    });
    return parChantier.sort(
      (a, b) => b.graves - a.graves || (b.total - a.total));
  });

  /** Les remises recues, la plus recente en tete. */
  remisesRecues = computed(() =>
    [...this.transmissions()].sort((a, b) =>
      new Date(b.transmis_le).getTime() - new Date(a.transmis_le).getTime()));

  /** La date de la derniere remise, ou rien si aucune. */
  derniereRemise = computed(() => {
    const liste = this.remisesRecues();
    return liste.length ? liste[0] : null;
  });

  ngOnInit(): void {
    this.charger();
  }

  private charger(): void {
    this.loading.set(true);
    // Les doleances ne sont demandees qu'au bailleur : le serveur les
    // refuse a l'agence de tutelle, et une requete vouee au 403 salirait
    // la console sans rien apporter.
    let restants = this.suitLeVoletSocial() ? 6 : 5;
    const fini = () => { if (--restants <= 0) this.loading.set(false); };

    if (this.suitLeVoletSocial()) {
      this.api.getPlaintes().subscribe({
        next: d => { this.plaintes.set(d); fini(); },
        error: () => fini(),
      });
    }

    this.api.getSignalements().subscribe({
      next: d => { this.signalements.set(d); fini(); },
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
    this.api.getIndicesSatellite().subscribe({
      next: d => { this.indices.set(d); fini(); },
      error: () => fini(),
    });
    this.api.getTransmissions().subscribe({
      next: d => { this.transmissions.set(d); fini(); },
      error: () => fini(),
    });
  }

  /** La couleur d'un taux de traitement, selon trois paliers.
   *
   * Les paliers sont ceux de la redaction du rapport : au-dela de 80 %
   * le suivi est tenu, sous 50 % il appelle une attention particuliere.
   */
  couleurTaux(taux: number | null): string {
    if (taux === null) return '#A1A1AA';
    if (taux >= 80) return '#16A34A';
    if (taux >= 50) return '#F37021';
    return '#D32F2F';
  }

  formatDate(valeur?: string): string {
    if (!valeur) return '—';
    const d = new Date(valeur);
    return Number.isNaN(d.getTime())
      ? '—' : d.toLocaleDateString('fr-FR',
        { day: '2-digit', month: 'long', year: 'numeric' });
  }
}
