/**
 * Nexus platform module: Cloud Run (v2) job with an optional Cloud Scheduler trigger.
 *
 * Typical uses: database migrations (run once per deploy) and periodic batch work.
 * Secrets are granted per secret to the job's service account. When a schedule is set,
 * a dedicated invoker service account is created and allowed to run only this job.
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

locals {
  image_ref = startswith(var.image_tag, "sha256:") ? "${var.image}@${var.image_tag}" : "${var.image}:${var.image_tag}"

  secret_ids = toset(concat(
    [for s in var.secrets : s.secret_id],
    [for f in var.secret_files : f.secret_id],
  ))

  scheduled = var.schedule != null
}

resource "google_cloud_run_v2_job" "job" {
  name                = var.job_name
  location            = var.region
  project             = var.project_id
  deletion_protection = var.deletion_protection
  labels              = var.labels

  template {
    task_count  = var.task_count
    parallelism = var.parallelism

    template {
      service_account = var.service_account_email
      timeout         = "${var.timeout_seconds}s"
      max_retries     = var.max_retries

      dynamic "vpc_access" {
        for_each = var.vpc_egress == null ? [] : [var.vpc_egress]
        content {
          egress = vpc_access.value.egress
          network_interfaces {
            network    = vpc_access.value.network
            subnetwork = vpc_access.value.subnetwork
            tags       = vpc_access.value.tags
          }
        }
      }

      dynamic "volumes" {
        for_each = length(var.cloud_sql_instances) > 0 ? [1] : []
        content {
          name = "cloudsql"
          cloud_sql_instance {
            instances = var.cloud_sql_instances
          }
        }
      }

      dynamic "volumes" {
        for_each = { for idx, f in var.secret_files : "secret-file-${idx}" => f }
        content {
          name = volumes.key
          secret {
            secret = volumes.value.secret_id
            items {
              version = volumes.value.version_id
              path    = volumes.value.file_name
            }
          }
        }
      }

      containers {
        image   = local.image_ref
        command = var.command
        args    = var.args

        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }

        dynamic "env" {
          for_each = var.env_vars
          content {
            name  = env.key
            value = env.value
          }
        }

        dynamic "env" {
          for_each = var.secrets
          content {
            name = env.value.env_name
            value_source {
              secret_key_ref {
                secret  = env.value.secret_id
                version = env.value.version_id
              }
            }
          }
        }

        dynamic "volume_mounts" {
          for_each = length(var.cloud_sql_instances) > 0 ? [1] : []
          content {
            name       = "cloudsql"
            mount_path = "/cloudsql"
          }
        }

        dynamic "volume_mounts" {
          for_each = { for idx, f in var.secret_files : "secret-file-${idx}" => f }
          content {
            name       = volume_mounts.key
            mount_path = volume_mounts.value.mount_path
          }
        }
      }
    }
  }
}

resource "google_secret_manager_secret_iam_member" "job_access" {
  for_each  = var.grant_secret_access ? local.secret_ids : toset([])
  project   = var.project_id
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

# Optional schedule: a dedicated invoker account that may run only this job.
resource "google_project_service" "scheduler" {
  count              = local.scheduled ? 1 : 0
  project            = var.project_id
  service            = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}

resource "google_service_account" "invoker" {
  count        = local.scheduled ? 1 : 0
  project      = var.project_id
  account_id   = coalesce(var.invoker_account_id, substr("${var.job_name}-invoker", 0, 30))
  display_name = "Cloud Scheduler invoker for job ${var.job_name}"
}

resource "google_cloud_run_v2_job_iam_member" "invoker" {
  count    = local.scheduled ? 1 : 0
  project  = var.project_id
  location = google_cloud_run_v2_job.job.location
  name     = google_cloud_run_v2_job.job.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.invoker[0].email}"
}

resource "google_cloud_scheduler_job" "trigger" {
  count            = local.scheduled ? 1 : 0
  project          = var.project_id
  region           = var.region
  name             = "${var.job_name}-trigger"
  schedule         = var.schedule
  time_zone        = var.schedule_time_zone
  attempt_deadline = "180s"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.job.name}:run"

    oauth_token {
      service_account_email = google_service_account.invoker[0].email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }

  depends_on = [google_project_service.scheduler, google_cloud_run_v2_job_iam_member.invoker]
}
