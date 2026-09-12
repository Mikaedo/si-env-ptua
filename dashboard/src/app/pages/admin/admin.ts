import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { User, Journal } from '../../core/models';
import { LucideAngularModule, Users, UserPlus, Cpu, ScrollText, Shield, Settings2, ShieldCheck, Upload, Building2, BellRing, Plus, AlertCircle, Trash2, Pencil, X } from 'lucide-angular';

@Component({
  selector: 'app-admin',
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './admin.html',
  styleUrl: './admin.scss'
})
export class Admin implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);
  private route = inject(ActivatedRoute);

  readonly Users = Users;
  readonly UserPlus = UserPlus;
  readonly Cpu = Cpu;
  readonly ScrollText = ScrollText;
  readonly Shield = Shield;
  readonly Settings2 = Settings2;
  readonly ShieldCheck = ShieldCheck;
  readonly Upload = Upload;
  readonly Building2 = Building2;
  readonly BellRing = BellRing;
  readonly Plus = Plus;
  readonly AlertCircle = AlertCircle;
  readonly Trash2 = Trash2;
  readonly Pencil = Pencil;
  readonly X = X;

  // Le referentiel des chantiers et les seuils d'alerte ont quitte cet ecran.
  // Ils relevent d'une appreciation environnementale et non de l'exploitation
  // de la plateforme, et se trouvent desormais dans l'analyse satellitaire,
  // au contact des indices qu'ils gouvernent.
  activeTab = signal<'users' | 'ia' | 'logs'>('users');
  users = signal<User[]>([]);
  logs = signal<Journal[]>([]);
  modeles = signal<Record<string, { disponible: boolean; version: number; taille_octets: number; deploye_le?: string }>>({});
  readonly typesModeles: ('detection' | 'classification')[] = ['detection', 'classification'];
  loading = signal(true);
  error = signal('');

  newUserNom = signal('');
  newUserEmail = signal('');
  newUserRole = signal('RESP_ENV');
  creating = signal(false);
  modelUploading = signal<'detection' | 'classification' | null>(null);
  dragOverType = signal<'detection' | 'classification' | null>(null);

  ngOnInit() {
    this.route.queryParamMap.subscribe(params => {
      const tab = params.get('tab');
      if (tab && ['users', 'ia', 'logs'].includes(tab)) {
        this.setTab(tab as any);
      }
    });
    this.loadUsers();
    this.api.getModelStatus().subscribe({ next: status => this.modeles.set(status) });
  }

  loadUsers() {
    this.api.getUsers().subscribe({
      next: (data) => { this.users.set(data); this.loading.set(false); },
      error: () => this.loading.set(false)
    });
  }

  // ── Le journal des actions ──────────────────────────────────────
  //
  // Il renvoyait tout, y compris les dépassements de seuil déclenchés
  // par le système. L'administrateur y cherche ce que les personnes
  // font : qui s'est connecté, qui a échoué, quel compte a changé. Un
  // NO2 au-dessus du seuil relève du Spécialiste et noyait ces lignes.
  filtreJournal = signal('');
  readonly filtresJournal = [
    { cle: '', libelle: 'Actions des utilisateurs' },
    { cle: 'ACCES', libelle: 'Connexions' },
    { cle: 'COMPTE', libelle: 'Comptes' },
    { cle: 'SYSTEME', libelle: 'Paramétrage' },
    { cle: 'TOUT', libelle: 'Tout, métier compris' },
  ];

  journalCharge = signal(false);
  journalEnCours = signal(false);

  loadLogs(force = false) {
    // La condition portait sur le nombre d'entrées déjà affichées : un
    // filtre qui ne renvoyait rien laissait la liste vide, et le filtre
    // suivant ne se rechargeait plus. C'est l'état du chargement, non
    // son résultat, qui décide de rappeler le serveur.
    if (this.journalCharge() && !force) return;
    const cle = this.filtreJournal();
    this.journalEnCours.set(true);
    this.api.getLogs(
      cle && cle !== 'TOUT' ? cle : undefined,
      cle === 'TOUT',
    ).subscribe({
      next: (data) => {
        this.logs.set(data);
        this.journalCharge.set(true);
        this.journalEnCours.set(false);
      },
      error: () => {
        this.journalEnCours.set(false);
        this.toast.error('Le journal n\'a pas pu être chargé.');
      }
    });
  }

  filtrerJournal(cle: string) {
    this.filtreJournal.set(cle);
    this.loadLogs(true);
  }

  /** Le libellé du filtre en cours, pour le dire quand la liste est vide. */
  get libelleFiltreJournal(): string {
    return this.filtresJournal
      .find(f => f.cle === this.filtreJournal())?.libelle ?? '';
  }

  /**
   * La nature de l'événement, en clair.
   *
   * Le journal n'affichait que INFO et WARNING, un vocabulaire de
   * développeur qui ne dit pas de quoi il s'agit. La catégorie, elle,
   * répond à la question que l'administrateur se pose en ouvrant cet
   * écran : est-ce un accès, un compte, un réglage.
   */
  libelleCategorie(code: string | null | undefined): string {
    const libelles: Record<string, string> = {
      'ACCES': 'Accès',
      'COMPTE': 'Compte',
      'SYSTEME': 'Système',
      'METIER': 'Suivi env.',
    };
    return libelles[code ?? ''] ?? 'Suivi env.';
  }

  couleurCategorie(code: string | null | undefined): string {
    const couleurs: Record<string, string> = {
      'ACCES': '#004F9F',
      'COMPTE': '#7C3AED',
      'SYSTEME': '#0891B2',
      'METIER': '#71717A',
    };
    return couleurs[code ?? ''] ?? '#71717A';
  }

  /**
   * L'heure précise de l'événement, non seulement le jour.
   *
   * Une trace d'audit sert à situer un fait dans le temps : « 12 sept. »
   * ne permet ni de rapprocher deux événements, ni de dire si une
   * tentative de connexion a précédé un changement de compte.
   */
  formatHorodatage(date: string): string {
    return new Date(date).toLocaleString('fr-FR', {
      day: '2-digit', month: 'short',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  }

  setTab(tab: 'users' | 'ia' | 'logs') {
    this.activeTab.set(tab);
    if (tab === 'logs') this.loadLogs();
  }

  get tabTitle(): string {
    const titles: Record<string, string> = {
      'users': 'Gestion des utilisateurs',
      'ia': 'Modèle IA Mobile',
      'logs': 'Journaux système'
    };
    return titles[this.activeTab()] ?? 'Administration';
  }

  get tabSubtitle(): string {
    const subs: Record<string, string> = {
      'users': 'Création et gestion des comptes utilisateurs',
      'ia': 'Déploiement et suivi du modèle d\'inférence locale',
      'logs': 'Audit complet des événements système'
    };
    return subs[this.activeTab()] ?? '';
  }


  deployModel(type: 'detection' | 'classification', event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.uploadFile(type, file);
  }

  onDrop(type: 'detection' | 'classification', event: DragEvent) {
    event.preventDefault();
    this.dragOverType.set(null);
    const file = event.dataTransfer?.files?.[0];
    if (!file) return;
    if (!file.name.endsWith('.onnx')) {
      this.toast.error('Seuls les fichiers .onnx sont acceptés');
      return;
    }
    this.uploadFile(type, file);
  }

  private uploadFile(type: 'detection' | 'classification', file: File) {
    this.modelUploading.set(type);
    this.api.uploadModel(type, file).subscribe({
      next: result => {
        this.modeles.update(m => ({ ...m, [type]: { disponible: result.disponible, version: result.version, taille_octets: result.taille_octets, deploye_le: result.deploye_le } }));
        this.modelUploading.set(null);
        this.toast.success('Modèle IA déployé : les mobiles verront la mise à jour proposée à leur prochaine synchronisation.');
      },
      error: () => { this.modelUploading.set(null); this.toast.error('Le déploiement du modèle a échoué.'); }
    });
  }

  createUser() {
    if (!this.newUserEmail()) return;
    this.creating.set(true);
    this.api.createUser({ nom: this.newUserNom() || undefined, email: this.newUserEmail(), role: this.newUserRole() }).subscribe({
      next: () => {
        this.creating.set(false);
        this.newUserNom.set('');
        this.newUserEmail.set('');
        this.loadUsers();
        this.toast.success('Utilisateur créé avec succès');
      },
      error: () => { this.creating.set(false); this.toast.error('Échec de la création de l\'utilisateur'); }
    });
  }

  updateUserRole(u: User, event: Event) {
    const newRole = (event.target as HTMLSelectElement).value;
    this.api.updateUser(u.id, { role: newRole }).subscribe({
      next: (updated) => {
        this.users.update(list => list.map(x => x.id === u.id ? updated : x));
        this.toast.success('Rôle mis à jour avec succès');
      },
      // Le serveur refuse qu'un administrateur se retire son propre
      // rôle : il dit pourquoi, autant le répéter à qui l'a tenté.
      error: (err) => {
        this.toast.error(err?.error?.detail
          || 'Échec de la mise à jour du rôle');
        this.loadUsers();
      }
    });
  }

  // ── Modification d'un compte ────────────────────────────────────
  //
  // Seul le rôle pouvait changer. Un agent qui se mariait, changeait de
  // numéro ou dont le nom avait été mal saisi obligeait à supprimer puis
  // recréer son compte, ce qui lui faisait perdre le lien avec ses
  // propres signalements.
  editingUser = signal<User | null>(null);
  editNom = signal('');
  editTelephone = signal('');
  editRole = signal('');
  savingUser = signal(false);

  openEdit(u: User) {
    this.editingUser.set(u);
    this.editNom.set(u.nom ?? '');
    this.editTelephone.set(u.telephone ?? '');
    this.editRole.set(u.role);
  }

  closeEdit() {
    this.editingUser.set(null);
    this.savingUser.set(false);
  }

  saveUser() {
    const u = this.editingUser();
    if (!u) return;
    this.savingUser.set(true);
    this.api.updateUser(u.id, {
      nom: this.editNom().trim() || undefined,
      telephone: this.editTelephone().trim() || undefined,
      role: this.editRole(),
    }).subscribe({
      next: (updated) => {
        this.users.update(list => list.map(x => x.id === u.id ? updated : x));
        this.closeEdit();
        this.toast.success('Compte mis à jour');
      },
      error: (err) => {
        this.savingUser.set(false);
        this.toast.error(err?.error?.detail || 'La mise à jour a échoué.');
      }
    });
  }

  deleteUser(u: User) {
    if (!confirm(`Supprimer l'utilisateur ${u.email} ? Cette action est irréversible.`)) return;
    this.api.deleteUser(u.id).subscribe({
      next: () => {
        this.users.update(list => list.filter(x => x.id !== u.id));
        this.toast.success('Utilisateur supprimé avec succès');
      },
      // Le serveur refuse la suppression du dernier administrateur et
      // celle de son propre compte : son motif vaut mieux qu'un échec
      // muet.
      error: (err) => this.toast.error(err?.error?.detail
        || 'Échec de la suppression de l\'utilisateur')
    });
  }



  get roleLabels(): Record<string, string> {
    return {
      'ADMIN': 'Administrateur',
      'SPEC_ENV': 'Spéc. Env.',
      'SPEC_PAR': 'Spéc. P.A.R',
      'RESP_ENV': 'Resp. Env.',
      'EXPERT_HSE': 'Expert HSE',
      // Les deux organismes de contrôle manquaient à la liste : leurs
      // comptes existent en production mais s'affichaient sous leur
      // sigle brut, et la modification d'un tel compte aurait écrasé
      // son rôle par le premier de la liste.
      'ANDE': 'ANDE (consultation)',
      'BAD': 'BAD (consultation)',
    };
  }

  /** Les rôles qu'un administrateur peut attribuer.
   *
   * Le riverain n'y figure pas : son compte se crée depuis
   * l'application citoyenne, à l'inscription, non par invitation.
   */
  readonly rolesDisponibles = [
    'RESP_ENV', 'EXPERT_HSE', 'SPEC_ENV', 'SPEC_PAR',
    'ANDE', 'BAD', 'ADMIN',
  ];

  get roleColors(): Record<string, string> {
    return {
      'ADMIN': '#004F9F',
      'SPEC_ENV': '#1565C0',
      'SPEC_PAR': '#F37021',
      'RESP_ENV': '#16A34A',
      'EXPERT_HSE': '#757575',
    };
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  }
}
