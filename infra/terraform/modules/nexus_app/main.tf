/**
 * Nexus Platform Framework: GCP Application Baseline Module
 * Provisions IAM service account with Vertex AI permissions for Gemini 3.8 and Secret Manager access.
 */

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
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

variable "region" {
  type        = string
  description = "Primary GCP region"
  default     = "us-east1"
}

# Ensure core APIs are enabled
resource "google_project_service" "apis" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "compute.googleapis.com",
    "run.googleapis.com",
  ])

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# Service Account for the application runtime
resource "google_service_account" "app_sa" {
  project      = var.project_id
  account_id   = "${var.app_name}-sa"
  display_name = "Service Account for Nexus App: ${var.app_name}"
}

# Grant Vertex AI user role so the app can invoke Gemini 3.8 Flash via IAM
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.app_sa.email}"
}

# Grant Secret Manager Secret Accessor role
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.app_sa.email}"
}

output "service_account_email" {
  description = "Service account email to attach to Cloud Run or Compute VM"
  value       = google_service_account.app_sa.email
}

output "project_id" {
  description = "Project ID"
  value       = var.project_id
}
