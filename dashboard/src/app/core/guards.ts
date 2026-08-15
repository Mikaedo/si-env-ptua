import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

// Profils admis dans le tableau de bord. L'ANDE et la BAD s'y ajoutent en
// consultation : elles lisent le dispositif sans jamais l'ecrire, le serveur
// refusant de son cote toute requete d'ecriture emise avec leur jeton.
const DASHBOARD_ROLES = [
  'ADMIN', 'SPEC_ENV', 'SPEC_PAR', 'RESP_ENV', 'EXPERT_HSE', 'ANDE', 'BAD',
];

/** Profils de consultation, sans droit d'ecriture. */
export const ROLES_CONSULTATION = ['ANDE', 'BAD'];

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated && auth.hasRole(...DASHBOARD_ROLES)) {
    return true;
  }

  auth.logout();
  router.navigate(['/login']);
  return false;
};

export const adminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated && auth.hasRole('ADMIN')) {
    return true;
  }

  router.navigate(['/dashboard']);
  return false;
};

export const alertesGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated && auth.hasRole('SPEC_ENV', 'SPEC_PAR', 'ANDE', 'BAD')) {
    return true;
  }

  if (auth.isAuthenticated && auth.hasRole('ADMIN')) {
    router.navigate(['/admin-dashboard']);
    return false;
  }

  router.navigate(['/dashboard']);
  return false;
};

// Analyse satellitaire et rapports : ouverts au specialiste qui les produit
// et aux deux organismes de controle qui les verifient.
export const specEnvGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated && auth.hasRole('SPEC_ENV', 'ANDE', 'BAD')) {
    return true;
  }

  if (auth.isAuthenticated && auth.hasRole('ADMIN')) {
    router.navigate(['/admin-dashboard']);
    return false;
  }

  router.navigate(['/dashboard']);
  return false;
};

// Doleances : le bailleur y accede au titre de sa sauvegarde sociale,
// l'agence nationale non, son mandat portant sur l'environnement.
export const specParGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated && auth.hasRole('SPEC_PAR', 'BAD')) {
    return true;
  }

  if (auth.isAuthenticated && auth.hasRole('ADMIN')) {
    router.navigate(['/admin-dashboard']);
    return false;
  }

  router.navigate(['/dashboard']);
  return false;
};
