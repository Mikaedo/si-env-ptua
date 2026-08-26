export interface User {
  id: number;
  nom: string;
  email: string;
  role: 'ADMIN' | 'SPEC_ENV' | 'SPEC_PAR' | 'RESP_ENV' | 'EXPERT_HSE'
      | 'ANDE' | 'BAD' | 'PLAIGNANT';
  premiere_connexion: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  premiere_connexion: boolean;
  role: string;
}

export interface Chantier {
  id: number;
  nom: string;
  commune: string;
  geom?: {
    type: string;
    coordinates: [number, number];
  };
}

export type Criticite = 'FAIBLE' | 'MODERE' | 'ELEVE';
export type StatutSignalement = 'NOUVEAU' | 'EN_TRAITEMENT' | 'CLOTURE' | 'REJETE' | 'PENDING_SYNC';

export interface Signalement {
  id: number;
  uuid_mobile: string;
  type_nuisance: string;
  description: string | null;
  criticite: Criticite;
  criticite_ia?: Criticite | null;
  confiance_ia?: number | null;
  gps_source: string;
  statut: StatutSignalement;
  cree_le: string;
  auteur_id?: number | null;
  chantier_id?: number | null;
  geom?: {
    type: string;
    coordinates: [number, number];
  } | null;
  auteur?: { id: number; nom: string | null; email: string } | null;
  chantier?: { id: number; nom: string; commune: string | null } | null;
  photos?: { id: number; chemin: string; signalement_id: number }[];
  actions?: ActionCorrective[];
}

export interface ActionCorrective {
  id: number;
  description: string;
  echeance: string | null;
  cree_le: string;
  signalement_id: number;
}

export interface Alerte {
  id: number;
  message: string;
  niveau: 'INFO' | 'WARNING' | 'CRITIQUE';
  valeur?: number | null;
  cree_le: string;
  chantier_id?: number | null;
  chantier?: { id: number; nom: string; commune?: string | null } | null;
  recue: boolean;
}

export interface Plainte {
  id: number;
  nom_plaignant: string;
  contact?: string | null;
  description: string;
  statut: 'OUVERTE' | 'EN_COURS' | 'RESOLU' | 'REJETE' | string;
  cree_le: string;
  chantier_id?: number | null;
  /** MOBILE pour un dépôt citoyen, GUICHET pour un recueil par un agent. */
  canal?: string | null;
  /** Nature déclarée par le riverain : bruit, poussière, circulation... */
  categorie?: string | null;
}

export interface NonConformite {
  id: number;
  description: string;
  gravite: string;
  statut: string;
  created_at: string;
  signalement_id?: number;
}

export interface IndiceSatellite {
  id: number;
  type_indice: string;
  valeur: number;
  unite?: string;
  date_calcule: string;
  chantier?: { id: number; nom: string; commune?: string };
  statut?: string;
  tendance?: string;
  source?: string;
}

export interface AlerteSeuil {
  id: number;
  nom: string;
  indicateur: string;
  seuil: number;
  niveau: string;
  actif: boolean;
  cree_le: string;
}

export interface Journal {
  id: number;
  niveau: string;
  message: string;
  utilisateur?: string | null;
  ip_source?: string | null;
  cree_le: string;
}

/**
 * Trace d'un rapport adressé à un organisme de contrôle.
 *
 * Consulter le tableau de bord et recevoir officiellement un rapport sont deux
 * actes distincts : le second se prouve, d'où cet enregistrement daté.
 */
export interface TransmissionRapport {
  id: number;
  transmis_le: string;
  emetteur_email: string;
  destinataire_email: string;
  organisme?: string | null;
  periode_debut?: string | null;
  periode_fin?: string | null;
  nom_fichier?: string | null;
  taille_octets?: number | null;
  succes: boolean;
}
