/**
 * Nexus platform module: application baseline.
 *
 * Enables the core APIs and creates the runtime service account. Grants Vertex AI access
 * only when enable_ai is true. It no longer grants project wide Secret Manager access:
 * nexus_cloud_run and nexus_cloud_run_job grant access per secret instead.
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

variable "project_id" {
  type        = string
  description = "GCP Project ID hosting the Nexus application"
}

variable "app_name" {
  type        = string
  description = "Name of the application/service"
}

variable "account_id" {
  type        = string
  description = "Runtime service account id (6 to 30 chars). Defaults to \"<app_name>-sa\"."
  default     = null
}

variable "enable_ai" {
  type        = bool
  description = "Enable Vertex AI and grant roles/aiplatform.user to the runtime account"
  default     = true
}

variable "enable_compute_api" {
  type        = bool
  description = "Enable compute.googleapis.com (needed for VMs, not for Cloud Run). Enabling it creates the default compute service account."
  default     = true
}

variable "extra_apis" {
  type        = list(string)
  description = "Additional Google APIs to enable alongside the baseline set"
  default     = []
}

variable "region" {
  type        = string
  description = "Primary GCP region"
  default     = "europe-west1"
}

locals {
  apis = toset(concat(
    ["secretmanager.googleapis.com", "run.googleapis.com"],
    var.enable_ai ? ["aiplatform.googleapis.com"] : [],
    var.enable_compute_api ? ["compute.googleapis.com"] : [],
    var.extra_apis,
  ))
}

resource "google_project_service" "apis" {
  for_each = local.apis

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# Service Account for the application runtime
resource "google_service_account" "app_sa" {
  project      = var.project_id
  account_id   = coalesce(var.account_id, "${var.app_name}-sa")
  display_name = "Service Account for Nexus App: ${var.app_name}"
}

# Vertex AI user role so the app can invoke Gemini via IAM (only when enable_ai)
resource "google_project_iam_member" "vertex_ai_user" {
  count      = var.enable_ai ? 1 : 0
  depends_on = [google_project_service.apis]
  project    = var.project_id
  role       = "roles/aiplatform.user"
  member     = "serviceAccount:${google_service_account.app_sa.email}"
}

moved {
  from = google_project_iam_member.vertex_ai_user
  to   = google_project_iam_member.vertex_ai_user[0]
}

# The previous version granted roles/secretmanager.secretAccessor on the whole project.
# It is intentionally gone: removing it from state and config revokes that grant on the
# next apply. Grant access per secret through nexus_cloud_run / nexus_cloud_run_job.

output "service_account_email" {
  description = "Service account email to attach to Cloud Run or Compute VM"
  value       = google_service_account.app_sa.email
}

output "project_id" {
  description = "Project ID"
  value       = var.project_id
}
