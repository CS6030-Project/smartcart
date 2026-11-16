# One-time identity and state bootstrap

Run `bash cloud/bootstrap/bootstrap.sh` **once** in Google Cloud Shell using an administrator account on the target project. This enables essential APIs, creates a versioned remote Terraform state bucket and creates separate GitHub Workload Identity Federation identities for infrastructure and image deployment.

After bootstrap, configure GitHub Actions repository variables printed by the script and a `dev` environment restricted to the reviewed `main` branch. The `20 · Ops / Terraform apply` workflow creates the required GCP resources. Once Cloud SQL and the empty Secret Manager secret exist, run `bash cloud/bootstrap/init-db.sh` in Cloud Shell. This generates the `smartcart` SQL user password and stores it directly in Secret Manager. Do not put the password in GitHub secrets, source control, or a developer's local environment.

Do not rerun `init-db.sh` for rotation; it refuses when a secret version already exists. Rotation is a separate planned administrative operation.

CI/CD deploys images automatically after relevant code is merged to main. Terraform apply remains manually controlled. See [deployment runbook](../../docs/deployment-runbook.md).
