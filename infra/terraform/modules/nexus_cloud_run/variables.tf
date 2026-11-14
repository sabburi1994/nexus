variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "service_name" {
  type        = string
  description = "Cloud Run service name"
}

variable "region" {
  type        = string
  description = "GCP region"
  default     = "europe-west1"
}

variable "image" {
  type        = string
  description = "Container image repository path WITHOUT tag, e.g. europe-west1-docker.pkg.dev/<project>/<repo>/<name>"

  validation {
    condition     = !can(regex(":[^/]*$", var.image)) && !strcontains(var.image, "@")
    error_message = "image must not include a tag or digest; pass it in image_tag."
  }
}

variable "image_tag" {
  type        = string
  description = "Required image tag (for example the git SHA) or digest (sha256:...). \"latest\" is rejected so every deploy is traceable."

  validation {
    condition     = length(trimspace(var.image_tag)) > 0 && var.image_tag != "latest"
    error_message = "image_tag is required and must not be \"latest\"."
  }
}

variable "service_account_email" {
  type        = string
  description = "Runtime service account email"
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
  description = "Secret Manager secrets mounted as files at <mount_path>/<file_name> (one directory per secret)"
  default     = []
}

variable "grant_secret_access" {
  type        = bool
  description = "Grant roles/secretmanager.secretAccessor on each referenced secret (not project wide) to the runtime account"
  default     = true
}

variable "min_instances" {
  type        = number
  description = "Minimum instances (0 scales to zero)"
  default     = 0
}

variable "max_instances" {
  type        = number
  description = "Maximum instances"
  default     = 2
}

variable "cpu" {
  type        = string
  description = "CPU limit"
  default     = "1"
}

variable "memory" {
  type        = string
  description = "Memory limit"
  default     = "512Mi"
}

variable "cpu_idle" {
  type        = bool
  description = "Allocate CPU only during requests (request based billing)"
  default     = true
}

variable "startup_cpu_boost" {
  type        = bool
  description = "Extra CPU during container start up"
  default     = true
}

variable "concurrency" {
  type        = number
  description = "Maximum concurrent requests per instance"
  default     = 80
}

variable "timeout_seconds" {
  type        = number
  description = "Request timeout in seconds"
  default     = 300
}

variable "container_port" {
  type        = number
  description = "Port the container listens on"
  default     = 8080
}

variable "ingress" {
  type        = string
  description = "INGRESS_TRAFFIC_ALL, INGRESS_TRAFFIC_INTERNAL_ONLY or INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  default     = "INGRESS_TRAFFIC_ALL"
}

variable "allow_unauthenticated" {
  type        = bool
  description = "Grant roles/run.invoker to allUsers (public service)"
  default     = true
}

variable "deletion_protection" {
  type        = bool
  description = "Block terraform destroy of the service until set to false and applied"
  default     = true
}

variable "startup_probe" {
  type = object({
    path                  = optional(string)
    initial_delay_seconds = optional(number, 0)
    period_seconds        = optional(number, 5)
    timeout_seconds       = optional(number, 3)
    failure_threshold     = optional(number, 24)
  })
  description = "Startup probe: HTTP GET on path when set, otherwise a TCP check on the container port"
  default     = {}
}

variable "liveness_probe" {
  type = object({
    path                  = string
    initial_delay_seconds = optional(number, 0)
    period_seconds        = optional(number, 30)
    timeout_seconds       = optional(number, 5)
    failure_threshold     = optional(number, 3)
  })
  description = "Optional HTTP liveness probe"
  default     = null
}

variable "cloud_sql_instances" {
  type        = list(string)
  description = "Cloud SQL connection names (project:region:instance) mounted as unix sockets under /cloudsql"
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

variable "labels" {
  type        = map(string)
  description = "Labels on the service"
  default     = {}
}
