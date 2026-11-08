# Team plan

Our first goal is a working flow: **product page → comparison API → product data → explained match**. The initial scope is five selected products across five retailers.

| Owner | Main responsibility | Deliverables |
| --- | --- | --- |
| **Diego** | Chrome extension and React frontend | Product-page detection, basic extraction, comparison UI, API calls, Azure-hosted dashboard and frontend tests |
| **Aayush** | Spring Boot backend and matching | API contract, product/variant data model, logical database schema, matching rules, explanations, database queries, migrations and backend tests |
| **Rishikesh** | Data, database infrastructure, cloud and DevOps | Product sample records, limited permitted collection, Python normalization worker, local/cloud PostgreSQL, GCP/Azure infrastructure, Docker, Terraform, CI/CD, security and monitoring |

All three review the shared API and data format, integration, tests, references, report and presentation.

## Integration stages

1. **Agree on contracts:** request/response JSON, product identifiers and specifications.
2. **Build in parallel:** frontend with examples; backend with sample data; data and local database setup.
3. **Connect:** browser → API → PostgreSQL; then cloud deployment.
4. **Test and review:** end-to-end tests, monitoring, report and demo.

## Current foundation

The repository includes a Java matching prototype, draft API examples and automated starter tests. Cloud deployment and full application integration are the next implementation steps.
