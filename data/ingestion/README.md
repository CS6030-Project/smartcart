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
