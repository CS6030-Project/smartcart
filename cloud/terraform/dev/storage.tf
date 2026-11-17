resource "google_storage_bucket" "raw" {
  name                        = "${var.project_id}-smartcart-raw"
  project                     = var.project_id
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  versioning { enabled = false }
  # A raw object is eligible for deletion 10 days after upload by default.
  # GCS executes lifecycle rules asynchronously; this isn't an exact deadline.
  lifecycle_rule {
    action { type = "Delete" }
    condition { age = var.raw_retention_days }
  }
  # Avoid extending retained raw records via the default 7-day soft-delete window.
  soft_delete_policy { retention_duration_seconds = 0 }

  depends_on = [google_project_service.required]
}
