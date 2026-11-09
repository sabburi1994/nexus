variable "project_id" {
  type        = string
  description = "Google Cloud Project ID"
  default     = "finhub-510316"
}

variable "region" {
  type        = string
  description = "GCP region"
  default     = "europe-west1"
}

variable "image" {
  type        = string
  description = "Container image URL"
  default     = "europe-west1-docker.pkg.dev/finhub-510316/apps/nexus-showcase:latest"
}
