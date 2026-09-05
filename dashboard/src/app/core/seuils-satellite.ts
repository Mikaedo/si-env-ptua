/**
 * Les seuils des quatre indices satellitaires, en un seul endroit.
 *
 * Ils viennent du tableau 5.6 du memoire, et non de Google Earth
 * Engine : GEE fournit les images et calcule les indices, il ne dit
 * jamais si une valeur est bonne ou mauvaise. Ces valeurs sont donc un
 * choix documente, que le memoire assume comme des seuils de vigilance
 * servant a hierarchiser les visites de terrain, non des seuils de
 * conformite reglementaire.
 *
 * Ils etaient auparavant recopies a treize endroits, dans le gabarit et
 * dans la classe. Deux avaient deja divergé du memoire : le NDVI
 * signalait une degradation severe sous 0,30 quand le tableau dit 0,20,
 * et le NDWI sous 0,20 quand le tableau dit 0. Les rassembler ici est
 * la seule facon de garantir que l'ecran et le document disent la meme
 * chose.
 *
 * Origine des valeurs, telle que le memoire l'expose :
 *
 *   - NDVI et NDWI reprennent les paliers admis en teledetection : sol
 *     nu sous 0,2, couvert etabli au-dela de 0,4 pour le NDVI ;
 *     changement de signe marquant le stress hydrique pour le NDWI.
 *   - NO2 et risque pluie/relief sont calibres empiriquement sur la
 *     ligne de base des chantiers, aucune norme n'etant transposable :
 *     Sentinel-5P mesure une colonne tropospherique quand les valeurs
 *     sanitaires portent sur une concentration respiree.
 */

/** Les trois etats d'un indice, du plus favorable au plus grave. */
export type EtatIndice = 'BON' | 'VIGILANCE' | 'CRITIQUE';

/** Les couleurs des trois etats, communes a toutes les jauges. */
export const COULEUR_ETAT: Record<EtatIndice, string> = {
  BON: '#10B981',
  VIGILANCE: '#F59E0B',
  CRITIQUE: '#EF4444',
};

/**
 * Le NO2 et le risque pluie se degradent quand la valeur monte ; le
 * NDVI et le NDWI quand elle descend. Le sens est donc porte par
 * l'indice, non par l'appelant.
 */
export interface SeuilIndice {
  /** Au-dela (ou en deca) duquel l'etat devient CRITIQUE. */
  critique: number;
  /** Au-dela (ou en deca) duquel l'etat devient VIGILANCE. */
  vigilance: number;
  /** true quand une valeur haute est mauvaise (NO2, risque pluie). */
  hautEstMauvais: boolean;
  /** Borne d'affichage de la jauge : la valeur qui remplit 100 %. */
  jaugeMax: number;
  /** Borne basse de la jauge. Le NDWI peut etre negatif. */
  jaugeMin: number;
}

export const SEUILS: Record<'no2' | 'ndvi' | 'ndwi' | 'pluie', SeuilIndice> = {
  // Tableau 5.6 : « > 50 µmol/m² (vigilance dès 30) ».
  no2: {
    critique: 50,
    vigilance: 30,
    hautEstMauvais: true,
    jaugeMin: 0,
    jaugeMax: 80,
  },

  // Tableau 5.6 : « < 0,4 (critique sous 0,2) ».
  ndvi: {
    critique: 0.2,
    vigilance: 0.4,
    hautEstMauvais: false,
    jaugeMin: 0,
    jaugeMax: 0.6,
  },

  // Tableau 5.6 : « < 0,3 (critique sous 0) ». Le NDWI est un indice
  // normalise : il varie de -1 a 1, et sa partie negative a un sens.
  // La jauge part donc de -0,3 et non de zero, sans quoi un stress
  // hydrique marque afficherait une barre vide.
  ndwi: {
    critique: 0,
    vigilance: 0.3,
    hautEstMauvais: false,
    jaugeMin: -0.3,
    jaugeMax: 0.5,
  },

  // Tableau 5.6 : « > 7 sur 10 (vigilance dès 4) ».
  pluie: {
    critique: 7,
    vigilance: 4,
    hautEstMauvais: true,
    jaugeMin: 0,
    jaugeMax: 10,
  },
};

/** L'etat d'une valeur au regard de son seuil. */
export function etatIndice(valeur: number, seuil: SeuilIndice): EtatIndice {
  if (seuil.hautEstMauvais) {
    if (valeur > seuil.critique) return 'CRITIQUE';
    if (valeur > seuil.vigilance) return 'VIGILANCE';
    return 'BON';
  }
  if (valeur < seuil.critique) return 'CRITIQUE';
  if (valeur < seuil.vigilance) return 'VIGILANCE';
  return 'BON';
}

/** La couleur d'une valeur, pour une jauge ou un chiffre. */
export function couleurIndice(valeur: number, seuil: SeuilIndice): string {
  return COULEUR_ETAT[etatIndice(valeur, seuil)];
}

/**
 * Le remplissage d'une jauge, en pourcentage.
 *
 * Borne a l'intervalle d'affichage : une valeur hors bornes remplit la
 * jauge ou la vide, elle ne la fait pas deborder ni passer en negatif,
 * ce qui casserait la mise en page.
 */
export function jaugeIndice(valeur: number, seuil: SeuilIndice): number {
  const etendue = seuil.jaugeMax - seuil.jaugeMin;
  const part = ((valeur - seuil.jaugeMin) / etendue) * 100;
  return Math.max(0, Math.min(100, part));
}
