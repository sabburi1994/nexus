#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${1:-finhub-510316}"
REGION="${2:-europe-west1}"
SERVICE="${3:-nexus-showcase}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
WHEELS_DIR="$SCRIPT_DIR/backend/wheels"

mkdir -p "$WHEELS_DIR"

if [[ ! -f "$ROOT_DIR/dist/nexus_framework-0.1.0-py3-none-any.whl" ]]; then
    echo "Building wheel from $ROOT_DIR..."
    python3 -m build "$ROOT_DIR"
fi

cp "$ROOT_DIR/dist/nexus_framework-0.1.0-py3-none-any.whl" "$WHEELS_DIR/"

echo "==> Deploying Nexus Showcase to Google Cloud Run ($PROJECT_ID, $REGION)..."
gcloud run deploy "$SERVICE" \
    --source "$SCRIPT_DIR/backend" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --port 8080 \
    --allow-unauthenticated \
    --quiet \
    --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,GEMINI_MODEL=gemini-3.8-flash"
