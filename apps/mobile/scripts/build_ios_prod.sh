#!/bin/bash
# Build iOS for Production
# Usage: ./scripts/build_ios_prod.sh [API_URL]
# Example: ./scripts/build_ios_prod.sh https://api.icfesleveling.com/api/v1

API_URL=$1

if [ -z "$API_URL" ]; then
    echo "ERROR: Debes proporcionar la URL de la API"
    echo "Uso: ./scripts/build_ios_prod.sh https://tu-api.com/api/v1"
    exit 1
fi

echo "Building iOS (Production)..."
echo "API URL: $API_URL"

cd "$(dirname "$0")/.."

flutter build ios --release --dart-define=API_URL=$API_URL

echo ""
echo "Build completado. Abre Xcode para archivar y subir a App Store Connect."
