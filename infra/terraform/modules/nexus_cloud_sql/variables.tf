variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "instance_name" {
  type        = string
  description = "Cloud SQL instance name"
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "database_version" {
  type    = string
  default = "POSTGRES_16"
}

variable "tier" {
  type        = string
  description = "Machine tier (db-f1-micro is the cheapest shared core tier)"
  default     = "db-f1-micro"
}

variable "edition" {
  type    = string
  default = "ENTERPRISE"
}

variable "availability_type" {
  type        = string
  description = "ZONAL or REGIONAL (REGIONAL doubles the cost)"
  default     = "ZONAL"
}

variable "disk_type" {
  type    = string
  default = "PD_SSD"
}

variable "disk_size_gb" {
  type    = number
  default = 10
}

variable "deletion_protection" {
  type        = bool
  description = "Terraform and API level deletion protection"
  default     = true
}

variable "backup_start_time" {
  type        = string
  description = "UTC HH:MM for the daily backup"
  default     = "02:00"
}

variable "retained_backups" {
  type    = number
  default = 7
}

variable "transaction_log_retention_days" {
  type    = number
  default = 7
}

variable "private_network" {
  type        = string
  description = "VPC self link for private IP. Null keeps a public IP with no authorized networks (socket connector only)."
  default     = null
}

variable "maintenance_day" {
  type        = number
  description = "1 (Monday) to 7 (Sunday)"
  default     = 7
}

variable "maintenance_hour" {
  type    = number
  default = 3
}

variable "database_flags" {
  type    = map(string)
  default = {}
}

variable "labels" {
  type    = map(string)
  default = {}
}

variable "databases" {
  type        = list(string)
  description = "Databases to create"
  default     = []
}

variable "users" {
  type = map(object({
    password_secret_id      = string
    password_secret_project = optional(string)
    password_secret_version = optional(string, "latest")
    password_wo_version     = optional(number, 1)
  }))
  description = <<-EOT
    Built in database users keyed by user name. The password is read from the Secret Manager
    secret at apply time and never stored in state. Bump password_wo_version after adding a new
    secret version to push the new password.
  EOT
  default     = {}
}

variable "client_members" {
  type        = map(string)
  description = "Static key => IAM member (for example \"serviceAccount:app@p.iam.gserviceaccount.com\") granted roles/cloudsql.client"
  default     = {}
}
