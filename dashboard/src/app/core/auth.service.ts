import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { User, LoginResponse } from './models';

import { environment } from '../../environments/environment';
const API_URL = environment.apiUrl;
const TOKEN_KEY = 'sienv_token';
const USER_KEY = 'sienv_user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private _user = signal<User | null>(null);
  readonly user = this._user.asReadonly();

  constructor(private http: HttpClient) {
    const savedUser = localStorage.getItem(USER_KEY);
    if (savedUser) {
      this._user.set(JSON.parse(savedUser));
    }
  }

  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  get isAuthenticated(): boolean {
    return !!this.token;
  }

  login(email: string, password: string): Observable<LoginResponse> {
    const body = new URLSearchParams();
    body.set('username', email);
    body.set('password', password);

    return this.http.post<LoginResponse>(`${API_URL}/auth/login`, body.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).pipe(
      tap(res => {
        localStorage.setItem(TOKEN_KEY, res.access_token);
        const user: User = {
          id: 0,
          nom: '',
          email,
          role: res.role as User['role'],
          premiere_connexion: res.premiere_connexion
        };
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        this._user.set(user);
      })
    );
  }

  /**
   * Deuxieme temps de la premiere connexion.
   *
   * Le premier temps est un appel a login() : quand le compte n'a pas encore
   * de mot de passe, le serveur delivre un jeton sans rien verifier, ce qui
   * autorise l'appel ci-dessous. L'utilisateur y depose son nom, son telephone
   * et le mot de passe qu'il choisit.
   */
  firstLogin(nom: string, telephone: string, motDePasse: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${API_URL}/auth/first-login`, {
      nom,
      telephone,
      mot_de_passe: motDePasse,
    }).pipe(
      tap(res => {
        localStorage.setItem(TOKEN_KEY, res.access_token);
        const brut = localStorage.getItem(USER_KEY);
        const user: User = brut ? JSON.parse(brut) : ({} as User);
        user.nom = nom;
        user.role = res.role as User['role'];
        user.premiere_connexion = false;
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        this._user.set(user);
      })
    );
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this._user.set(null);
  }

  forgotPassword(email: string): Observable<any> {
    return this.http.post(`${API_URL}/auth/forgot`, { email }, {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  verifyCode(email: string, code: string): Observable<any> {
    return this.http.post(`${API_URL}/auth/verify-code`, { email, code }, {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  resetPassword(email: string, code: string, nouveau_mot_de_passe: string): Observable<any> {
    return this.http.post(`${API_URL}/auth/reset-password`, { email, code, nouveau_mot_de_passe }, {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  hasRole(...roles: string[]): boolean {
    const u = this._user();
    return !!u && roles.includes(u.role);
  }
}
