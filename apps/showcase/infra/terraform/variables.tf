variable "project_id" {
  type        = string
  description = "Dedicated Google Cloud project for the Nexus showcase. Must not be shared with any other app; there is deliberately no default."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be a valid Google Cloud project id (6 to 30 chars, lowercase letters, digits, hyphens)."
  }
}

variable "region" {
  type        = string
  description = "GCP region for Cloud Run and Artifact Registry"
  default     = "europe-west1"
}

variable "service_name" {
  type        = string
  description = "Cloud Run service name"
  default     = "nexus-showcase"
}

variable "repository_id" {
  type        = string
  description = "Artifact Registry Docker repository that holds the showcase images"
  default     = "nexus-showcase"
}

variable "image_tag" {
  type        = string
  description = "Image tag to run (the git SHA that Cloud Build tagged). Required; \"latest\" is rejected by the module."
}

variable "domain_name" {
  type        = string
  description = "Custom domain to map to the service (for example the public showcase domain). Null creates no mapping."
  default     = null
}

variable "deletion_protection" {
  type        = bool
  description = "Protect the Cloud Run service from terraform destroy"
  default     = true
}
