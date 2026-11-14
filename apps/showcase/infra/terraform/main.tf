/**
 * Nexus showcase, alone in its own Google Cloud project.
 *
 *   * runtime service account (nexus_app module) with NO project roles: the showcase makes no
 *     server side model calls (visitors may bring their own Gemini key, sent per request);
 *   * build service account for Cloud Build, allowed to push to this app's repository only;
 *   * a dedicated Artifact Registry Docker repository with a cleanup policy;
 *   * the Cloud Run service (nexus_cloud_run module): min 0, max 2, 512Mi, CPU only during requests;
 *   * optionally the custom domain mapping.
 *
 * First apply is two step (see ../../ROLLOUT.md): foundation with -target, Cloud Build, then full apply.
 */

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. APIs and runtime identity (no Vertex AI, no Secret Manager, no compute default account).
module "nexus_base" {
  source             = "../../../../infra/terraform/modules/nexus_app"
  project_id         = var.project_id
  app_name           = var.service_name
  account_id         = "${var.service_name}-run"
  region             = var.region
  enable_ai          = false
  enable_compute_api = false
  extra_apis = [
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "logging.googleapis.com",
  ]
}

# 2. Dedicated container registry for this app only.
resource "google_artifact_registry_repository" "images" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repository_id
  format        = "DOCKER"
  description   = "Nexus showcase container images"

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }

  cleanup_policies {
    id     = "delete-old"
    action = "DELETE"
    condition {
      older_than = "2592000s"
    }
  }

  depends_on = [module.nexus_base]
}

# 3. Build identity for Cloud Build: push to this repository, write logs, read the uploaded source.
resource "google_service_account" "build" {
  project      = var.project_id
  account_id   = "${var.service_name}-build"
  display_name = "Cloud Build account for ${var.service_name}"
}

resource "google_artifact_registry_repository_iam_member" "build_push" {
  project    = var.project_id
  location   = google_artifact_registry_repository.images.location
  repository = google_artifact_registry_repository.images.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.build.email}"
}

resource "google_project_iam_member" "build_logs" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.build.email}"
}

# gcloud builds submit uploads the source tarball to gs://<project>_cloudbuild; the build reads it back.
resource "google_project_iam_member" "build_source_read" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.build.email}"
}

# 4. The public Cloud Run service.
module "cloud_run" {
  source                = "../../../../infra/terraform/modules/nexus_cloud_run"
  project_id            = var.project_id
  service_name          = var.service_name
  region                = var.region
  image                 = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}/${var.service_name}"
  image_tag             = var.image_tag
  service_account_email = module.nexus_base.service_account_email

  min_instances         = 0
  max_instances         = 2
  cpu                   = "1"
  memory                = "512Mi"
  cpu_idle              = true
  startup_cpu_boost     = true
  concurrency           = 40
  timeout_seconds       = 120
  allow_unauthenticated = true
  deletion_protection   = var.deletion_protection

  startup_probe  = { path = "/health" }
  liveness_probe = { path = "/health" }

  env_vars = {
    "GEMINI_MODEL" = "gemini-3.8-flash"
    "ENVIRONMENT"  = "production"
  }

  labels = {
    app = var.service_name
  }

  depends_on = [module.nexus_base]
}

# 5. Optional custom domain. The domain must be verified for the account that applies this.
resource "google_cloud_run_domain_mapping" "custom" {
  count    = var.domain_name == null ? 0 : 1
  project  = var.project_id
  location = var.region
  name     = var.domain_name

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = module.cloud_run.service_name
  }
}

output "service_url" {
  value = module.cloud_run.service_url
}

output "image" {
  value = module.cloud_run.image
}

output "runtime_service_account" {
  value = module.nexus_base.service_account_email
}

output "build_service_account" {
  description = "Pass to gcloud builds submit --service-account"
  value       = google_service_account.build.email
}

output "image_repository" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}

output "domain_mapping_records" {
  description = "DNS records the domain must point to (expected: CNAME ghs.googlehosted.com)"
  value       = var.domain_name == null ? [] : google_cloud_run_domain_mapping.custom[0].status[0].resource_records
}
