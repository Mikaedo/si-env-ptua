/**
 * Configuration de développement (valeur par défaut).
 *
 * L'adresse de l'API était auparavant codée en dur dans quatre fichiers
 * distincts. Un déploiement obligeait donc à les modifier un par un, et le
 * tableau de bord publié appelait le « localhost » du visiteur plutôt que le
 * serveur. Elle est désormais centralisée ici.
 */
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
};
