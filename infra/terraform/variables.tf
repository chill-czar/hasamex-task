variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
  default     = "gen-lang-client-0072932240"
}

variable "region" {
  description = "The primary Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The primary Google Cloud zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "production"
}

variable "machine_type" {
  description = "Compute Engine machine type (e2-small has 2 vCPU, 2GB RAM)"
  type        = string
  default     = "e2-small"
}

variable "gemini_api_key" {
  description = "Google Gemini API key for live analysis"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "git_repo_url" {
  description = "Git repository URL to clone on the instance"
  type        = string
  default     = "https://github.com/aisarthak/hasamex-task.git"
}

variable "git_branch" {
  description = "Git branch to checkout on the instance"
  type        = string
  default     = "main"
}
