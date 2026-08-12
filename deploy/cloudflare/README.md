# Dashboard sur Cloudflare Pages

Instructions pour publier le tableau de bord Angular sur Cloudflare Pages.
Gratuit et sans carte bancaire.

## 1. Créer le projet

- Aller sur **dash.cloudflare.com** → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
- Sélectionner le dépôt GitHub `SI-ENV`.

## 2. Configuration du build

| Champ | Valeur |
|---|---|
| **Framework preset** | Angular |
| **Build command** | `npm run build:cf` |
| **Build output directory** | `dist/dashboard/browser` |
| **Root directory** | `dashboard` |
| **Node version** | 20 |

## 3. Variable d'environnement

Dans **Settings → Environment variables → Production** :

| Nom | Valeur |
|---|---|
| `API_URL` | URL du Space Hugging Face, par ex. `https://votre-user-si-env-backend.hf.space` |

Cette variable est lue par `scripts/generer_config.js` au build pour
produire `assets/config.js`, consommé au démarrage du bundle Angular.

## 4. Déploiement

Chaque push sur `main` déclenche automatiquement un build. La première mise
en ligne est disponible sur `https://si-env.pages.dev` (nom à adapter au
projet créé).

## Notes

- Le fichier `public/_redirects` gère la réécriture SPA (routes profondes → `index.html`).
- Aucune clé secrète n'est exposée : la clé Supabase reste côté backend.
