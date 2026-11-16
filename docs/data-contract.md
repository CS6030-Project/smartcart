# Catalog and product-offer contract

The PostgreSQL catalog preserves two separate concepts: **manufacturer product variants** and **retailer listings**. A retailer URL or SKU cannot serve as the canonical product identity across merchants.

## Tables

| Entity | Primary role |
|---|---|
| `catalog.product_variants` | Canonical category, brand, exact manufacturer model; normalized brand/model keys, unique within category |
| `catalog.retailer_listings` | One current listing per canonical retailer `source_url`, with variant reference and offer data |
| `catalog.ingestion_runs` | Immutable run identity, manifest reference, source, accepted/rejected counts |

The loader executes `sql/001_catalog.sql` and then `sql/002_real_catalog.sql` in its PostgreSQL transaction. Both migrations are idempotent. The second migration adds `variant_id`, `gtin`, `seller`, `product_condition`, `availability` and `extraction_method` without breaking existing listing identifiers.

Raw collector records contain `retailer`, `source_url`, `source_listing_id`, `brand`, `model`, `category`, `title`, optional `price`, `currency`, `gtin`, `condition`, `seller`, `availability`, `specifications`, `source_type=scrape`, `collected_at` and `extraction_method`. The loader rejects inconsistent category/currency/model fields and preserves missing price as NULL.

A completed gzip JSONL manifest includes version, run ID, source, collected time, record count, SHA-256 per file and collection diagnostics. The loader reads only the exact completed manifest, verifies counts and hashes, rejects stale batches unless explicitly replayed, and upserts with a newer-data-wins condition. A successful real ingestion removes prior synthetic listings from the live table.

## Useful queries

Same manufacturer model sold at multiple stores:

```sql
SELECT v.brand, v.manufacturer_model, v.category, count(DISTINCT l.retailer) AS stores
FROM catalog.product_variants AS v
JOIN catalog.retailer_listings AS l ON l.variant_id = v.id
WHERE l.source_type = 'scrape'
GROUP BY v.id, v.brand, v.manufacturer_model, v.category
HAVING count(DISTINCT l.retailer) >= 2
ORDER BY stores DESC, v.brand, v.manufacturer_model;
```

Compare current stored offers of one exact TV model:

```sql
SELECT retailer, source_listing_id, price_usd, product_condition,
       availability, collected_at, source_url
FROM catalog.retailer_listings
WHERE lower(brand) = 'lg' AND upper(model) = 'OLED55C6PUA'
  AND source_type = 'scrape'
ORDER BY price_usd NULLS LAST, collected_at DESC;
```

The query above displays observed prices, not necessarily fresh/current prices. For consumer-facing API responses, filter by a source-approved freshness interval, seller and condition; missing prices or ambiguous variants must not yield verified price savings.

## Backend integration

The Spring Boot API should retrieve candidates by brand/model/category (or `variant_id` after canonical matching) and return evidence and offer age. Existing Java request/response types remain owned by the backend workstream; this migration doesn't automatically create database access within the Spring Boot app. Cloud Run's `ENABLE_API_DATABASE` should remain false until JDBC wiring and the Cloud SQL socket factory are deployed and tested.
