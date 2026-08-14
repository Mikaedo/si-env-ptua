import { Routes, Router } from '@angular/router';
import { inject } from '@angular/core';
import { authGuard, adminGuard, alertesGuard, specEnvGuard, specParGuard } from './core/guards';
import { AuthService } from './core/auth.service';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login').then(m => m.Login),
  },
  {
    // Cible du lien envoye dans le courriel de bienvenue. Volontairement
    // placee hors du shell protege : la page doit rester accessible meme
    // lorsqu'aucune session valide n'existe, et elle ferme d'elle-meme celle
    // qui serait deja ouverte dans le navigateur.
    path: 'premiere-connexion',
    loadComponent: () => import('./pages/premiere-connexion/premiere-connexion').then(m => m.PremiereConnexion),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./layout/shell').then(m => m.Shell),
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', loadComponent: () => import('./pages/dashboard/dashboard').then(m => m.Dashboard),
        canActivate: [() => {
          const auth = inject(AuthService);
          const router = inject(Router);
          if (auth.hasRole('ADMIN')) { router.navigate(['/admin-dashboard']); return false; }
          return true;
        }]
      },
      { path: 'signalements', loadComponent: () => import('./pages/signalements/signalements').then(m => m.Signalements) },
      { path: 'signalements/:id', loadComponent: () => import('./pages/signalement-detail/signalement-detail').then(m => m.SignalementDetail) },
      {
        path: 'alertes',
        canActivate: [alertesGuard],
        loadComponent: () => import('./pages/alertes/alertes').then(m => m.Alertes)
      },
      {
        path: 'satellite',
        canActivate: [specEnvGuard],
        loadComponent: () => import('./pages/satellite/satellite').then(m => m.Satellite)
      },
      {
        path: 'rapports',
        canActivate: [specEnvGuard],
        loadComponent: () => import('./pages/rapports/rapports').then(m => m.Rapports)
      },
      {
        path: 'plaintes',
        canActivate: [specParGuard],
        loadComponent: () => import('./pages/plaintes/plaintes').then(m => m.Plaintes)
      },
      {
        path: 'admin',
        canActivate: [adminGuard],
        loadComponent: () => import('./pages/admin/admin').then(m => m.Admin)
      },
      {
        path: 'admin-dashboard',
        canActivate: [adminGuard],
        loadComponent: () => import('./pages/admin-dashboard/admin-dashboard').then(m => m.AdminDashboard)
      },
    ]
  },
  { path: '**', redirectTo: '' }
];
