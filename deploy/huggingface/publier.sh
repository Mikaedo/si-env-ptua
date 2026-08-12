#!/usr/bin/env bash
# publier.sh
# ----------
# Prepare et pousse le backend vers Hugging Face Spaces.
#
# Hugging Face servant chaque Space depuis son propre depot git, on ne peut
# pas y pousser directement le monorepo. Ce script rassemble dans un dossier
# temporaire tout ce dont le Space a besoin, puis le pousse.
#
# Prerequis :
#   - Space cree sur huggingface.co, SDK = Docker
#   - git-lfs installe
#   - Un jeton HF avec droit write, exporte comme HF_TOKEN
#   - Variables : HF_USER (nom d'utilisateur HF), HF_SPACE (nom du Space)
#
# Utilisation :
#   HF_USER=votre-user HF_SPACE=si-env-backend HF_TOKEN=hf_... \
#     ./deploy/huggingface/publier.sh

set -euo pipefail

: "${HF_USER:?HF_USER manquant}"
: "${HF_SPACE:?HF_SPACE manquant}"
: "${HF_TOKEN:?HF_TOKEN manquant}"

racine=$(cd "$(dirname "$0")/../.." && pwd)
depot="https://$HF_USER:$HF_TOKEN@huggingface.co/spaces/$HF_USER/$HF_SPACE"

# Repertoire temporaire, nettoye a la sortie
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

echo "→ Clonage du Space depuis Hugging Face"
git clone "$depot" "$tmp/space"

cd "$tmp/space"
# On repart d'un contenu propre a chaque publication ; le suivi git conserve
# l'historique de toute facon.
find . -mindepth 1 -maxdepth 1 -not -name '.git' -exec rm -rf {} +

echo "→ Assemblage du contexte backend"
cp -r "$racine/backend/app" ./app
cp "$racine/backend/seed.py" ./seed.py
cp "$racine/backend/requirements.txt" ./requirements.txt
cp "$racine/deploy/huggingface/Dockerfile" ./Dockerfile
cp "$racine/deploy/huggingface/README.md" ./README.md

# Verrous de securite : la cle GEE ne doit jamais partir dans le depot
if [ -f app/gee-service-account.json ] || find . -name 'gee-service-account.json' | grep -q .; then
    echo "!! Une cle GEE a ete trouvee dans le contexte. Abandon." >&2
    exit 2
fi
if grep -RiE "private_key|BEGIN PRIVATE KEY" --exclude=publier.sh . >/dev/null; then
    echo "!! Un secret potentiel a ete detecte dans les fichiers a pousser. Abandon." >&2
    exit 2
fi

echo "→ Commit et push"
git add -A
git config user.email "sienv@deploy"
git config user.name  "SI-ENV Deploy"
git commit -m "Publication backend $(date -u +%Y-%m-%dT%H:%M:%SZ)" || echo "  (rien a commiter)"
git push

echo "✓ Publie sur https://huggingface.co/spaces/$HF_USER/$HF_SPACE"
echo "  API disponible a https://$HF_USER-$HF_SPACE.hf.space"
