# Terraform remote state configured in Google Cloud Storage
terraform {
  backend "gcs" {
    bucket = "hasamex-tfstate-gen-lang-client-0072932240"
    prefix = "hasamex/prod"
  }
}
