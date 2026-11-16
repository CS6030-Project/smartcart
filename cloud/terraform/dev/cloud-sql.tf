resource "google_sql_database_instance" "postgres" {
  project             = var.project_id
  name                = "smartcart-pg-dev"
  region              = var.region
  database_version    = "POSTGRES_16"
  deletion_protection = false # Development only; protect production data.

  settings {
    tier              = var.db_tier
    edition           = "ENTERPRISE"
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10
    disk_autoresize   = true
    backup_configuration {
      enabled    = true
      start_time = "04:00"
    }
    ip_configuration {
      ipv4_enabled = true
      # No authorized networks: direct public TCP clients cannot use password-only access.
      # Cloud Run uses the managed Cloud SQL Auth Proxy socket.
    }
  }
  depends_on = [google_project_service.required]
}
resource "google_sql_database" "catalog" {
  project  = var.project_id
  name     = "smartcart"
  instance = google_sql_database_instance.postgres.name
}
