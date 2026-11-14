"""Nexus IT Pack: fixed templates for the files that deploy a generated app.

The model decides what varies between apps (the compose file, whether the service calls
Vertex AI, which runtime secrets it reads). Everything that encodes platform policy is
rendered here from fixed templates instead of being written by the model:

* ``backend/Dockerfile``: non root user, listens on 8080.
* ``backend/requirements.txt`` and ``backend/pyproject.toml``: published package names.
* ``frontend/package.json``: published ``@nexus-agent-framework/*`` packages.
* ``infra/terraform/main.tf`` and ``variables.tf``: call the ``nexus_app`` and
  ``nexus_cloud_run`` platform modules (min 0, max 2 instances, request based CPU,
  required image tag, per secret IAM, Vertex AI grant only when needed).
* ``scripts/deploy.sh``: a local deploy script (no CI workflow).
"""

from __future__ import annotations

import re

from nexus import __version__

FRAMEWORK_PACKAGE = "nexus-agent-framework"
UI_PACKAGE = "@nexus-agent-framework/ui"
CONTRACTS_PACKAGE = "@nexus-agent-framework/contracts"
UI_VERSION_RANGE = "^0.2.0"
CONTRACTS_VERSION_RANGE = "^1.0.3"

MODULES_REPOSITORY = "git::https://github.com/sabburi1994/nexus.git//infra/terraform/modules"
CONTAINER_PORT = 8080

_SLUG_MAX = 40
_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]{0,62}$")


def framework_version_floor() -> str:
    """Lowest framework version a generated app accepts: the release that generated it."""
    return __version__


def backend_runtime_dependencies() -> list[str]:
    """Runtime dependencies of a generated backend (single source for pyproject and requirements)."""
    return [
        f"{FRAMEWORK_PACKAGE}>={framework_version_floor()}",
        "uvicorn>=0.30.0",
    ]


def backend_dev_dependencies() -> list[str]:
    """Test dependencies of a generated backend."""
    return [
        "pytest>=8.0.0",
        "pytest-asyncio>=0.23.0",
        "httpx>=0.27.0",
    ]


