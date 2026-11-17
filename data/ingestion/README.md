# Product ingestion

A two-worker batch pipeline collects permitted HTML product listings, writes immutable gzip JSONL objects and a manifest, then loads normalized retailer offers into PostgreSQL. The collector has no SQL credentials; the loader has no retailer account credentials. The Workflows execution passes the exact manifest to the loader.

## Run locally

From `data/ingestion/` after installing `requirements.txt`:

```bash
python -m collector.main --source scrape --max-records 3 \
  --retailers abt,homedepot --output-dir /tmp/smartcart-live
```

The command prints `manifest_uri`. Validate its data without PostgreSQL:

```bash
python -m loader.main --manifest-uri /tmp/smartcart-live/manifests/<run-id>.json --dry-run
```

For database insertion, configure `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` and `DB_PASSWORD` and rerun the loader without `--dry-run`. Always use a local dev database for local integration tests.

**No external HTTP needed for CI:**

```bash
python -m unittest discover -s tests -v
python -m tests.create_offline_batch --output-dir /tmp/smartcart-ci
python -m loader.main --manifest-uri /tmp/smartcart-ci/manifests/ci-offline-batch.json --dry-run
```

The test source contains constructed product HTML for known manufacturer-model strings; test prices are illustrative and must not be represented as live offers.

## Configuration

`config.yaml` defines enabled retailers, curated product URLs, category landing pages, HTTP limits and the default 25-record cap. Options can override deployment controls without changing Python:

- `--max-records N` or `MAX_RECORDS` — accepted records per execution.
- `--retailers abt,homedepot` or `RETAILERS` — selected retailer adapters.
- `--discovery-mode seeds|category` or `DISCOVERY_MODE` — seed-only or bounded category URL discovery.
- `--config path` or `INGESTION_CONFIG` — alternate YAML configuration.
- `--output-dir` — local; `RAW_BUCKET` — Cloud Storage.

Seed collection is deliberately focused on verified model numbers. Category discovery follows product links and `rel=next` when the site's HTML exposes them; there is no universal promise that category pages are crawlable. The collector rotates between retailers to maximize early cross-store coverage.

## Contracts and error behavior

- Product page extraction: JSON-LD `Product`/`Offer`, then HTML/meta fallback.
- Only `television` and `dishwasher` categories enter the live catalog.
- Missing or conflicting model/brand evidence rejects a record; prices are nullable.
- A rate limit, explicit access denial or prohibited robots path is never bypassed.
- Zero valid records raises an error and writes no completed manifest.
- Completed batches include SHA-256 and record counts. The loader rejects tampering and stale manifests.
- Successful real ingestion removes the old `source_type='synthetic'` rows from `catalog.retailer_listings`, while test coverage remains offline.
- `catalog.product_variants` is grouped by normalized brand/model/category; `catalog.retailer_listings` preserves distinct seller/retailer offers. Matching decisions belong in the Spring Boot service.

See [scraping architecture](../../docs/scraping.md) and [data contract](../../docs/data-contract.md).

## Local development against the existing Docker Postgres

The repository root already has `compose.yaml` with a persistent `postgres_data` volume.
Run the **same collector and loader code as Cloud Run** without redeploying:

```bash
cd <your-smartcart-repo>
cp .env.example .env  # only if .env is missing; enter local credentials
python3 -m venv .venv
source .venv/bin/activate
pip install -r data/ingestion/requirements.txt
bash data/ingestion/scripts/local_ingest.sh abt,homedepot,bestbuy 9
```

This calls `docker compose up -d --wait postgres` (reuses the existing volume),
scrapes **live** retailer pages into `.local/ingestion/`, verifies the manifest,
then upserts into **local PostgreSQL**. It does not write to GCP. An existing volume
retains its original password even if you edit `.env`; use the credentials that
correspond to that volume. Never run `docker compose down -v` to fix authentication.

For a quick deterministic offline test (no live websites or GCP):

```bash
cd data/ingestion
python -m unittest discover -s tests -v
python -m tests.create_offline_batch --output-dir /tmp/smartcart-ci
python -m loader.main --manifest-uri /tmp/smartcart-ci/manifests/ci-offline-batch.json --dry-run
```

Inspect locally in IntelliJ's database window, DBeaver, pgAdmin or `psql`:

```sql
SELECT retailer, COUNT(*) FROM catalog.retailer_listings GROUP BY retailer;
SELECT * FROM catalog.api_product_offers ORDER BY collected_at DESC LIMIT 15;
SELECT run_id, accepted_count, rejected_count, diagnostics
  FROM catalog.ingestion_runs ORDER BY finished_at DESC LIMIT 5;
```

### Optional isolated Cloud Storage staging (not required for local tests)

For authorized GCP users who already have application-default credentials and
object-write permissions, run the same collector with `--bucket` instead of
`--output-dir`, plus `--namespace local-test`:

```bash
cd data/ingestion
python -m collector.main --source scrape --max-records 3 --retailers abt \
  --bucket smartcart-cs6030-smartcart-raw --namespace local-test
```

This writes only under `gs://.../local-test/raw/` and
`gs://.../local-test/manifests/`, not production manifests. You can pass the
resulting manifest URI to the same loader with `--dry-run`; loading into local
PostgreSQL still requires **local** DB credentials. Cloud Storage billing and
permissions still apply; local disk is the preferred default.

### See the actual collector logs in GCP

Google Cloud Console → **Cloud Run → Jobs → smartcart-collector → Executions → Logs**.
In Logs Explorer (not the Cloud Run API service logs), use:

```text
resource.type="cloud_run_job"
resource.labels.job_name="smartcart-collector"
resource.labels.location="us-central1"
```

Filter to the run's execution time. New code emits attempted URLs, elapsed time,
acceptance/rejection reasons, per-retailer totals and a manifest diagnostic
summary. `catalog.ingestion_runs.diagnostics` preserves bounded reason examples.
A green Workflow with only Abt rows is **partial retailer coverage**, not proof
that Best Buy/Home Depot worked. Do not bypass robots rules, 403, 429, or CAPTCHAs.
