variable "project_id" {
  description = "Existing billed Google Cloud project ID"
  type        = string
}
variable "region" {
  description = "Primary GCP region"
  type        = string
  default     = "us-central1"
}
variable "raw_retention_days" {
  description = "Object age when raw batches become eligible for automatic deletion"
  type        = number
  default     = 10
  validation {
    condition     = var.raw_retention_days >= 1 && var.raw_retention_days <= 365
    error_message = "Retention must be between 1 and 365 days."
  }
}
variable "db_tier" {
  description = "Development Cloud SQL machine tier; adjust after evaluating actual resource requirements"
  type        = string
  default     = "db-f1-micro"
}
variable "enable_runtime_jobs" {
  description = "Enable collector/loader Jobs and Workflow only once container images and database password exist"
  type        = bool
  default     = false
}
variable "enable_schedule" {
  description = "Enable daily ingestion only after validating sources and jobs"
  type        = bool
  default     = false
}
variable "job_image_tag" {
  description = "Pre-published image tag for initial provisioning (CD owns later releases)"
  type        = string
  default     = "bootstrap"
}
variable "public_api" {
  description = "Allow unauthenticated requests to the demo backend; use auth/rate protection before wide release"
  type        = bool
  default     = false
}
variable "source_mode" {
  description = "fixtures for synthetic data; bestbuy requires approved API access and a managed secret"
  type        = string
  default     = "fixtures"
  validation {
    condition     = contains(["fixtures", "bestbuy"], var.source_mode)
    error_message = "source_mode must be fixtures or bestbuy."
  }
}

variable "max_records" {
  description = "Max raw records per collection execution; increase from 25 to 500 without code changes"
  type        = number
  default     = 25
  validation {
    condition     = var.max_records >= 1 && var.max_records <= 10000
    error_message = "max_records must be 1..10000."
  }
}
variable "max_age_hours" {
  description = "Reject old manifests during routine loads; explicit replay is separate"
  type        = number
  default     = 48
}
variable "enable_api_database" {
  description = "Enable Spring JDBC only after the backend adds the Cloud SQL PostgreSQL socket factory"
  type        = bool
  default     = false
}

variable "api_max_instances" {
  description = "Maximum Cloud Run API instances; set with database connection limits in mind"
  type        = number
  default     = 3
  validation {
    condition     = var.api_max_instances >= 1 && var.api_max_instances <= 100
    error_message = "api_max_instances must be 1..100."
  }
}
variable "schedule_cron" {
  description = "Collector refresh cron expression"
  type        = string
  default     = "0 3 * * *"
}
variable "schedule_timezone" {
  description = "Cloud Scheduler time zone"
  type        = string
  default     = "America/Detroit"
}
