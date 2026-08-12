import { Injectable, signal } from '@angular/core';

/**
 * Apparence du bouton de validation, selon la portee de l'action demandee.
 * `danger` pour une suppression definitive, `success` pour une cloture,
 * `primary` pour une prise en charge ou une action neutre.
 */
export type ConfirmVariant = 'danger' | 'primary' | 'success';

export interface ConfirmOptions {
  titre: string;
  message: string;
  /** Libelle du bouton de validation (defaut : « Confirmer »). */
  texteConfirmer?: string;
  /** Libelle du bouton d'annulation (defaut : « Annuler »). */
  texteAnnuler?: string;
  variant?: ConfirmVariant;
}

interface DemandeEnCours extends ConfirmOptions {
  resoudre: (accepte: boolean) => void;
}

/**
 * Boite de dialogue de confirmation, en remplacement du `confirm()` natif du
 * navigateur : celui-ci ne peut etre ni traduit ni mis en forme, et son rendu
 * varie d'un navigateur a l'autre.
 *
 * Usage :
 *   if (!await this.confirm.demander({ titre: '...', message: '...' })) return;
 */
@Injectable({ providedIn: 'root' })
export class ConfirmService {
  /** Demande courante, ou null si aucune boite n'est ouverte. */
  readonly demande = signal<DemandeEnCours | null>(null);

  demander(options: ConfirmOptions): Promise<boolean> {
    // Une seule boite a la fois : si une demande est deja ouverte, on la
    // refuse plutot que de l'ecraser silencieusement.
    const precedente = this.demande();
    if (precedente) precedente.resoudre(false);

    return new Promise<boolean>((resolve) => {
      this.demande.set({ ...options, resoudre: resolve });
    });
  }

  /** Appele par le composant d'affichage lorsque l'utilisateur tranche. */
  repondre(accepte: boolean) {
    const courante = this.demande();
    if (!courante) return;
    this.demande.set(null);
    courante.resoudre(accepte);
  }
}
