output "connection_name" {
  description = "project:region:instance, for the Cloud Run cloud_sql_instances input"
  value       = google_sql_database_instance.instance.connection_name
}

output "instance_name" {
  value = google_sql_database_instance.instance.name
}

output "databases" {
  value = [for d in google_sql_database.databases : d.name]
}
