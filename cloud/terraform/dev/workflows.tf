resource "google_workflows_workflow" "ingestion" {
  count               = var.enable_runtime_jobs ? 1 : 0
  project             = var.project_id
  region              = var.region
  name                = "smartcart-ingestion"
  description         = "Collect raw listing batch, then load only that completed batch"
  service_account     = google_service_account.workflow.email
  deletion_protection = false
  source_contents = replace(replace(replace(
    file("${path.module}/../../workflows/ingestion.yaml"),
    "__PROJECT_ID__", var.project_id),
    "__REGION__", var.region),
  "__RAW_BUCKET__", google_storage_bucket.raw.name)
  depends_on = [google_cloud_run_v2_job.collector, google_cloud_run_v2_job.loader]
}
resource "google_cloud_scheduler_job" "daily" {
  count       = var.enable_runtime_jobs ? 1 : 0
  project     = var.project_id
  region      = var.region
  name        = "smartcart-daily-ingestion"
  description = "Daily scheduled ingestion; disabled until validated"
  schedule    = var.schedule_cron
  time_zone   = var.schedule_timezone
  paused      = !var.enable_schedule
  http_target {
    uri         = "https://workflowexecutions.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/workflows/${google_workflows_workflow.ingestion[0].name}/executions"
    http_method = "POST"
    body        = base64encode("{\"argument\":\"{}\"}")
    headers     = { "Content-Type" = "application/json" }
    oauth_token { service_account_email = google_service_account.scheduler.email }
  }
  depends_on = [google_project_iam_member.scheduler_workflows]
}