def service_slug(app_name: str) -> str:
    """Normalize a model supplied app name into a safe Cloud Run / Terraform identifier.

    Lowercase letters, digits and dashes, starting with a letter, at most 40 characters.
    """
    slug = re.sub(r"[^a-z0-9-]+", "-", app_name.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if not slug or not slug[0].isalpha():
        slug = f"app-{slug}" if slug else "nexus-app"
    return slug[:_SLUG_MAX].rstrip("-")


def runtime_account_id(app_name: str) -> str:
    """Runtime service account id: 6 to 30 characters, starts with a letter."""
    return f"{service_slug(app_name)[:22].rstrip('-')}-run-sa"


def runtime_secret_env_names(secrets: list[str]) -> list[str]:
    """Keep the secret names that are valid environment variable names, upper cased, deduplicated."""
    seen: list[str] = []
    for raw in secrets:
        name = re.sub(r"[^A-Za-z0-9_]+", "_", raw.strip()).upper().strip("_")
        if _ENV_NAME.match(name) and name not in seen:
            seen.append(name)
    return seen


def secret_id_for(app_name: str, env_name: str) -> str:
    """Secret Manager id for one runtime secret of an app."""
    return f"{service_slug(app_name)}-{env_name.lower().replace('_', '-')}"


def render_backend_pyproject(app_name: str, title: str) -> str:
    """``backend/pyproject.toml`` for a generated app."""
    deps = "\n".join(f'    "{d}",' for d in backend_runtime_dependencies())
    dev = "\n".join(f'    "{d}",' for d in backend_dev_dependencies())
    safe_title = title.replace("\\", "").replace('"', "'")
    return f"""[project]
name = "{service_slug(app_name)}"
version = "0.1.0"
description = "{safe_title} powered by Nexus Platform Framework"
requires-python = ">=3.11"
dependencies = [
{deps}
]

[project.optional-dependencies]
dev = [
{dev}
]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
asyncio_mode = "auto"
"""


def render_backend_requirements() -> str:
    """``backend/requirements.txt``: what the container installs."""
    return "\n".join(backend_runtime_dependencies()) + "\n"


def render_dockerfile() -> str:
    """``backend/Dockerfile``: slim Python image, non root runtime user, port 8080."""
    return f"""FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1 \\
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Unprivileged runtime user with a fixed uid.
RUN groupadd --system --gid 10001 app \\
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

# Dependencies and source are installed as root and stay read only for the runtime user.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/

USER 10001:10001

EXPOSE {CONTAINER_PORT}

CMD ["uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "{CONTAINER_PORT}"]
"""


def render_dockerignore() -> str:
    """``backend/.dockerignore``: keep tests, caches and local env files out of the image."""
    return "\n".join(
        [
            "tests/",
            "**/__pycache__/",
            "**/*.pyc",
            ".pytest_cache/",
            ".venv/",
            ".env",
            ".env.*",
            "",
        ]
    )


def render_frontend_package_json(app_name: str) -> str:
    """``frontend/package.json`` using the published npm packages."""
    return f"""{{
  "name": "{service_slug(app_name)}-web",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "{UI_PACKAGE}": "{UI_VERSION_RANGE}",
    "{CONTRACTS_PACKAGE}": "{CONTRACTS_VERSION_RANGE}",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  }},
  "devDependencies": {{
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "tailwindcss": "^3.4.4",
    "typescript": "^5.4.5",
    "vite": "^5.3.1"
  }}
}}
"""


def render_terraform_main(
    app_name: str,
    needs_vertex_ai: bool,
    runtime_secrets: list[str],
    modules_ref: str | None = None,
) -> str:
    """``infra/terraform/main.tf`` built on the ``nexus_app`` and ``nexus_cloud_run`` modules.

    ``modules_ref`` is the git ref of this repository the module sources are pinned to
    (defaults to the tag of the running framework version).
    """
    ref = modules_ref or f"v{__version__}"
    env_names = runtime_secret_env_names(runtime_secrets)
    secret_ids = [secret_id_for(app_name, n) for n in env_names]

    if env_names:
        id_list = ", ".join(f'"{s}"' for s in secret_ids)
        secrets_block = f"""
# Runtime secrets. Terraform creates the empty secrets; add a version to each one
# (gcloud secrets versions add <id> --data-file=-) before the first full apply.
resource "google_secret_manager_secret" "runtime" {{
  for_each = toset([{id_list}])

  project   = var.project_id
  secret_id = each.key
  replication {{
    auto {{}}
  }}
  depends_on = [module.app]
}}
"""
        entries = "\n".join(
            f'    {{ env_name = "{n}", secret_id = google_secret_manager_secret.runtime["{s}"].secret_id, '
            f'version_id = "latest" }},'
            for n, s in zip(env_names, secret_ids, strict=True)
        )
        secrets_arg = (
            f"\n  # Access is granted on each of these secrets only, not project wide.\n  secrets = [\n{entries}\n  ]\n"
        )
    else:
        secrets_block = ""
        secrets_arg = ""

    return f"""# Generated by Nexus {__version__} from the platform template.
# Cloud Run v2, scale to zero (max 2 instances), CPU billed per request, image tagged with the git SHA.

terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = ">= 6.0.0"
    }}
  }}
}}

provider "google" {{
  project = var.project_id
  region  = var.region
}}

locals {{
  image = "${{var.region}}-docker.pkg.dev/${{var.project_id}}/${{var.repository_id}}/${{var.service_name}}"
}}

# APIs and the runtime service account. Vertex AI is enabled and granted only when the app calls it.
module "app" {{
  source             = "{MODULES_REPOSITORY}/nexus_app?ref={ref}"
  project_id         = var.project_id
  app_name           = var.service_name
  account_id         = "{runtime_account_id(app_name)}"
  region             = var.region
  enable_ai          = {"true" if needs_vertex_ai else "false"}
  enable_compute_api = false
  extra_apis         = ["artifactregistry.googleapis.com"]
}}

resource "google_artifact_registry_repository" "containers" {{
  project       = var.project_id
  location      = var.region
  repository_id = var.repository_id
  format        = "DOCKER"
  depends_on    = [module.app]
}}
{secrets_block}
module "service" {{
  source                = "{MODULES_REPOSITORY}/nexus_cloud_run?ref={ref}"
  project_id            = var.project_id
  service_name          = var.service_name
  region                = var.region
  image                 = local.image
  image_tag             = var.image_tag
  service_account_email = module.app.service_account_email
  container_port        = {CONTAINER_PORT}
  min_instances         = 0
  max_instances         = 2
  cpu_idle              = true
  startup_probe         = {{ path = "/health" }}
{secrets_arg}
  depends_on = [google_artifact_registry_repository.containers]
}}

output "service_url" {{
  value = module.service.service_url
}}

output "image" {{
  value = module.service.image
}}
"""


def render_terraform_variables(app_name: str) -> str:
    """``infra/terraform/variables.tf``: ``image_tag`` has no default and rejects ``latest``."""
    return f"""variable "project_id" {{
  type        = string
  description = "GCP project id"
}}

variable "region" {{
  type        = string
  description = "GCP region"
  default     = "europe-west1"
}}

variable "service_name" {{
  type        = string
  description = "Cloud Run service name"
  default     = "{service_slug(app_name)}"
}}

variable "repository_id" {{
  type        = string
  description = "Artifact Registry repository for the container image"
  default     = "containers"
}}

variable "image_tag" {{
  type        = string
  description = "Image tag to deploy: the git SHA of the commit the image was built from"

  validation {{
    condition     = length(trimspace(var.image_tag)) > 0 && var.image_tag != "latest"
    error_message = "image_tag is required and must not be \\"latest\\"."
  }}
}}
"""


def render_deploy_script(app_name: str) -> str:
    """``scripts/deploy.sh``: build, push and deploy from a clean local checkout."""
    slug = service_slug(app_name)
    return f"""#!/usr/bin/env bash
# Deploy {slug} to Cloud Run from a clean local checkout (no CI workflow).
#
#   PROJECT_ID=<project> ./scripts/deploy.sh
#
# Needs: gcloud (authenticated), docker, terraform, git. The image is tagged with the git SHA
# of HEAD, so uncommitted changes are refused. Terraform asks before it changes anything.
set -euo pipefail

: "${{PROJECT_ID:?set PROJECT_ID to the target GCP project}}"
REGION="${{REGION:-europe-west1}}"
SERVICE="{slug}"
REPOSITORY="${{REPOSITORY:-containers}}"

cd "$(dirname "$0")/.."

if [ -n "$(git status --porcelain)" ]; then
  echo "Working tree has uncommitted changes; commit first so the image tag matches the code." >&2
  exit 1
fi
TAG="$(git rev-parse --short=12 HEAD)"
IMAGE="${{REGION}}-docker.pkg.dev/${{PROJECT_ID}}/${{REPOSITORY}}/${{SERVICE}}"

TF_VARS=(-var "project_id=${{PROJECT_ID}}" -var "region=${{REGION}}" -var "repository_id=${{REPOSITORY}}" -var "image_tag=${{TAG}}")

terraform -chdir=infra/terraform init -input=false

# 1. Foundation first: APIs, runtime service account and the image registry.
terraform -chdir=infra/terraform apply -input=false "${{TF_VARS[@]}}" \\
  -target=module.app -target=google_artifact_registry_repository.containers

# 2. Build and push the image tagged with the git SHA.
gcloud auth configure-docker "${{REGION}}-docker.pkg.dev" --quiet
docker build -t "${{IMAGE}}:${{TAG}}" backend
docker push "${{IMAGE}}:${{TAG}}"

# 3. Everything else, including the Cloud Run revision for this tag.
terraform -chdir=infra/terraform apply -input=false "${{TF_VARS[@]}}"

terraform -chdir=infra/terraform output service_url
"""
