/**
 * Example: one app on the Nexus platform modules.
 * Cloud Run service + migration job (with a nightly trigger) + Cloud SQL, secrets granted per secret.
 * Validate with: terraform init -backend=false && terraform validate
 */

terraform {
  required_version = ">= 1.11.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 7.0.0"
    }
  }
}

variable "project_id" {
  type = string
}

variable "image_tag" {
  type        = string
  description = "Git SHA of the image to deploy"
}

locals {
  region = "europe-west1"
  image  = "${local.region}-docker.pkg.dev/${var.project_id}/containers/example-app"
}

provider "google" {
  project = var.project_id
  region  = local.region
}

module "app" {
  source     = "../../../infra/terraform/modules/nexus_app"
  project_id = var.project_id
  app_name   = "example-app"
  enable_ai  = false
  # Cloud Run only: no VMs, so skip the compute API and its default service account.
  enable_compute_api = false
}

resource "google_secret_manager_secret" "db_password" {
  project   = var.project_id
  secret_id = "example-app-db-password"
  replication {
    auto {}
  }
}

module "db" {
  source        = "../../../infra/terraform/modules/nexus_cloud_sql"
  project_id    = var.project_id
  instance_name = "example-db"
  databases     = ["example"]
  users = {
    example = { password_secret_id = google_secret_manager_secret.db_password.secret_id }
  }
  client_members = {
    app = "serviceAccount:${module.app.service_account_email}"
  }
}

module "service" {
  source                = "../../../infra/terraform/modules/nexus_cloud_run"
  project_id            = var.project_id
  service_name          = "example-app"
  image                 = local.image
  image_tag             = var.image_tag
  service_account_email = module.app.service_account_email
  cloud_sql_instances   = [module.db.connection_name]
  env_vars = {
    DB_SOCKET = "/cloudsql/${module.db.connection_name}"
  }
  secrets = [
    { env_name = "DB_PASSWORD", secret_id = google_secret_manager_secret.db_password.secret_id, version_id = "latest" },
  ]
  startup_probe  = { path = "/health" }
  liveness_probe = { path = "/health" }
}

module "migrate" {
  source                = "../../../infra/terraform/modules/nexus_cloud_run_job"
  project_id            = var.project_id
  job_name              = "example-app-migrate"
  image                 = local.image
  image_tag             = var.image_tag
  service_account_email = module.app.service_account_email
  args                  = ["alembic", "upgrade", "head"]
  cloud_sql_instances   = [module.db.connection_name]
  secret_files = [
    { secret_id = google_secret_manager_secret.db_password.secret_id, mount_path = "/secrets/db" },
  ]
  schedule = "0 3 * * *"
}

output "url" {
  value = module.service.service_url
}
