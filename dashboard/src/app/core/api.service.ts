import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Signalement, Chantier, Alerte, Plainte, NonConformite, IndiceSatellite, User, AlerteSeuil, Journal, TransmissionRapport, ActionCorrective } from './models';
import { AuthService } from './auth.service';

import { environment } from '../../environments/environment';
const API_URL = environment.apiUrl;

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

  // Prise en charge avec une vraie procedure : la description et l'echeance
  // de l'action corrective sont enregistrees, et le signalement passe en
  // meme temps « en cours » cote serveur.
  ajouterActionCorrective(id: number, description: string, echeance: string | null): Observable<ActionCorrective> {
    return this.http.post<ActionCorrective>(`${API_URL}/signalements/${id}/action`,
      { description, echeance }, { headers: this.headers });
  }

  retournerAgent(id: number, motif: string): Observable<Signalement> {
    return this.http.post<Signalement>(`${API_URL}/signalements/${id}/retour`,
      { motif }, { headers: this.headers });
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

  ajouterActionPlainte(id: number, description: string, echeance: string | null): Observable<ActionCorrective> {
    return this.http.post<ActionCorrective>(`${API_URL}/plaintes/${id}/action`,
      { description, echeance }, { headers: this.headers });
  }

  // Non-conformités
  // ── Non-conformites (BF-09) ──────────────────────────────────────
  //
  // L'ecart constate lors du controle contradictoire. Il se distingue
  // de l'action corrective : celle-ci dit ce qu'il faut faire, l'ecart
  // dit ce qui n'est pas conforme, et se leve quand la mise en
  // conformite est constatee.

  /** Les ecarts consignes sur un signalement. */
  getNonConformitesDuSignalement(
      signalementId: number): Observable<NonConformite[]> {
    return this.http.get<NonConformite[]>(
      `${API_URL}/signalements/${signalementId}/non-conformites`,
      { headers: this.headers });
  }

  /** Consigne un ecart. Reserve a l'Expert HSE et au Specialiste. */
  ajouterNonConformite(signalementId: number, description: string,
                       severite: string): Observable<NonConformite> {
    return this.http.post<NonConformite>(
      `${API_URL}/signalements/${signalementId}/non-conformites`,
      { description, severite }, { headers: this.headers });
  }

  /** Leve un ecart, la mise en conformite ayant ete constatee. */
  resoudreNonConformite(id: number): Observable<NonConformite> {
    return this.http.patch<NonConformite>(
      `${API_URL}/signalements/non-conformites/${id}/resoudre`,
      {}, { headers: this.headers });
  }

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

  /**
   * Adresse formellement le rapport à l'organisme retenu.
   *
   * Distinct du téléchargement : celui-ci sert à consulter, celui-là engage
   * l'AGEROUTE et laisse une trace datée dans l'historique des remises.
   * L'adresse peut rester vide, l'adresse institutionnelle de l'organisme
   * étant alors utilisée.
   */
  transmettreRapport(chantierIds: number[], dateDebut: string, dateFin: string,
                     organisme: string, destinataireEmail?: string): Observable<TransmissionRapport> {
    return this.http.post<TransmissionRapport>(`${API_URL}/rapports/transmettre`, {
      chantier_ids: chantierIds,
      date_debut: dateDebut,
      date_fin: dateFin,
      entreprise_destinataire: organisme,
      destinataire_email: destinataireEmail || null,
    }, { headers: this.headers });
  }

  getTransmissions(): Observable<TransmissionRapport[]> {
    return this.http.get<TransmissionRapport[]>(`${API_URL}/rapports/transmissions`, { headers: this.headers });
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

  // Modèle IA (admin) : un statut par type de modèle (detection, classification).
  getModelStatus(): Observable<Record<string, { disponible: boolean; version: number; taille_octets: number; deploye_le?: string }>> {
    return this.http.get<Record<string, { disponible: boolean; version: number; taille_octets: number; deploye_le?: string }>>(`${API_URL}/admin/model`, { headers: this.headers });
  }

  uploadModel(typeModele: 'detection' | 'classification', file: File): Observable<{ message: string; type_modele: string; disponible: boolean; version: number; taille_octets: number; deploye_le?: string }> {
    const form = new FormData();
    form.append('type_modele', typeModele);
    form.append('file', file);
    return this.http.post<{ message: string; type_modele: string; disponible: boolean; version: number; taille_octets: number; deploye_le?: string }>(`${API_URL}/admin/model`, form, {
      headers: { Authorization: `Bearer ${this.auth.token}` }
    });
  }

  // Logs (admin)
  getLogs(): Observable<Journal[]> {
    return this.http.get<Journal[]>(`${API_URL}/admin/logs`, { headers: this.headers });
  }
}
