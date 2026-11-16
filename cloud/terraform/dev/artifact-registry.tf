resource "google_artifact_registry_repository" "docker" {
  project       = var.project_id
  location      = var.region
  repository_id = "smartcart"
  format        = "DOCKER"
  description   = "SmartCart API and ingestion worker container images"
  depends_on    = [google_project_service.required]
}
