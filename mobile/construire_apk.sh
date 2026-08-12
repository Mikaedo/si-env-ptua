#!/usr/bin/env bash
# construire_apk.sh
# -----------------
# Compile l'APK release de SI-ENV en pointant vers un backend distant.
#
# Le mobile lit son URL d'API depuis kApiBaseUrl (constants.dart), lui-meme
# lu depuis --dart-define=API_URL au build. Sans variable, il retombe sur
# http://127.0.0.1:8000 pour l'usage local avec `adb reverse`.
#
# Utilisation :
#   API_URL=https://votre-user-si-env-backend.hf.space ./construire_apk.sh
#
# Sans argument :
#   ./construire_apk.sh
# → APK debug local (adb reverse), meme comportement qu'avant.

set -euo pipefail
cd "$(dirname "$0")"

if [ -n "${API_URL:-}" ]; then
    echo "→ Compilation avec API_URL=$API_URL"
    flutter build apk --release --dart-define=API_URL="$API_URL"
    sortie="build/app/outputs/flutter-apk/app-release.apk"
else
    echo "→ Compilation locale (API_URL = defaut, http://127.0.0.1:8000)"
    flutter build apk --debug
    sortie="build/app/outputs/flutter-apk/app-debug.apk"
fi

echo "✓ APK genere : $sortie"
ls -lh "$sortie" | awk '{print "  taille :", $5}'
