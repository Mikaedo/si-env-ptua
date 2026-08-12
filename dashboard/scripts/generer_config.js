// generer_config.js
// -----------------
// Emet dist/dashboard/browser/assets/config.js a partir des variables
// d'environnement de la plateforme de deploiement.
//
// Utilise par le pipeline Cloudflare Pages, apres `npm run build`.
// L'objet est expose comme `window.SIENV_CONFIG`.

const fs = require('fs');
const path = require('path');

const dist = path.join(__dirname, '..', 'dist', 'dashboard', 'browser', 'assets');
fs.mkdirSync(dist, { recursive: true });

const apiUrl = process.env.API_URL || process.env.SIENV_API_URL || '';
if (!apiUrl) {
  console.warn('!! Aucune variable API_URL definie : l\'app se rabattra sur http://localhost:8000');
}

const contenu = `window.SIENV_CONFIG = ${JSON.stringify({ apiUrl }, null, 2)};\n`;
fs.writeFileSync(path.join(dist, 'config.js'), contenu, 'utf-8');
console.log(`✓ dist/.../assets/config.js ecrit avec apiUrl = ${apiUrl || '(vide)'}`);
