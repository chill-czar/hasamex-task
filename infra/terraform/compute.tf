# Compute Engine Single-Instance VM
resource "google_compute_instance" "hasamex_vm" {
  name         = "hasamex-platform-vm"
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["hasamex-web"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      size  = 20
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"
    access_config {
      nat_ip = google_compute_address.hasamex_ip.address
    }
  }

  service_account {
    email  = google_service_account.vm_sa.email
    scopes = ["cloud-platform"]
  }

  metadata_startup_script = templatefile("${path.module}/startup.sh.tpl", {
    project_id             = var.project_id
    git_repo_url           = var.git_repo_url
    git_branch             = var.git_branch
    gemini_secret_id       = google_secret_manager_secret.gemini_api_key.secret_id
    fallback_gemini_key    = var.gemini_api_key
    db_password_secret_id  = google_secret_manager_secret.db_password.secret_id
    db_user                = google_sql_user.hasamex_user.name
    db_host                = google_sql_database_instance.postgres.public_ip_address
    db_name                = google_sql_database.hasamex.name
  })

  depends_on = [
    google_project_service.services,
    google_compute_address.hasamex_ip,
    google_sql_database_instance.postgres,
    google_sql_user.hasamex_user,
    google_secret_manager_secret_version.gemini_api_key,
    google_secret_manager_secret_version.db_password,
    google_project_iam_member.secret_accessor,
    google_project_iam_member.cloudsql_client
  ]
}
