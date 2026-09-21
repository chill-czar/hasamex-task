# Static external IP address for Hasamex platform instance
resource "google_compute_address" "hasamex_ip" {
  name       = "hasamex-platform-ip"
  region     = var.region
  depends_on = [google_project_service.services]
}

# Firewall rule: Allow HTTP & HTTPS ingress traffic
resource "google_compute_firewall" "allow_http" {
  name    = "hasamex-allow-http"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["hasamex-web"]

  depends_on = [google_project_service.services]
}

# Firewall rule: Allow SSH ingress traffic for administrative access
resource "google_compute_firewall" "allow_ssh" {
  name    = "hasamex-allow-ssh"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["hasamex-web"]

  depends_on = [google_project_service.services]
}
