-- Non-destructive migration: keep existing listing IDs/API contract while adding
-- canonical product identity and offer attributes for real retail data.
CREATE TABLE IF NOT EXISTS catalog.product_variants (
    id BIGSERIAL PRIMARY KEY,
    brand TEXT NOT NULL,
    brand_key TEXT NOT NULL,
    manufacturer_model TEXT NOT NULL,
    model_key TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (brand_key, model_key, category)
);
ALTER TABLE catalog.retailer_listings
    ADD COLUMN IF NOT EXISTS variant_id BIGINT REFERENCES catalog.product_variants(id),
    ADD COLUMN IF NOT EXISTS gtin TEXT,
    ADD COLUMN IF NOT EXISTS seller TEXT,
    ADD COLUMN IF NOT EXISTS product_condition TEXT NOT NULL DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS availability TEXT NOT NULL DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS extraction_method TEXT NOT NULL DEFAULT 'unknown';
CREATE INDEX IF NOT EXISTS idx_listings_variant ON catalog.retailer_listings (variant_id);
CREATE INDEX IF NOT EXISTS idx_listings_gtin ON catalog.retailer_listings (gtin) WHERE gtin IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_variant_model_key ON catalog.product_variants (model_key);
-- Conservative freshness window for demonstration queries. Source-specific
-- retention and display requirements still apply and may be stricter.
CREATE OR REPLACE VIEW catalog.fresh_retailer_offers AS
SELECT l.* FROM catalog.retailer_listings AS l
WHERE l.source_type = 'scrape'
  AND l.collected_at >= (now() - INTERVAL '48 hours');
