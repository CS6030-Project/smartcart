# SmartCart GCP deployment and operations

Project: `smartcart-cs6030` · Region: `us-central1` · Terraform root: `cloud/terraform/dev`.

## Provisioning responsibilities

The one-time Cloud Shell bootstrap creates the Terraform state bucket, two CI/CD service accounts and GitHub Workload Identity Federation. Terraform deploys Cloud SQL, Artifact Registry, Cloud Storage, runtime identities, Cloud Run services/jobs, Workflows and optional Scheduler. Secret values are initialized through `cloud/bootstrap/init-db.sh` in GCP, not stored in GitHub. Don't repeat initial setup on an already provisioned project.

Terraform state is in the GCS bucket `smartcart-cs6030-smartcart-tf-state` (prefix `smartcart/dev`); do not delete it or create divergent local state.

## First transition to real collection

1. Review and merge the scraper change through a pull request. Required CI checks should pass. `10 · CD / Ingestion workers` automatically tests and publishes images and updates existing Cloud Run Jobs.
2. In GitHub repository **Settings → Secrets and variables → Actions → Variables**, set `SOURCE_MODE=scrape`, `DISCOVERY_MODE=seeds`, `RETAILERS=` (empty selects all enabled configured adapters), `MAX_RECORDS=9` initially, `ENABLE_RUNTIME_JOBS=true`, `ENABLE_SCHEDULE=false`.
3. In GitHub **Actions → 20 · Ops / Terraform apply → Run workflow → main**, apply environment changes. Review the Terraform plan; the workflow currently applies automatically once the protected job starts. Do not enable public API access.
4. In Google Cloud Console, open **Workflows → smartcart-ingestion → Execute**. This runs the collector, writes GCS objects and an exact completed manifest, then runs the loader. Observe both Cloud Run Job executions and their logs.
5. In Cloud SQL Studio query `catalog.retailer_listings`, `catalog.product_variants` and `catalog.ingestion_runs`. A successful real ingestion removes old synthetic rows from the live listing table. No live records are fabricated if a source denies access.
6. Leave `ENABLE_SCHEDULE=false` until repeat executions and expected source metadata have been verified. For larger runs, adjust `MAX_RECORDS` and `DISCOVERY_MODE` then manually apply Terraform to update job settings; an image update alone does not update Terraform-owned environment settings.

## Routine releases

Merging ingestion code into main automatically triggers ingestion worker CI, Docker image publication (commit SHA) and Cloud Run Job image update. Merging the Spring Boot backend similarly triggers Maven tests, image publication and `smartcart-api` Cloud Run revision. Infrastructure changes still require a manual Terraform apply. GitHub environment `dev` may require reviewer approval.

## Troubleshooting

| Symptom | Where to inspect | Action |
|---|---|---|
| Collector returns zero records | Cloud Run `smartcart-collector` execution logs | Review source access, robots restrictions, selectors, model evidence and network errors; do not invent product rows |
| Workflow fails after collector | Cloud Workflows execution and loader logs | Inspect exact manifest URI, GCS hash/count verification and database permissions |
| Collector image updated but still says `fixtures` | Job environment settings and GitHub `SOURCE_MODE` | Change repository variable to `scrape` and run Terraform Apply |
| API still shows placeholder | `11 · CD / Spring Boot API` and Cloud Run revisions | Merge backend code and ensure its CI/CD passes |
| Prices look out of date | `collected_at`, seller, condition and source policy | Use freshness filtering and disable stale offers |
| GitHub Action cannot authenticate | `GCP_WIF_PROVIDER`, GCP service account, main branch and WIF IAM binding | Verify exact project number/identity configuration |

Cloud SQL is billed while the instance is running. Cloud Scheduler doesn't cap budget. Review GCP billing alerts, database retention and request volume before enabling repeated collection.
