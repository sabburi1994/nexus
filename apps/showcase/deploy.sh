#!/usr/bin/env bash
# Build the Nexus showcase image and roll it out with Terraform, in its own dedicated project.
#
# Terraform is the only path for infrastructure. This script builds the framework wheel, builds and
# pushes the image with Cloud Build (as the build service account) tagged with the git SHA, then runs
# terraform apply in infra/terraform with that tag. First time set up is described in ROLLOUT.md.
#
# Usage: ./deploy.sh <project-id> [domain-name]
# Optional environment: REGION, SERVICE, REPOSITORY, TAG, AUTO_APPROVE=1
set -euo pipefail

if [[ $# -lt 1 || -z "${1:-}" ]]; then
    echo "usage: $0 <project-id> [domain-name]" >&2
    exit 2
fi

PROJECT_ID="$1"
DOMAIN_NAME="${2:-}"
REGION="${REGION:-europe-west1}"
SERVICE="${SERVICE:-nexus-showcase}"
REPOSITORY="${REPOSITORY:-nexus-showcase}"
TAG="${TAG:-}"

BUILD_SA="${SERVICE}-build@${PROJECT_ID}.iam.gserviceaccount.com"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
WHEELS_DIR="$BACKEND_DIR/wheels"
TF_DIR="$SCRIPT_DIR/infra/terraform"

# Guard: the showcase must live alone in its project. Refuse if other Cloud Run services exist there.
OTHERS="$(gcloud run services list --project "$PROJECT_ID" --region "$REGION" --format 'value(metadata.name)' 2>/dev/null | grep -vx "$SERVICE" || true)"
if [[ -n "$OTHERS" ]]; then
    echo "Project $PROJECT_ID already runs other Cloud Run services: $OTHERS. Use a dedicated project." >&2
    exit 1
fi

if [[ -z "$TAG" ]]; then
    if [[ -n "$(git -C "$ROOT_DIR" status --porcelain)" ]]; then
        echo "Working tree has uncommitted changes; commit first or set TAG." >&2
        exit 1
    fi
    TAG="$(git -C "$ROOT_DIR" rev-parse --short=12 HEAD)"
fi
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE}:${TAG}"

echo "==> Building nexus-agent-framework wheel from $ROOT_DIR"
rm -rf "$WHEELS_DIR"
mkdir -p "$WHEELS_DIR"
python3 -m build --wheel --outdir "$WHEELS_DIR" "$ROOT_DIR"

echo "==> Building $IMAGE with Cloud Build as $BUILD_SA"
gcloud builds submit "$BACKEND_DIR" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --config "$BACKEND_DIR/cloudbuild.yaml" \
    --substitutions "_IMAGE=$IMAGE" \
    --service-account "projects/$PROJECT_ID/serviceAccounts/$BUILD_SA"

echo "==> terraform apply (image tag $TAG)"
TF_ARGS=(-input=false -var "project_id=$PROJECT_ID" -var "region=$REGION" -var "service_name=$SERVICE"
    -var "repository_id=$REPOSITORY" -var "image_tag=$TAG")
[[ -n "$DOMAIN_NAME" ]] && TF_ARGS+=(-var "domain_name=$DOMAIN_NAME")
[[ "${AUTO_APPROVE:-0}" == "1" ]] && TF_ARGS+=(-auto-approve)
terraform -chdir="$TF_DIR" init -input=false
terraform -chdir="$TF_DIR" apply "${TF_ARGS[@]}"

echo "==> Rolled out $IMAGE"
