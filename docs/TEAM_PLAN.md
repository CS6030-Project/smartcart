# SmartCart - Team responsibilities and integration plan

This follows the team's two-page integration plan.

| Person | Primary owner | Main tasks |
|---|---|---|
| Diego Peña Sadornil | Chrome extension and React UI | MV3 popup, supported-page detection, product extraction, result cards, API integration, frontend tests and Azure-hosted React dashboard |
| Aayush Guragain | Spring Boot API and matching | API contract, product matching rules, explanations, backend database interface, REST docs, unit and integration tests, end-to-end demo coordination |
| Rishikesh Upadhyaya | Data and cloud platform | Select sample products and sources, local PostgreSQL setup, limited permitted ingestion, database provisioning, Docker, GKE/Azure environment, Terraform, GitHub Actions, security, monitoring and cost control |

All three: discuss alternative designs, verify the shared schema and API fields, test integration, prepare report and present in class.

## Four working stages
1. Agree on fields: request/response shape and normalized product records.
2. Build in parallel: extension with sample responses; API with sample inputs; data fixtures/local PostgreSQL.
3. Connect: extension -> API -> catalog, then deploy verified components.
4. Test and present: end-to-end checks, cloud evidence, monitoring, documentation.

## Don't misstate current progress
The included Java class is a tiny proof-of-concept. A full Spring Boot API, Chrome extension and cloud deployment remain separate work.
