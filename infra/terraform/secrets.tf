resource "random_password" "db_password" {
  length  = 24
  special = false
}

locals {
  effective_db_password = var.db_password != "" ? var.db_password : random_password.db_password.result
}

# Secret Manager: Gemini API Key
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "hasamex-gemini-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "gemini_api_key" {
  secret      = google_secret_manager_secret.gemini_api_key.id
  secret_data = var.gemini_api_key
}

# Secret Manager: Database Password
resource "google_secret_manager_secret" "db_password" {
  secret_id = "hasamex-db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = local.effective_db_password
}
