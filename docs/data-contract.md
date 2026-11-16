# Product data and API contract

## Persistent catalog (PostgreSQL 16)

`data/ingestion/sql/001_catalog.sql` is the initial schema, created idempotently by the Python loader. Changes after adoption should be versioned migrations.

| Table | Key fields / purpose |
|---|---|
| `catalog.ingestion_runs` | `run_id` PK, `manifest_uri`, `source`, `collected_at`, accepted/rejected counts |
| `catalog.retailer_listings` | `id`, unique `source_url`, `retailer`, `source_listing_id`, `brand`, `model`, `category`, `price_usd`, `currency`, `specifications JSONB`, `raw_object_uri`, `collected_at`, `last_run_id` |

Indexes support candidate search by `lower(brand)`, `lower(model)` and category; GIN supports JSONB queries. `source_url` is an initial listing key; a later canonical SKU/retailer key can be introduced after source validation. Do not equate a retailer listing with a globally verified manufacturer variant.

```sql
SELECT retailer, source_url, brand, model, price_usd, specifications
FROM catalog.retailer_listings
WHERE category = 'refrigerator'
  AND lower(brand) = lower('Acme')
  AND lower(model) = lower('ACME-RF-001');
```

## Loader guarantees

- Completed batch manifest required; checks SHA-256 and record counts; scheduled ingestion rejects stale manifests.
- `source_type='synthetic'` is retained so test rows cannot be mistaken for retailer data.
- Repeated loads UPSERT the same `source_url`; older observations cannot overwrite a newer listing.
- Unknown specifications stay missing; model suffixes are preserved. Only USD price values are currently supported; other currencies require conversion before ingestion.
- Every normalized listing retains its raw batch URI and collection timestamp. Rejected records are counted and surfaced by the loader; raw evidence stays in GCS until its lifecycle expiration.

## Backend integration

Aayush's API currently uses `POST /api/v1/compare` with `ProductRequest` and `CompareResponse` records. Candidate retrieval should replace the empty `DefaultCandidateProductService` with a PostgreSQL repository and map DB `specifications` keys such as `capacityCubicFeet`, `configuration`, `finish`, `iceMaker` into Java fields. Category-aware rules can extend the JSONB shape without forcing unrelated columns onto all products.

For Cloud SQL on Cloud Run, Java needs a supported Cloud SQL PostgreSQL JDBC connector/socket factory if using the configured `jdbc:postgresql:///smartcart?cloudSqlInstance=...&socketFactory=...` URL; this dependency and disabling the current JDBC auto-configuration exclusion remain backend tasks. The API runtime identity receives `cloudsql.client` and `secretmanager.secretAccessor` grants. Enable Terraform's `enable_api_database` only after that wiring and DB credentials are ready.
