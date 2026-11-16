-- Idempotent first-version catalog schema. Coordinate future schema changes through migrations.
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE TABLE IF NOT EXISTS catalog.ingestion_runs (
    run_id TEXT PRIMARY KEY,
    manifest_uri TEXT NOT NULL,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    accepted_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS catalog.retailer_listings (
    id BIGSERIAL PRIMARY KEY,
    retailer TEXT NOT NULL,
    source_url TEXT NOT NULL UNIQUE,
    source_listing_id TEXT,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    price_usd NUMERIC(12,2),
    currency TEXT NOT NULL DEFAULT 'USD',
    specifications JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_type TEXT NOT NULL,
    raw_object_uri TEXT NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    last_run_id TEXT NOT NULL REFERENCES catalog.ingestion_runs(run_id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_listing_model ON catalog.retailer_listings (lower(brand), lower(model));
CREATE INDEX IF NOT EXISTS idx_listing_category ON catalog.retailer_listings (category, lower(brand));
CREATE INDEX IF NOT EXISTS idx_listing_specs ON catalog.retailer_listings USING GIN (specifications);
-- Aayush can query rows using: SELECT ... FROM catalog.retailer_listings WHERE category=? AND lower(brand)=lower(?);
