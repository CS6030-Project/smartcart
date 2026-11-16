output "artifact_registry" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}"
}
output "raw_bucket" { value = google_storage_bucket.raw.name }
output "api_url" { value = google_cloud_run_v2_service.api.uri }
output "sql_connection_name" { value = google_sql_database_instance.postgres.connection_name }
output "workflow_name" { value = var.enable_runtime_jobs ? google_workflows_workflow.ingestion[0].name : "not-yet-enabled" }
