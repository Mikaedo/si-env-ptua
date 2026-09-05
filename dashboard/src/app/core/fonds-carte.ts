/**
 * Les fonds de carte, en un seul endroit.
 *
 * Le tableau de bord tirait ses tuiles d'OpenStreetMap. Or le service
 * refuse desormais les requetes qui ne viennent pas de son propre site :
 * il repond bien 200, mais avec une image vide de cent trois octets, si
 * bien que la carte restait blanche sans qu'aucune erreur ne paraisse
 * dans la console. Le diagnostic est trompeur, et c'est ce qui l'a fait
 * passer inapercu.
 *
 * ArcGIS Online sert les deux fonds sans cle et sans restriction
 * d'origine. Le meme fournisseur porte donc le plan et l'imagerie, ce
 * qui evite qu'un seul des deux tombe.
 *
 * Ces adresses sont partagees par la carte des signalements et celle de
 * l'analyse satellitaire : les recopier a chaque page est ce qui avait
 * laisse le defaut se propager.
 */

/** Fond cartographique clair : voies, quartiers, toponymes. */
export const FOND_PLAN =
  'https://server.arcgisonline.com/ArcGIS/rest/services/' +
  'World_Street_Map/MapServer/tile/{z}/{y}/{x}';

/** Imagerie satellitaire. */
export const FOND_SATELLITE =
  'https://server.arcgisonline.com/ArcGIS/rest/services/' +
  'World_Imagery/MapServer/tile/{z}/{y}/{x}';

/** Mention d'attribution, exigee par les conditions d'ArcGIS Online. */
export const ATTRIBUTION_CARTE = '© Esri, HERE, Garmin, USGS';

/** Le zoom maximal servi par ces couches. */
export const ZOOM_MAX = 19;
