variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "job_name" {
  type        = string
  description = "Cloud Run job name"
}

variable "region" {
  type        = string
  description = "GCP region (also used for Cloud Scheduler)"
  default     = "europe-west1"
}

variable "image" {
  type        = string
  description = "Container image repository path WITHOUT tag"

  validation {
    condition     = !can(regex(":[^/]*$", var.image)) && !strcontains(var.image, "@")
    error_message = "image must not include a tag or digest; pass it in image_tag."
  }
}

variable "image_tag" {
  type        = string
  description = "Required image tag (for example the git SHA) or digest (sha256:...); \"latest\" is rejected"

  validation {
    condition     = length(trimspace(var.image_tag)) > 0 && var.image_tag != "latest"
    error_message = "image_tag is required and must not be \"latest\"."
  }
}

variable "service_account_email" {
  type        = string
  description = "Service account the job runs as"
}

variable "command" {
  type        = list(string)
  description = "Container entrypoint override (null keeps the image default)"
  default     = null
}

variable "args" {
  type        = list(string)
  description = "Container arguments (null keeps the image default)"
  default     = null
}

variable "env_vars" {
  type        = map(string)
  description = "Plain environment variables"
  default     = {}
}

variable "secrets" {
  type = list(object({
    env_name   = string
    secret_id  = string
    version_id = string
  }))
  description = "Secret Manager secrets exposed as environment variables"
  default     = []
}

variable "secret_files" {
  type = list(object({
    secret_id  = string
    mount_path = string
    file_name  = optional(string, "secret")
    version_id = optional(string, "latest")
  }))
  description = "Secret Manager secrets mounted as files"
  default     = []
}

variable "grant_secret_access" {
  type        = bool
  description = "Grant roles/secretmanager.secretAccessor on each referenced secret to the job account"
  default     = true
}

variable "cpu" {
  type    = string
  default = "1"
}

variable "memory" {
  type    = string
  default = "512Mi"
}

variable "task_count" {
  type    = number
  default = 1
}

variable "parallelism" {
  type    = number
  default = 1
}

variable "max_retries" {
  type    = number
  default = 1
}

variable "timeout_seconds" {
  type        = number
  description = "Per task timeout in seconds"
  default     = 600
}

variable "cloud_sql_instances" {
  type        = list(string)
  description = "Cloud SQL connection names mounted under /cloudsql"
  default     = []
}

variable "vpc_egress" {
  type = object({
    network    = string
    subnetwork = string
    egress     = optional(string, "PRIVATE_RANGES_ONLY")
    tags       = optional(list(string), [])
  })
  description = "Optional Direct VPC egress"
  default     = null
}

variable "deletion_protection" {
  type    = bool
  default = true
}

variable "labels" {
  type    = map(string)
  default = {}
}

variable "schedule" {
  type        = string
  description = "Optional cron schedule (for example \"0 3 * * *\"). Null means no Cloud Scheduler trigger."
  default     = null
}

variable "schedule_time_zone" {
  type    = string
  default = "Europe/Amsterdam"
}

variable "invoker_account_id" {
  type        = string
  description = "Account id for the scheduler invoker (defaults to \"<job_name>-invoker\", truncated to 30 chars)"
  default     = null
}
