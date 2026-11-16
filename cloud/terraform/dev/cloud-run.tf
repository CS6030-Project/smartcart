resource "google_cloud_run_v2_service" "api" {
  project             = var.project_id
  name                = "smartcart-api"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false
  template {
    service_account = google_service_account.api.email
    scaling {
      min_instance_count = 0
      max_instance_count = var.api_max_instances
    }
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello" # Replaced by backend release workflow
      ports { container_port = 8080 }
      resources { limits = { cpu = "1", memory = "1Gi" } }
      env {
        name  = "SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE"
        value = "2"
      }
      dynamic "env" {
        for_each = var.enable_api_database ? [1] : []
        content {
          name  = "SPRING_DATASOURCE_URL"
          value = "jdbc:postgresql:///smartcart?cloudSqlInstance=${google_sql_database_instance.postgres.connection_name}&socketFactory=com.google.cloud.sql.postgres.SocketFactory"
        }
      }
      dynamic "env" {
        for_each = var.enable_api_database ? [1] : []
        content {
          name  = "SPRING_DATASOURCE_USERNAME"
          value = "smartcart"
        }
      }
      dynamic "env" {
        for_each = var.enable_api_database ? [1] : []
        content {
          name = "SPRING_DATASOURCE_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.db_password.secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }
  lifecycle {
    # Terraform owns service configuration. CI/CD owns the application image revision.
    ignore_changes = [template[0].containers[0].image]
  }
  depends_on = [google_project_service.required]
}
resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.public_api ? 1 : 0
  project  = var.project_id
  location = google_cloud_run_v2_service.api.location
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
resource "google_cloud_run_v2_job" "collector" {
  count               = var.enable_runtime_jobs ? 1 : 0
  project             = var.project_id
  location            = var.region
  name                = "smartcart-collector"
  deletion_protection = false
  template {
    task_count  = 1
    parallelism = 1
    template {
      service_account = google_service_account.collector.email
      timeout         = "3600s"
      # A failed collector may have written immutable partial objects. Start a new
      # Workflow execution (new run ID) instead of retrying the same object names.
      max_retries = 0
      containers {
        name  = "collector"
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}/collector:${var.job_image_tag}"
        env {
          name  = "RAW_BUCKET"
          value = google_storage_bucket.raw.name
        }
        env {
          name  = "SOURCE_MODE"
          value = var.source_mode
        }
        env {
          name  = "MAX_RECORDS"
          value = tostring(var.max_records)
        }
        env {
          name  = "DISCOVERY_MODE"
          value = var.discovery_mode
        }
        env {
          name  = "RETAILERS"
          value = var.retailers
        }
        resources { limits = { cpu = "1", memory = "512Mi" } }
      }
    }
  }
  lifecycle { ignore_changes = [template[0].template[0].containers[0].image] }
  depends_on = [google_project_service.required]
}
resource "google_cloud_run_v2_job" "loader" {
  count               = var.enable_runtime_jobs ? 1 : 0
  project             = var.project_id
  location            = var.region
  name                = "smartcart-loader"
  deletion_protection = false
  template {
    task_count  = 1
    parallelism = 1
    template {
      service_account = google_service_account.loader.email
      timeout         = "900s"
      max_retries     = 1
      containers {
        name  = "loader"
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}/loader:${var.job_image_tag}"
        env {
          name  = "DB_HOST"
          value = "/cloudsql/${google_sql_database_instance.postgres.connection_name}"
        }
        env {
          name  = "DB_NAME"
          value = google_sql_database.catalog.name
        }
        env {
          name  = "DB_USER"
          value = "smartcart"
        }
        env {
          name  = "MAX_AGE_HOURS"
          value = tostring(var.max_age_hours)
        }
        env {
          name  = "MANIFEST_URI"
          value = "gs://${google_storage_bucket.raw.name}/manifests/manual.json"
        }
        env {
          name = "DB_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.db_password.secret_id
              version = "latest"
            }
          }
        }
        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
        resources { limits = { cpu = "1", memory = "512Mi" } }
      }
      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [google_sql_database_instance.postgres.connection_name]
        }
      }
    }
  }
  lifecycle { ignore_changes = [template[0].template[0].containers[0].image] }
  depends_on = [google_project_service.required]
}
