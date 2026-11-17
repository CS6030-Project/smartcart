resource "google_service_account" "api" {
  project      = var.project_id
  account_id   = "smartcart-api"
  display_name = "SmartCart Cloud Run API runtime"
}
resource "google_service_account" "collector" {
  project      = var.project_id
  account_id   = "smartcart-collector"
  display_name = "SmartCart raw data collector"
}
resource "google_service_account" "loader" {
  project      = var.project_id
  account_id   = "smartcart-loader"
  display_name = "SmartCart PostgreSQL loader"
}
resource "google_service_account" "workflow" {
  project      = var.project_id
  account_id   = "smartcart-workflow"
  display_name = "SmartCart ingestion orchestration"
}
resource "google_service_account" "scheduler" {
  project      = var.project_id
  account_id   = "smartcart-scheduler"
  display_name = "SmartCart schedule invoker"
}
resource "google_storage_bucket_iam_member" "collector_write" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.collector.email}"
}
resource "google_storage_bucket_iam_member" "loader_read" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.loader.email}"
}
resource "google_project_iam_member" "loader_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.loader.email}"
}
resource "google_project_iam_member" "api_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}
resource "google_secret_manager_secret" "db_password" {
  project   = var.project_id
  secret_id = "smartcart-db-password"
  replication {
    auto {}
  }
  depends_on = [google_project_service.required]
  # Secret VALUE is not managed by Terraform; an authorized bootstrap workflow adds it.
}
resource "google_secret_manager_secret_iam_member" "loader_db_password" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.loader.email}"
}
resource "google_secret_manager_secret_iam_member" "api_db_password" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}
# The batch orchestrator needs permission to start its two predefined Cloud Run Jobs.
resource "google_project_iam_member" "workflow_run" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.workflow.email}"
}
resource "google_project_iam_member" "scheduler_workflows" {
  project = var.project_id
  role    = "roles/workflows.invoker"
  member  = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_secret_manager_secret" "bestbuy_api_key" {
  project   = var.project_id
  secret_id = "smartcart-bestbuy-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.required]
}
resource "google_secret_manager_secret_iam_member" "collector_bestbuy_key" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.bestbuy_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.collector.email}"
}
