/**
 * Nexus platform module: Cloud SQL (PostgreSQL by default).
 *
 * Point in time recovery, SSL only connections, no authorized networks (connect through the
 * Cloud Run Cloud SQL socket), deletion protection at both the Terraform and the API level.
 * User passwords are read from Secret Manager through an ephemeral resource and written with
 * write only attributes, so they never land in the Terraform state or plan.
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

resource "google_project_service" "sqladmin" {
  project            = var.project_id
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_sql_database_instance" "instance" {
  project             = var.project_id
  name                = var.instance_name
  region              = var.region
  database_version    = var.database_version
  deletion_protection = var.deletion_protection

  settings {
    tier                        = var.tier
    edition                     = var.edition
    availability_type           = var.availability_type
    disk_type                   = var.disk_type
    disk_size                   = var.disk_size_gb
    disk_autoresize             = true
    deletion_protection_enabled = var.deletion_protection
    user_labels                 = var.labels

    backup_configuration {
      enabled                        = true
      start_time                     = var.backup_start_time
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = var.transaction_log_retention_days

      backup_retention_settings {
        retained_backups = var.retained_backups
        retention_unit   = "COUNT"
      }
    }

    ip_configuration {
      ipv4_enabled    = var.private_network == null
      private_network = var.private_network
      ssl_mode        = "ENCRYPTED_ONLY"
    }

    maintenance_window {
      day          = var.maintenance_day
      hour         = var.maintenance_hour
      update_track = "stable"
    }

    dynamic "database_flags" {
      for_each = var.database_flags
      content {
        name  = database_flags.key
        value = database_flags.value
      }
    }
  }

  depends_on = [google_project_service.sqladmin]
}

resource "google_sql_database" "databases" {
  for_each = toset(var.databases)
  project  = var.project_id
  instance = google_sql_database_instance.instance.name
  name     = each.value
}

ephemeral "google_secret_manager_secret_version" "user_password" {
  for_each = var.users
  project  = coalesce(each.value.password_secret_project, var.project_id)
  secret   = each.value.password_secret_id
  version  = each.value.password_secret_version
}

resource "google_sql_user" "users" {
  for_each            = var.users
  project             = var.project_id
  instance            = google_sql_database_instance.instance.name
  name                = each.key
  password_wo         = ephemeral.google_secret_manager_secret_version.user_password[each.key].secret_data
  password_wo_version = each.value.password_wo_version
}

# Lets the listed identities (for example Cloud Run runtime accounts) open Cloud SQL connections.
resource "google_project_iam_member" "clients" {
  for_each = var.client_members
  project  = var.project_id
  role     = "roles/cloudsql.client"
  member   = each.value
}
