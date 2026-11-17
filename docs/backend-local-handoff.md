
# SmartCart Backend: Local Setup and Handoff

## Purpose

This document explains how to run and test the SmartCart Spring Boot backend with a local PostgreSQL database.

The implementation is on the `feature/aayush-backend` branch.

The local setup uses Docker Compose and does not require Google Cloud credentials.

## Requirements

Install and verify:

- Git
- Docker Desktop, with Docker running
- Python 3.12 or newer
- Java 21
- Apache Maven
- GNU Make

Run all commands from the repository root.

## 1. Get the branch

```bash
git clone https://github.com/CS6030-Project/smartcart.git
cd smartcart
git switch feature/aayush-backend
```

For an existing clone:

```bash
git fetch origin
git switch feature/aayush-backend
git pull --ff-only
```

## 2. Configure local PostgreSQL

Create the local environment file:

```bash
cp .env.example .env
```

Open `.env` and replace `replace_me_locally` with a local password.

Do not commit `.env` or use production database credentials.

Start Docker Desktop before continuing.

## 3. Install dependencies and initialize the database

```bash
make setup
```

This installs Python dependencies, starts PostgreSQL, and applies the SQL migrations.

The PostgreSQL data is stored in a persistent Docker volume.

## 4. Run automated tests

```bash
make test
```

This runs the Python ingestion tests and Java backend tests.

At handoff, the Java test suite passed 18 tests with no failures or errors.

## 5. Ingest sample products

```bash
make ingest
```

This collects up to three real product listings from Abt, validates the collected records, and loads them into local PostgreSQL.

Live scraping depends on retailer availability and page structure.

## 6. Start the backend

```bash
make api
```

The backend uses the Spring Boot `db` profile and connects to the local PostgreSQL database.

Keep this Terminal window open while testing.

The API runs at:

`http://localhost:8080`

## 7. Test product comparison

Open a second Terminal window in the repository root and run:

```bash
curl -i -X POST http://localhost:8080/api/v1/compare \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "retailer": "test",
      "url": "https://example.com/lg-oled55c6pua",
      "brand": "LG",
      "model": "OLED55C6PUA",
      "category": "television",
      "price": 1499.99,
      "currency": "USD",
      "specifications": {}
    }
  }'
```

Important: the request body must contain the outer `product` object.

After successful ingestion, the API should return HTTP 200 with a `comparisons` array.

The matching results include classifications, reasons, retailer offers, prices, and product URLs.

## 8. Other Makefile commands

| Command | Purpose |
|---|---|
| `make help` | Show available commands |
| `make setup` | Install Python dependencies and initialize PostgreSQL |
| `make ingest` | Collect and load three Abt products |
| `make test` | Run Python and Java tests |
| `make test-python` | Run Python tests |
| `make test-java` | Run Java tests |
| `make api` | Start Spring Boot using local PostgreSQL |
| `make db-up` | Start PostgreSQL |
| `make db-down` | Stop PostgreSQL without deleting data |
| `make status` | Show database container status |

## 9. Implementation notes

- Java 21 and Spring Boot provide the matching API.
- PostgreSQL 16 stores the local product catalog.
- Python collects and loads retailer product data.
- SQL migrations are under `data/ingestion/sql/`.
- The backend reads product candidates from `catalog.api_product_offers`.
- Database connection settings are supplied through `.env` and passed to Spring Boot.
- Local PostgreSQL is separate from the planned Google Cloud SQL deployment.
- The matching logic distinguishes exact products from cases with insufficient evidence.

## 10. Review and merge

Review the `feature/aayush-backend` branch and run the setup, ingestion, and API checks above.

When satisfied, open a GitHub pull request from:

`feature/aayush-backend` into `main`

Review the changes and required CI checks before merging.

Do not merge directly without the team's review.

