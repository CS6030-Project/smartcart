"""Synthetic fixtures and an authorized Best Buy Products API adapter.

A second real retailer must be implemented as a separate adapter after confirming
its permitted access. Synthetic retailer names are never presented as real data.
"""
from __future__ import annotations
from datetime import datetime, timezone
import math
import os
from typing import Iterator
import requests

PRODUCTS = (
    ("refrigerator", "RF", {"capacityCubicFeet": 25.0, "configuration": "French door", "finish": "Stainless", "iceMaker": True}),
    ("television", "TV", {"screenInches": 55, "resolution": "4K", "refreshHz": 60}),
    ("dishwasher", "DW", {"widthInches": 24, "installation": "Built-in", "noiseDb": 44}),
    ("washer", "WA", {"capacityCubicFeet": 4.5, "configuration": "Front load"}),
    ("air_conditioner", "AC", {"btu": 10000, "installation": "Window"}),
)


def fixtures(max_records: int = 25, *, retailers: list[str] | None = None) -> Iterator[dict]:
    """Generate consistent cross-store fixtures: 25 by default; 500 if configured."""
    retailers = retailers or ["demo-mart", "demo-home", "demo-tech", "demo-shop", "demo-market"]
    produced = 0
    model_count = math.ceil(max_records / len(retailers))
    for model_index in range(model_count):
        category, code, base_specs = PRODUCTS[model_index % len(PRODUCTS)]
        variant_number = model_index // len(PRODUCTS) + 1
        model = f"ACME-{code}-{variant_number:03d}"
        specs = dict(base_specs)
        if "capacityCubicFeet" in specs:
            specs["capacityCubicFeet"] = round(specs["capacityCubicFeet"] + (variant_number - 1) * 0.1, 2)
        for retail_index, retailer in enumerate(retailers):
            yield {
                "retailer": retailer,
                "source_url": f"https://{retailer}.example/products/{model.lower()}",
                "source_listing_id": f"{retailer}-{model}",
                "brand": "Acme", "model": model, "category": category,
                "title": f"Acme {model}", "price": str(899 + 50 * retail_index + model_index),
                "currency": "USD", "specifications": specs,
                "source_type": "synthetic",
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
            produced += 1
            if produced >= max_records:
                return


def _category(category_path: list | None) -> str | None:
    names = " ".join(c.get("name", "") for c in category_path or [] if isinstance(c, dict)).lower()
    for category, tokens in (
        ("refrigerator", ("refrigerator",)),
        ("television", ("television", " tv", "tvs")),
        ("dishwasher", ("dishwasher",)),
        ("washer", ("washing machine", "washer")),
        ("air_conditioner", ("air conditioner",)),
    ):
        if any(token in names for token in tokens):
            return category
    return None


def bestbuy_api(*, max_records: int = 25, page_size: int = 100,
                max_pages: int = 20, searches: list[str] | None = None) -> Iterator[dict]:
    """Best Buy Products API search; requires a key and permitted use.

    Counts are upper limits, not guarantees: pages can lack required fields or
    contain products outside supported categories.
    """
    api_key = os.getenv("BESTBUY_API_KEY")
    if not api_key:
        raise RuntimeError("BESTBUY_API_KEY is required for Best Buy collection")
    if not 1 <= page_size <= 100:
        raise ValueError("Best Buy page_size must be between 1 and 100")
    searches = searches or ["refrigerator", "television", "dishwasher", "washer", "air conditioner"]
    seen: set[str] = set()
    count = 0
    for search in searches:
        # Official v1 keyword syntax uses products(search=term) rather than a
        # generic URL-scraping pattern. Avoid unrestricted catalog crawling.
        query = "&".join(f"search={part}" for part in search.split())
        endpoint = f"https://api.bestbuy.com/v1/products({query})"
        for page in range(1, max_pages + 1):
            response = requests.get(endpoint, params={
                "apiKey": api_key, "format": "json", "pageSize": page_size,
                "page": page,
                "show": "sku,name,manufacturer,modelNumber,salePrice,url,categoryPath",
            }, timeout=30)
            response.raise_for_status()
            products = response.json().get("products", [])
            for product in products:
                model, brand, url = product.get("modelNumber"), product.get("manufacturer"), product.get("url")
                category = _category(product.get("categoryPath"))
                if not all((model, brand, url, category)) or url in seen:
                    continue
                seen.add(url)
                yield {
                    "retailer": "bestbuy", "source_url": url,
                    "source_listing_id": str(product.get("sku") or ""),
                    "title": product.get("name") or f"{brand} {model}",
                    "brand": brand, "model": model, "category": category,
                    "price": product.get("salePrice"), "currency": "USD",
                    "specifications": {}, "raw_extra": product,
                    "source_type": "bestbuy_api", "collected_at": datetime.now(timezone.utc).isoformat(),
                }
                count += 1
                if count >= max_records:
                    return
            if not products or len(products) < page_size:
                break
