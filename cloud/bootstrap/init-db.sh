#!/usr/bin/env bash
# One-time Cloud Shell command after Terraform has created Cloud SQL and the secret.
# Generates a password in Cloud Shell memory; never writes it to Git or GitHub Actions.
set -euo pipefail
PROJECT_ID="${PROJECT_ID:-smartcart-cs6030}"
INSTANCE="smartcart-pg-dev"
SECRET="smartcart-db-password"

EXISTING="$(gcloud secrets versions list "$SECRET" --project "$PROJECT_ID" --format='value(name)' --limit=1)"
if [[ -n "$EXISTING" ]]; then
  echo "Secret already has a version. Refusing to rotate credentials automatically." >&2
  exit 1
fi
PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(36))')"
trap 'unset PASSWORD' EXIT
if gcloud sql users list --project "$PROJECT_ID" --instance "$INSTANCE" --format='value(name)' | grep -qx smartcart; then
  gcloud sql users set-password smartcart --project "$PROJECT_ID" --instance "$INSTANCE" --password="$PASSWORD" --quiet
else
  gcloud sql users create smartcart --project "$PROJECT_ID" --instance "$INSTANCE" --password="$PASSWORD" --quiet
fi
printf '%s' "$PASSWORD" | gcloud secrets versions add "$SECRET" --project "$PROJECT_ID" --data-file=- >/dev/null
echo "PostgreSQL smartcart user initialized; password saved in GCP Secret Manager."
