/**
 * Nexus platform module: Cloud Run (v2) service.
 *
 * Platform defaults: scale to zero, at most 2 instances, CPU only during requests
 * (cpu_idle = true), startup CPU boost, deletion protection on, image pinned by tag.
 * Secrets are granted per secret to the runtime service account, never project wide.
 * See README.md in this folder for inputs and migration notes.
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
}

resource "google_cloud_run_v2_service" "service" {
  name                = var.service_name
  location            = var.region
  project             = var.project_id
  ingress             = var.ingress
  deletion_protection = var.deletion_protection
  labels              = var.labels

  template {
    service_account                  = var.service_account_email
    timeout                          = "${var.timeout_seconds}s"
    max_instance_request_concurrency = var.concurrency

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

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
      image = local.image_ref

      ports {
        container_port = var.container_port
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
        cpu_idle          = var.cpu_idle
        startup_cpu_boost = var.startup_cpu_boost
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

      startup_probe {
        initial_delay_seconds = var.startup_probe.initial_delay_seconds
        period_seconds        = var.startup_probe.period_seconds
        timeout_seconds       = var.startup_probe.timeout_seconds
        failure_threshold     = var.startup_probe.failure_threshold

        dynamic "http_get" {
          for_each = var.startup_probe.path == null ? [] : [var.startup_probe.path]
          content {
            path = http_get.value
            port = var.container_port
          }
        }

        dynamic "tcp_socket" {
          for_each = var.startup_probe.path == null ? [1] : []
          content {
            port = var.container_port
          }
        }
      }

      dynamic "liveness_probe" {
        for_each = var.liveness_probe == null ? [] : [var.liveness_probe]
        content {
          initial_delay_seconds = liveness_probe.value.initial_delay_seconds
          period_seconds        = liveness_probe.value.period_seconds
          timeout_seconds       = liveness_probe.value.timeout_seconds
          failure_threshold     = liveness_probe.value.failure_threshold
          http_get {
            path = liveness_probe.value.path
            port = var.container_port
          }
        }
      }
    }
  }
}

# Per secret access for the runtime account (replaces the old project wide secretAccessor grant).
resource "google_secret_manager_secret_iam_member" "runtime_access" {
  for_each  = var.grant_secret_access ? local.secret_ids : toset([])
  project   = var.project_id
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_cloud_run_service_iam_member" "public_access" {
  count    = var.allow_unauthenticated ? 1 : 0
  location = google_cloud_run_v2_service.service.location
  project  = google_cloud_run_v2_service.service.project
  service  = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Callers of the previous module version had this resource without count.
moved {
  from = google_cloud_run_service_iam_member.public_access
  to   = google_cloud_run_service_iam_member.public_access[0]
}
