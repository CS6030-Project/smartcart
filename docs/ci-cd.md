# CI/CD and operational workflows

GitHub displays workflows as a flat list; numeric/category prefixes make that list recognizable by purpose. Individual workflow YAML files must remain directly inside `.github/workflows/` and cannot be nested as GitHub Actions folders.

| Workflow | Event | Action |
|---|---|---|
| `01 · CI / Repository` | All PRs and pushes | Java/Python repository starter checks |
| `02 · CI / Ingestion` | Ingestion PRs and main changes | Offline parser and manifest tests; collector/loader Docker builds |
| `03 · CI / Terraform` | Terraform PRs | Format/init/validate without credentials |
| `10 · CD / Ingestion workers` | Push/merge to main affecting `data/ingestion` or manual dispatch | PostgreSQL integration and replay gate; publish immutable collector/loader images; update existing Cloud Run Jobs |
| `11 · CD / Spring Boot API` | Push/merge to main affecting the backend or manual dispatch | Maven gate, image build, Artifact Registry publish and Cloud Run API revision |
| `20 · Ops / Terraform apply` | Manual dispatch on main | Plan/apply GCP resources using versioned GCS state, with GitHub `dev` environment policy |

## What a merge does automatically

A merged data ingestion change triggers `10 · CD / Ingestion workers`: tests run first, then both worker images are published and existing jobs updated. A backend merge automatically triggers its release workflow. Both use GitHub OIDC to authenticate as dedicated GCP deployment service accounts; no static JSON key or database password is stored in GitHub.

The jobs **do not automatically execute the ingestion Workflow** just because an image was deployed. The existing Cloud Scheduler controls recurring collection and should remain paused until source access and data accuracy are verified.

Terraform apply is intentionally manual because it can create, replace, destroy or bill resources. Changes to `SOURCE_MODE`, `DISCOVERY_MODE`, `RETAILERS`, Cloud SQL, service environment or Scheduler activation require an approved Terraform apply. Routine collector/loader code changes do not.

## Required repository configuration

Use GitHub Actions repository variables: `GCP_PROJECT_ID`, `GCP_REGION`, `TF_STATE_BUCKET`, `GCP_TF_SA`, `GCP_APP_DEPLOY_SA`, `GCP_WIF_PROVIDER`, `ENABLE_RUNTIME_JOBS`, `ENABLE_SCHEDULE`, `SOURCE_MODE`, `MAX_RECORDS`, `DISCOVERY_MODE`, `RETAILERS`, and existing Terraform variables. The recommended live source mode is `scrape`, initial discovery mode `seeds`, schedule disabled until validated.

After renaming existing workflows or job names, review the GitHub branch ruleset's **required status checks** and update any retired check names; GitHub can otherwise leave a PR waiting for a check that no longer runs.

Protect `main` and sensitive workflow/Terraform code with review requirements. GitHub environment `dev` can gate access to short-lived GCP identities; review settings depend on GitHub plan and repository visibility. The Terraform service account has broad development-project authority and should be reduced for production.

## Release verification

1. Check the corresponding `CD` workflow run and Docker image SHA tags in Artifact Registry.
2. Confirm the new Cloud Run Job image or API revision.
3. Manually execute `smartcart-ingestion` in Google Cloud Workflows for a controlled collection.
4. Inspect Job execution logs, completed GCS manifest and `catalog.ingestion_runs`.
5. Query `catalog.retailer_listings` and `catalog.product_variants` to confirm cross-retailer overlap and real-data provenance.

GitHub Actions only validates the offline extraction tests. A successful build does not guarantee any retailer's live site will be accessible or structured as expected.
