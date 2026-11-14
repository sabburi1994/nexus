output "service_url" {
  description = "The default public URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.service.uri
}

output "service_name" {
  description = "Cloud Run service name"
  value       = google_cloud_run_v2_service.service.name
}

output "service_id" {
  description = "Fully qualified service id"
  value       = google_cloud_run_v2_service.service.id
}

output "image" {
  description = "Deployed image reference"
  value       = local.image_ref
}
