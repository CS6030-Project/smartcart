.DEFAULT_GOAL := help

SHELL := /bin/bash
PYTHON := .venv/bin/python
PIP := .venv/bin/pip
MAVEN := mvn -f backend/smartcart-api/pom.xml
SQL_FILES := $(sort $(wildcard data/ingestion/sql/*.sql))

.PHONY: help check-env check-tools setup python-deps db-up db-init ingest test test-python test-java api db-down status

help:
	@echo "SmartCart local development commands:"
	@echo "  make setup       Install Python dependencies and initialize PostgreSQL"
	@echo "  make ingest      Scrape and load 3 Abt products"
	@echo "  make test        Run Python and Java tests"
	@echo "  make api         Start Spring Boot with PostgreSQL"
	@echo "  make db-up       Start PostgreSQL"
	@echo "  make db-down     Stop PostgreSQL without deleting data"
	@echo "  make status      Show database container status"

check-env:
	@test -f .env || (echo "Missing .env. Run: cp .env.example .env, then set POSTGRES_PASSWORD"; exit 1)

check-tools:
	@command -v docker >/dev/null || (echo "Install Docker Desktop"; exit 1)
	@command -v python3 >/dev/null || (echo "Install Python 3.12+"; exit 1)
	@command -v mvn >/dev/null || (echo "Install Maven"; exit 1)
	@command -v java >/dev/null || (echo "Install Java 21"; exit 1)

python-deps:
	@test -x $(PYTHON) || python3 -m venv .venv
	@$(PYTHON) -m pip install -r data/ingestion/requirements.txt

db-up: check-env
	@docker compose up -d --wait postgres

db-init: db-up
	@set -a; source .env; set +a; \
	for sql in $(SQL_FILES); do \
		echo "Applying $$sql"; \
		docker compose exec -T postgres psql \
			-v ON_ERROR_STOP=1 \
			-U "$$POSTGRES_USER" -d "$$POSTGRES_DB" < "$$sql" || exit 1; \
	done

setup: check-tools python-deps db-init
	@echo "SmartCart setup complete."

ingest: python-deps db-init
	@PYTHON="$(CURDIR)/$(PYTHON)" bash data/ingestion/scripts/local_ingest.sh abt 3

test-python: python-deps
	@$(PYTHON) -m unittest discover -s data/ingestion/tests -t data/ingestion

test-java:
	@$(MAVEN) test

test: test-python test-java
	@echo "All SmartCart tests completed."

api: db-up
	@set -a; source .env; set +a; \
	SPRING_PROFILES_ACTIVE=db \
	DB_URL="jdbc:postgresql://localhost:$${POSTGRES_PORT:-5432}/$$POSTGRES_DB" \
	DB_USER="$$POSTGRES_USER" \
	DB_PASSWORD="$$POSTGRES_PASSWORD" \
	$(MAVEN) spring-boot:run

db-down:
	@docker compose stop postgres

status:
	@docker compose ps
