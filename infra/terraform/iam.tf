# Dedicated Service Account for Hasamex Compute Engine VM
resource "google_service_account" "vm_sa" {
  account_id   = "hasamex-vm-sa"
  display_name = "Hasamex VM Service Account"
  description  = "Least-privilege service account running Hasamex on Compute Engine"

  depends_on = [google_project_service.services]
}

# Secret Accessor: allows VM to fetch GEMINI_API_KEY and DB password
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.vm_sa.email}"
}

# Cloud SQL Client: allows VM to connect to Cloud SQL PostgreSQL
resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.vm_sa.email}"
}

# Cloud Logging Writer
resource "google_project_iam_member" "log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.vm_sa.email}"
}

# Cloud Monitoring Metric Writer
resource "google_project_iam_member" "metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.vm_sa.email}"
}
