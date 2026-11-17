-- Non-destructive: append evidence and expose a read-only API-facing projection.
ALTER TABLE catalog.retailer_listings
    ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE catalog.ingestion_runs
    ADD COLUMN IF NOT EXISTS diagnostics JSONB NOT NULL DEFAULT '{}'::jsonb;

-- This is a VIEW, not another copy of your products/offers.
-- Aayush can filter by model, category, age and condition in the backend.
CREATE OR REPLACE VIEW catalog.api_product_offers AS
SELECT
    l.id AS listing_id,
    l.variant_id,
    v.brand AS manufacturer,
    v.manufacturer_model,
    v.brand_key,
    v.model_key,
    v.category,
    l.retailer,
    l.source_listing_id,
    l.title,
    l.description,
    l.specifications,
    l.gtin,
    l.price_usd,
    l.currency,
    l.seller,
    l.product_condition,
    l.availability,
    l.source_url,
    l.extraction_method,
    l.collected_at,
    (l.collected_at >= now() - interval '48 hours') AS is_fresh
FROM catalog.retailer_listings AS l
JOIN catalog.product_variants AS v ON v.id = l.variant_id
WHERE l.source_type = 'scrape';
