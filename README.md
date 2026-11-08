# SmartCart

**CS6030 Cloud Computing | Western Michigan University | Fall 2026**

SmartCart is a browser extension that helps shoppers compare products across retailers. It uses model numbers and product specifications to determine whether two listings are **Exact**, **Equivalent**, **Near-equivalent**, or **Different**, and explains the result.

## Technology

- **Frontend:** Chrome Extension (Manifest V3), React, TypeScript
- **Backend:** Java, Spring Boot
- **Database:** PostgreSQL
- **Cloud:** Google Cloud Platform and Microsoft Azure
- **DevOps:** Docker, GitHub Actions, Terraform

## Team

| Member | Focus |
| --- | --- |
| Diego Peña Sadornil | Browser extension and frontend |
| Aayush Guragain | Backend API and product matching |
| Rishikesh Upadhyaya | Product data, cloud infrastructure and DevOps |

## Project folders

- `frontend/` — Chrome extension and React dashboard
- `backend/` — Java matching code and Spring Boot API
- `data/` — Sample records and product data ingestion
- `cloud/` — Terraform and Kubernetes configuration
- `docs/` — Team plan, API examples and midterm report
- `tests/` — Shared tests

## Run starter checks

Requires **Java 21 JDK** and **Python 3**:

```bash
bash run-tests.sh
```

The repository includes a small Java matching example and test cases. The Spring Boot API, browser extension and cloud deployment will be developed and connected next.

See [`docs/team-plan.md`](docs/team-plan.md) for responsibilities and [`docs/api.md`](docs/api.md) for the draft comparison API.
