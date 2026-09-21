locals {
  required_services = [
    "compute.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "generativelanguage.googleapis.com",
    "servicenetworking.googleapis.com",
  ]
}

resource "google_project_service" "services" {
  for_each                   = toset(local.required_services)
  project                    = var.project_id
  service                    = each.key
  disable_dependent_services = false
  disable_on_destroy         = false
}
