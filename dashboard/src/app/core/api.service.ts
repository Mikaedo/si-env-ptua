import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Signalement, Chantier, Alerte, Plainte, NonConformite, IndiceSatellite, User, AlerteSeuil, Journal } from './models';
import { AuthService } from './auth.service';

const API_URL = 'http://localhost:8000';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);

  private get headers() {
    return {
      'Authorization': `Bearer ${this.auth.token}`,
      'Content-Type': 'application/json'
    };
  }

  // Signalements
  getSignalements(): Observable<Signalement[]> {
    return this.http.get<Signalement[]>(`${API_URL}/signalements`, { headers: this.headers });
  }

  getSignalement(id: number): Observable<Signalement> {
    return this.http.get<Signalement>(`${API_URL}/signalements/${id}`, { headers: this.headers });
  }

  updateSignalementStatut(id: number, statut: string): Observable<Signalement> {
    return this.http.patch<Signalement>(`${API_URL}/signalements/${id}/statut`,
      { statut }, { headers: this.headers });
  }

  // Chantiers
  getChantiers(): Observable<Chantier[]> {
    return this.http.get<Chantier[]>(`${API_URL}/chantiers`, { headers: this.headers });
  }

  // Alertes
  getAlertes(): Observable<Alerte[]> {
    return this.http.get<Alerte[]>(`${API_URL}/alertes`, { headers: this.headers });
  }

  acknowledgeAlerte(id: number): Observable<Alerte> {
    return this.http.post<Alerte>(`${API_URL}/alertes/${id}/accuser`, {}, { headers: this.headers });
  }

  // Plaintes
  getPlaintes(): Observable<Plainte[]> {
    return this.http.get<Plainte[]>(`${API_URL}/plaintes`, { headers: this.headers });
  }

  createPlainte(data: { nom_plaignant: string; contact?: string; description: string; chantier_id?: number }): Observable<Plainte> {
    return this.http.post<Plainte>(`${API_URL}/plaintes`, data, { headers: this.headers });
  }

  updatePlainteStatut(id: number, statut: string): Observable<Plainte> {
    return this.http.patch<Plainte>(`${API_URL}/plaintes/${id}/statut`, { statut }, { headers: this.headers });
  }

  // Non-conformités
  getNonConformites(): Observable<NonConformite[]> {
    return this.http.get<NonConformite[]>(`${API_URL}/non-conformites`, { headers: this.headers });
  }

  // Indices satellites
  getIndicesSatellite(): Observable<IndiceSatellite[]> {
    return this.http.get<IndiceSatellite[]>(`${API_URL}/satellite/indices`, { headers: this.headers });
  }

  // Rapports
  generateRapport(chantierIds: number[], dateDebut: string, dateFin: string, entrepriseDestinataire?: string): Observable<Blob> {
    return this.http.post(`${API_URL}/rapports/generate`,
      { chantier_ids: chantierIds, date_debut: dateDebut, date_fin: dateFin, entreprise_destinataire: entrepriseDestinataire || 'ANDE' },
      { headers: this.headers, responseType: 'blob' });
  }

  // Users (admin)
  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${API_URL}/admin/users`, { headers: this.headers });
  }

  createUser(data: { email: string; role: string; nom?: string }): Observable<User> {
    return this.http.post<User>(`${API_URL}/auth/register`, data, { headers: this.headers });
  }

  updateUser(id: number, data: { role?: string; nom?: string }): Observable<User> {
    return this.http.patch<User>(`${API_URL}/admin/users/${id}`, data, { headers: this.headers });
  }

  deleteUser(id: number): Observable<void> {
    return this.http.delete<void>(`${API_URL}/admin/users/${id}`, { headers: this.headers });
  }

  // Chantiers (admin)
  createChantier(data: { nom: string; commune?: string; latitude?: number; longitude?: number }): Observable<Chantier> {
    return this.http.post<Chantier>(`${API_URL}/chantiers`, data, { headers: this.headers });
  }

  updateChantier(id: number, data: { nom: string; commune?: string; latitude?: number; longitude?: number }): Observable<Chantier> {
    return this.http.patch<Chantier>(`${API_URL}/chantiers/${id}`, data, { headers: this.headers });
  }

  deleteChantier(id: number): Observable<void> {
    return this.http.delete<void>(`${API_URL}/chantiers/${id}`, { headers: this.headers });
  }

  // Seuils (admin)
  getSeuils(): Observable<AlerteSeuil[]> {
    return this.http.get<AlerteSeuil[]>(`${API_URL}/admin/seuils`, { headers: this.headers });
  }

  createSeuil(data: Omit<AlerteSeuil, 'id' | 'cree_le'>): Observable<AlerteSeuil> {
    return this.http.post<AlerteSeuil>(`${API_URL}/admin/seuils`, data, { headers: this.headers });
  }

  updateSeuil(id: number, data: Omit<AlerteSeuil, 'id' | 'cree_le'>): Observable<AlerteSeuil> {
    return this.http.patch<AlerteSeuil>(`${API_URL}/admin/seuils/${id}`, data, { headers: this.headers });
  }

  deleteSeuil(id: number): Observable<void> {
    return this.http.delete<void>(`${API_URL}/admin/seuils/${id}`, { headers: this.headers });
  }

  // Modèle IA (admin)
  getModelStatus(): Observable<{ nom: string; taille_octets: number; deploye_le?: string }> {
    return this.http.get<{ nom: string; taille_octets: number; deploye_le?: string }>(`${API_URL}/admin/model`, { headers: this.headers });
  }

  uploadModel(file: File): Observable<{ message: string; nom: string; taille_octets: number; deploye_le?: string }> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<{ message: string; nom: string; taille_octets: number; deploye_le?: string }>(`${API_URL}/admin/model`, form, {
      headers: { Authorization: `Bearer ${this.auth.token}` }
    });
  }

  // Logs (admin)
  getLogs(): Observable<Journal[]> {
    return this.http.get<Journal[]>(`${API_URL}/admin/logs`, { headers: this.headers });
  }
}
