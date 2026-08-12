/**
 * Configuration de production.
 *
 * L'URL de l'API n'est plus codee en dur : elle est lue au demarrage depuis
 * `window.SIENV_CONFIG.apiUrl`, un objet injecte par assets/config.js. Ce
 * fichier est produit au moment du build par la plateforme d'hebergement
 * (Cloudflare Pages) a partir des variables d'environnement du projet, ce
 * qui permet de repointer le meme bundle vers plusieurs environnements sans
 * recompiler.
 *
 * En dernier recours (config.js absent), on retombe sur l'URL de dev.
 */
declare global {
  interface Window {
    SIENV_CONFIG?: { apiUrl?: string };
  }
}

function resoudreApiUrl(): string {
  if (typeof window !== 'undefined' && window.SIENV_CONFIG?.apiUrl) {
    return window.SIENV_CONFIG.apiUrl;
  }
  return 'http://localhost:8000';
}

export const environment = {
  production: true,
  apiUrl: resoudreApiUrl(),
};
