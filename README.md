# SmartCart - CS6030 (Fall 2026)

Team: Rishikesh Upadhyaya, Aayush Guragain, Diego Peña Sadornil.

SmartCart is a planned Chrome extension and cloud application that helps compare product variants across stores. It should show Exact, Equivalent, Near-equivalent, or Different with reasons, not only a price difference.

## Current starter contents

- `backend/prototype/`: **small Java matching proof of concept** with real assertions, not yet a Spring Boot REST API.
- `contracts/`: sample JSON request/response for the planned API (synthetic demo data).
- `tests/`: tests for JSON contract examples.
- `.github/workflows/starter-ci.yml`: CI for Java proof of concept + contract fixtures.
- `docs/`: scope, team plan, matching choices, API sketch, report PDF and editable source.
- Empty starting directories for `extension/`, `dashboard/`, `worker/`, and `infrastructure/`.

## Local verification (Java 21 and Python 3)

```bash
bash scripts/check.sh
```

This verifies the small Java example and JSON fixtures. It does **not** verify the future Chrome extension, Spring Boot service, PostgreSQL, GKE, or Azure deployment.

## Project work

- Diego: Chrome MV3 extension, React UI, product-page capture, frontend integration.
- Aayush: Spring Boot API, matching engine, logical product model, backend tests.
- Rishikesh: limited data acquisition, database setup, GCP/Azure infrastructure, Docker, Terraform, CI/CD and monitoring.
- Shared: integration, tests, references, report, presentation.

The first release should connect a supported page to a real API and return an explained comparison. A curated catalog is acceptable for the first proof of concept if clearly identified.
