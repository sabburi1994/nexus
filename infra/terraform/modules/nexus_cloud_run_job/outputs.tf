output "job_name" {
  value = google_cloud_run_v2_job.job.name
}

output "job_id" {
  value = google_cloud_run_v2_job.job.id
}

output "image" {
  value = local.image_ref
}

output "invoker_service_account" {
  description = "Scheduler invoker account (null without a schedule)"
  value       = local.scheduled ? google_service_account.invoker[0].email : null
}
