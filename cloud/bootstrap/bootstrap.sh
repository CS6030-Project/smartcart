#!/usr/bin/env bash
# One-time bootstrap, intended to run in Google Cloud Shell, NOT on a laptop.
# Requires project administrator/IAM and billing permissions. Review before execution.
set -euo pipefail
PROJECT_ID="${PROJECT_ID:-smartcart-cs6030}"
REGION="${REGION:-us-central1}"
REPO_ID="1449935331"       # Stable numeric GitHub repository ID checked 2026-11-16
ORG_ID="353088412"         # Stable numeric GitHub organization ID checked 2026-11-16
STATE_BUCKET="${PROJECT_ID}-smartcart-tf-state"

# GitHub federation + remote state are bootstrap resources, intentionally outside the
# Terraform root they support; no dependency on any developer's local GCP account.
gcloud config set project "$PROJECT_ID"
gcloud services enable iam.googleapis.com iamcredentials.googleapis.com \
  sts.googleapis.com serviceusage.googleapis.com storage.googleapis.com \
  cloudresourcemanager.googleapis.com --project="$PROJECT_ID"
if ! gcloud storage buckets describe "gs://$STATE_BUCKET" --project="$PROJECT_ID" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://$STATE_BUCKET" --project="$PROJECT_ID" \
    --location="$REGION" --uniform-bucket-level-access --public-access-prevention
fi
gcloud storage buckets update "gs://$STATE_BUCKET" --versioning

for NAME in smartcart-tf smartcart-app-cd; do
  if ! gcloud iam service-accounts describe "$NAME@$PROJECT_ID.iam.gserviceaccount.com" --project="$PROJECT_ID" >/dev/null 2>&1; then
    gcloud iam service-accounts create "$NAME" --project="$PROJECT_ID" --display-name="SmartCart $NAME CI identity"
  fi
done

if ! gcloud iam workload-identity-pools describe smartcart-gh --location=global --project="$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create smartcart-gh --location=global --project="$PROJECT_ID" \
    --display-name="SmartCart GitHub Actions"
fi
if ! gcloud iam workload-identity-pools providers describe github \
  --workload-identity-pool=smartcart-gh --location=global --project="$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc github \
    --workload-identity-pool=smartcart-gh --location=global --project="$PROJECT_ID" \
    --issuer-uri=https://token.actions.githubusercontent.com \
    --attribute-mapping='google.subject=assertion.sub,attribute.repository_id=assertion.repository_id' \
    --attribute-condition="assertion.repository_id == '$REPO_ID' && assertion.repository_owner_id == '$ORG_ID' && assertion.ref == 'refs/heads/main'"
fi
NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
PRINCIPAL="principalSet://iam.googleapis.com/projects/$NUMBER/locations/global/workloadIdentityPools/smartcart-gh/attribute.repository_id/$REPO_ID"
for NAME in smartcart-tf smartcart-app-cd; do
  gcloud iam service-accounts add-iam-policy-binding "$NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --project="$PROJECT_ID" --role='roles/iam.workloadIdentityUser' --member="$PRINCIPAL" >/dev/null
done

# Project-scoped permissions for the DEV Terraform identity. In production, replace these
# administrative predefined roles with narrower custom roles/scoped permissions.
for ROLE in \
  roles/serviceusage.serviceUsageAdmin \
  roles/artifactregistry.admin \
  roles/storage.admin \
  roles/cloudsql.admin \
  roles/run.admin \
  roles/iam.serviceAccountAdmin \
  roles/iam.serviceAccountUser \
  roles/resourcemanager.projectIamAdmin \
  roles/secretmanager.admin \
  roles/workflows.admin \
  roles/cloudscheduler.admin; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:smartcart-tf@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$ROLE" --quiet >/dev/null
done
for ROLE in roles/artifactregistry.writer roles/run.developer roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:smartcart-app-cd@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$ROLE" --quiet >/dev/null
done
# Restrict state bucket access to Terraform identity; retains human admin access as configured.
gcloud storage buckets add-iam-policy-binding "gs://$STATE_BUCKET" \
  --member="serviceAccount:smartcart-tf@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin" >/dev/null

cat <<EOF
Bootstrap complete. Configure these GitHub Actions REPOSITORY VARIABLES:
GCP_PROJECT_ID=$PROJECT_ID
GCP_REGION=$REGION
TF_STATE_BUCKET=$STATE_BUCKET
GCP_TF_SA=smartcart-tf@$PROJECT_ID.iam.gserviceaccount.com
GCP_APP_DEPLOY_SA=smartcart-app-cd@$PROJECT_ID.iam.gserviceaccount.com
GCP_WIF_PROVIDER=projects/$NUMBER/locations/global/workloadIdentityPools/smartcart-gh/providers/github
ENABLE_RUNTIME_JOBS=false
ENABLE_SCHEDULE=false
PUBLIC_API=false
ENABLE_API_DATABASE=false
SOURCE_MODE=fixtures
MAX_RECORDS=25
MAX_AGE_HOURS=48
RAW_RETENTION_DAYS=10
DB_TIER=db-f1-micro
API_MAX_INSTANCES=3
SCHEDULE_CRON=0 3 * * *
SCHEDULE_TIMEZONE=America/Detroit
JOB_IMAGE_TAG=bootstrap

In GitHub create environment 'dev'. After the first Terraform apply, initialize
PostgreSQL using cloud/bootstrap/init-db.sh in Cloud Shell. Credentials will live
in GCP Secret Manager, NOT GitHub. Protect main and workflow files before apply.
EOF
