output "vm_public_ip" {
  description = "Public IP address of the Hasamex single-instance VM"
  value       = google_compute_address.hasamex_ip.address
}

output "web_url" {
  description = "Public Web URL of the Hasamex Analysis Platform"
  value       = "http://${google_compute_address.hasamex_ip.address}"
}

output "health_url" {
  description = "Health check API URL"
  value       = "http://${google_compute_address.hasamex_ip.address}/api/health"
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL PostgreSQL Instance Connection Name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "cloud_sql_ip" {
  description = "Cloud SQL PostgreSQL Public IP Address"
  value       = google_sql_database_instance.postgres.public_ip_address
}

output "service_account_email" {
  description = "Compute Engine instance service account email"
  value       = google_service_account.vm_sa.email
}
