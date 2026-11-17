# SmartCart development infrastructure (Terraform)

Terraform controls project-scoped GCP APIs, the Artifact Registry repository, Cloud SQL PostgreSQL, private GCS raw archive, runtime IAM identities, Cloud Run API service and ingestion Jobs, Workflows and optional paused Scheduler. GitHub Actions handles container image releases separately; Terraform ignores image drift to avoid rolling back current application revisions.

This stack uses an existing billed project. Remote GCS state and GitHub Workload Identity Federation are bootstrapped once using `cloud/bootstrap/bootstrap.sh`, prior to the first Terraform apply. Keep state bucket versioning enabled.

Runtime configuration: `enable_runtime_jobs`, `enable_schedule`, `public_api`, `enable_api_database`, `source_mode=scrape`, `discovery_mode=seeds|category`, `retailers` (optional comma-separated), `max_records`, `raw_retention_days`, `max_age_hours`, Cloud SQL tier, API instance limits and scheduling settings. GitHub Actions repository variables feed corresponding Terraform input variables.

To make a configuration change, update the repository variables, then manually run `20 · Ops / Terraform apply` from the protected `main` branch. Do not simultaneously run local `terraform apply` against this shared state.

A database password is added to Secret Manager by `cloud/bootstrap/init-db.sh` after the secret resource exists. The loader gets the password as a runtime secret reference. Spring Boot database wiring is a separate backend task; leave `ENABLE_API_DATABASE=false` until the required JDBC connector and configuration are deployed. `PUBLIC_API=false` leaves the API nonpublic until authentication and usage safeguards are designed.

The collector Job has a one-hour task timeout for bounded retailer collection. Time and throughput depend on source limits; setting `MAX_RECORDS=500` or `1000` does not guarantee those counts. See [data collection](../../../docs/scraping.md), [CI/CD](../../../docs/ci-cd.md) and [deployment](../../../docs/deployment-runbook.md).
