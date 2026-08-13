/**
 * Configuration d'environnement lue a l'execution.
 *
 * Le tableau de bord est compile une seule fois puis distribue tel quel a
 * chaque environnement. L'URL du backend n'est donc pas gelee dans le bundle
 * mais lue au demarrage depuis `window.SIENV_CONFIG.apiUrl`, un objet injecte
 * par le fichier assets/config.js. Ce fichier est produit au moment du build
 * par la plateforme d'hebergement (Cloudflare Pages) via
 * scripts/generer_config.js, a partir de la variable API_URL du projet.
 *
 * En developpement local, config.js est absent : on retombe sur
 * http://localhost:8000, ce qui correspond a la pile Docker locale.
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
  production: false,
  apiUrl: resoudreApiUrl(),
};
