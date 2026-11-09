terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Base Nexus Application Platform (Service Account & Vertex AI IAM)
module "nexus_base" {
  source       = "../../../infra/terraform/modules/nexus_app"
  project_id   = var.project_id
  app_name     = "showcase"
  enable_ai    = true
  enable_secrets = true
}

# 2. Serverless Cloud Run Deployment
module "cloud_run" {
  source                = "../../../infra/terraform/modules/nexus_cloud_run"
  project_id            = var.project_id
  service_name          = "nexus-showcase"
  region                = var.region
  image                 = var.image
  service_account_email = module.nexus_base.service_account_email

  env_vars = {
    "GCP_PROJECT_ID" = var.project_id
    "GEMINI_MODEL"   = "gemini-3.8-flash"
    "ENVIRONMENT"    = "production"
  }
}

output "app_url" {
  value = module.cloud_run.service_url
}
