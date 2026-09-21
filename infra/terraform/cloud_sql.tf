resource "random_id" "db_suffix" {
  byte_length = 4
}

# Cloud SQL PostgreSQL Instance (db-f1-micro: minimal cost)
resource "google_sql_database_instance" "postgres" {
  name             = "hasamex-pg-${random_id.db_suffix.hex}"
  database_version = "POSTGRES_16"
  region           = var.region

  deletion_protection = false

  settings {
    edition           = "ENTERPRISE"
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_SSD"

    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
        name  = "hasamex-vm-public-ip"
        value = google_compute_address.hasamex_ip.address
      }
    }

    backup_configuration {
      enabled    = false # Keep minimal and inexpensive
    }
  }

  depends_on = [
    google_project_service.services,
    google_compute_address.hasamex_ip
  ]
}

# Database
resource "google_sql_database" "hasamex" {
  name     = "hasamex"
  instance = google_sql_database_instance.postgres.name
}

# Database User
resource "google_sql_user" "hasamex_user" {
  name     = "hasamex_app"
  instance = google_sql_database_instance.postgres.name
  password = local.effective_db_password
}
