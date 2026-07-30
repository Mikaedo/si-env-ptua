import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

const DASHBOARD_ROLES = ['ADMIN', 'SPEC_ENV', 'SPEC_PAR', 'RESP_ENV', 'EXPERT_HSE'];

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

  if (auth.isAuthenticated && auth.hasRole('SPEC_ENV', 'SPEC_PAR')) {
    return true;
  }

  if (auth.isAuthenticated && auth.hasRole('ADMIN')) {
    router.navigate(['/admin-dashboard']);
    return false;
  }

  router.navigate(['/dashboard']);
  return false;
};

export const specEnvGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated && auth.hasRole('SPEC_ENV')) {
    return true;
  }

  if (auth.isAuthenticated && auth.hasRole('ADMIN')) {
    router.navigate(['/admin-dashboard']);
    return false;
  }

  router.navigate(['/dashboard']);
  return false;
};

export const specParGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated && auth.hasRole('SPEC_PAR')) {
    return true;
  }

  if (auth.isAuthenticated && auth.hasRole('ADMIN')) {
    router.navigate(['/admin-dashboard']);
    return false;
  }

  router.navigate(['/dashboard']);
  return false;
};
