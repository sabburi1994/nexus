/**
 * Nexus Platform Framework: Compute Engine VM Module
 * Deploys secure e2-micro / e2-medium instance with IAP-only SSH, custom VPC, and Docker.
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
  description = "GCP Project ID"
}

variable "vm_name" {
  type        = string
  description = "Name of the VM instance"
}

variable "region" {
  type        = string
  description = "GCP region (e.g. us-east1 for Always Free)"
  default     = "us-east1"
}

variable "zone" {
  type        = string
  description = "GCP zone"
  default     = "us-east1-b"
}

variable "machine_type" {
  type        = string
  description = "Machine type"
  default     = "e2-micro"
}

variable "service_account_email" {
  type        = string
  description = "Service account email"
}

variable "subnet_cidr" {
  type        = string
  description = "CIDR block for the custom VPC subnet"
  default     = "10.50.0.0/24"
}

resource "google_compute_network" "vpc" {
  name                    = "${var.vm_name}-vpc"
  project                 = var.project_id
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${var.vm_name}-subnet"
  project       = var.project_id
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
}

# Allow Web traffic (HTTP/HTTPS)
resource "google_compute_firewall" "allow_web" {
  name    = "${var.vm_name}-allow-web"
  project = var.project_id
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }
  allow {
    protocol = "udp"
    ports    = ["443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["nexus-web"]
}

# Allow SSH strictly via GCP Identity-Aware Proxy (IAP) CIDR
resource "google_compute_firewall" "allow_iap" {
  name    = "${var.vm_name}-allow-iap"
  project = var.project_id
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["nexus-web"]
}

resource "google_compute_instance" "vm" {
  name         = var.vm_name
  project      = var.project_id
  machine_type = var.machine_type
  zone         = var.zone
  tags         = ["nexus-web"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 30
      type  = "pd-standard"
    }
  }

  network_interface {
    network    = google_compute_network.vpc.name
    subnetwork = google_compute_subnetwork.subnet.name

    access_config {
      // Ephemeral public IP for outbound access and web traffic
    }
  }

  service_account {
    email  = var.service_account_email
    scopes = ["cloud-platform"]
  }

  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
}

output "instance_ip" {
  description = "Public IP address of the VM"
  value       = google_compute_instance.vm.network_interface[0].access_config[0].nat_ip
}
