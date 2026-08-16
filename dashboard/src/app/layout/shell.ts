import { Component, signal, inject, OnInit, OnDestroy } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { CommonModule, DatePipe } from '@angular/common';
import { AuthService } from '../core/auth.service';
import { ApiService } from '../core/api.service';
import { ToastContainer } from '../shared/toast-container';
import { Alerte } from '../core/models';
import { LucideAngularModule, LayoutDashboard, MapPin, Bell, Satellite, FileText, Users,
  ShieldAlert, LogOut, Menu, X, ChevronRight, Search, Clock, Activity, CircleUser, BellRing, Eye,
  Cpu, Settings2, ScrollText } from 'lucide-angular';

interface NavItem {
  label: string;
  icon: any;
  route: string;
  roles?: string[];
  queryParams?: Record<string, string>;
  isSection?: boolean;
}

@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule, LucideAngularModule, ToastContainer],
  templateUrl: './shell.html',
  styleUrl: './shell.scss'
})
export class Shell implements OnInit, OnDestroy {
  private auth = inject(AuthService);
  private api = inject(ApiService);
  private router = inject(Router);

  readonly X = X;
  readonly Menu = Menu;
  readonly LogOut = LogOut;
  readonly ChevronRight = ChevronRight;
  readonly Bell = Bell;
  readonly BellRing = BellRing;
  readonly Search = Search;
  readonly Clock = Clock;
  readonly Activity = Activity;
  readonly CircleUser = CircleUser;

  readonly sidebarOpen = signal(false);
  readonly profileOpen = signal(false);
  readonly notifOpen = signal(false);
  readonly alertes = signal<Alerte[]>([]);
  readonly currentUser = this.auth.user;
  private refreshSub?: any;

  readonly currentTime = signal(new Date());
  private timerId: any;

  ngOnInit() {
    this.timerId = setInterval(() => this.currentTime.set(new Date()), 1000);
    this.refreshSub = setInterval(() => this.loadAlertes(), 15000);
    this.loadAlertes();
  }

  ngOnDestroy() {
    if (this.timerId) clearInterval(this.timerId);
    if (this.refreshSub) clearInterval(this.refreshSub);
  }

  get timeStr(): string {
    return this.currentTime().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  get dateStr(): string {
    return this.currentTime().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  }

  // L'entree « Configuration » a disparu de l'administration : le referentiel
  // des chantiers et les seuils d'alerte ont rejoint l'analyse satellitaire,
  // au contact des indices qu'ils gouvernent.
  //
  // L'ANDE et la BAD consultent le dispositif sans pouvoir l'ecrire. Leurs
  // perimetres different : le mandat de l'agence nationale porte sur la
  // conformite environnementale, celui du bailleur englobe en plus le volet
  // social, dont releve le traitement des doleances de riverains.
  navItems: NavItem[] = [
    { label: 'Tableau de bord', icon: LayoutDashboard, route: '/dashboard', roles: ['SPEC_ENV', 'SPEC_PAR', 'RESP_ENV', 'EXPERT_HSE', 'ANDE', 'BAD'] },
    { label: 'Signalements', icon: MapPin, route: '/signalements', roles: ['SPEC_ENV', 'SPEC_PAR', 'RESP_ENV', 'EXPERT_HSE', 'ANDE', 'BAD'] },
    { label: 'Alertes', icon: Bell, route: '/alertes', roles: ['SPEC_ENV', 'SPEC_PAR', 'ANDE', 'BAD'] },
    { label: 'Analyse satellitaire', icon: Satellite, route: '/satellite', roles: ['SPEC_ENV', 'ANDE', 'BAD'] },
    { label: 'Rapports de suivi', icon: FileText, route: '/rapports', roles: ['SPEC_ENV', 'ANDE', 'BAD'] },
    { label: 'Plaintes (MGP)', icon: ShieldAlert, route: '/plaintes', roles: ['SPEC_PAR', 'BAD'] },
    // Admin: section label
    { label: 'Administration', icon: Users, route: '', roles: ['ADMIN'], isSection: true },
    // Admin: sub-items
    { label: 'Utilisateurs', icon: Users, route: '/admin', roles: ['ADMIN'], queryParams: { tab: 'users' } },
    { label: 'Modèle IA Mobile', icon: Cpu, route: '/admin', roles: ['ADMIN'], queryParams: { tab: 'ia' } },
    { label: 'Journaux Système', icon: ScrollText, route: '/admin', roles: ['ADMIN'], queryParams: { tab: 'logs' } },
    // Admin: consultation
    { label: 'Vue consultation', icon: Eye, route: '/admin-dashboard', roles: ['ADMIN'] },
  ];

  get visibleNavItems(): NavItem[] {
    const user = this.currentUser();
    if (!user) return [];
    return this.navItems.filter(item => !item.roles || item.roles.includes(user.role));
  }

  toggleSidebar() {
    this.sidebarOpen.update(v => !v);
  }

  closeSidebar() {
    this.sidebarOpen.set(false);
  }

  toggleProfile() {
    this.profileOpen.update(v => !v);
    this.notifOpen.set(false);
  }

  closeProfile() {
    this.profileOpen.set(false);
  }

  toggleNotif() {
    this.notifOpen.update(v => !v);
    this.profileOpen.set(false);
  }

  closeNotif() {
    this.notifOpen.set(false);
  }

  private loadAlertes() {
    this.api.getAlertes().subscribe({
      next: (data) => this.alertes.set(data),
      error: () => {}
    });
  }

  get alertesNonLues(): number {
    return this.alertes().filter(a => !a.recue).length;
  }

  get alertesRecentes(): Alerte[] {
    return [...this.alertes()]
      .sort((a, b) => new Date(b.cree_le).getTime() - new Date(a.cree_le).getTime())
      .slice(0, 8);
  }

  get alertesCritiques(): number {
    return this.alertes().filter(a => a.niveau === 'CRITIQUE').length;
  }

  formatAlerteDate(date: string): string {
    const d = new Date(date);
    const now = new Date();
    const diff = (now.getTime() - d.getTime()) / 1000;
    if (diff < 60) return 'À l\'instant';
    if (diff < 3600) return Math.floor(diff / 60) + ' min';
    if (diff < 86400) return Math.floor(diff / 3600) + ' h';
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  get currentTitle(): string {
    const url = this.router.url;
    const item = this.navItems.find(i => url.startsWith(i.route));
    return item?.label ?? 'Tableau de bord';
  }

  get roleLabel(): string {
    const roles: Record<string, string> = {
      'ADMIN': 'Administrateur',
      'SPEC_ENV': 'Spéc. Suivi Env.',
      'SPEC_PAR': 'Spéc. Suivi P.A.R',
    };
    return roles[this.currentUser()?.role ?? ''] ?? '';
  }

  get initials(): string {
    const user = this.currentUser();
    if (!user) return '';
    const name = user.nom || user.email;
    return name.substring(0, 2).toUpperCase();
  }
}
