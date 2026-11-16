"""Offline HTML snapshots for deterministic end-to-end integration tests.

These are *test* documents, not claimed captures of current retailer pages or prices.
The fixtures deliberately exercise real model identifiers and different prices.
"""
from __future__ import annotations
import json

TV_MODEL = "OLED55C6PUA"
DISH_MODEL = "GDT650SYVFS"


def page(model: str, *, brand="LG", category="television", price="999.99", sku="123456",
         include_jsonld=True, mismatch=False) -> str:
    label = f'{brand} 55" C6 OLED 4K Smart TV - {model}' if category == "television" else f'{brand} 24" Stainless Dishwasher - {model}'
    payload = {
        "@context": "https://schema.org", "@type": "Product", "name": label,
        "brand": {"@type": "Brand", "name": brand},
        "model": ("OLED65C6PUA" if mismatch else model), "sku": sku,
        "offers": {"@type": "Offer", "price": price, "priceCurrency": "USD",
                   "availability": "https://schema.org/InStock"},
    }
    script = f'<script type="application/ld+json">{json.dumps(payload)}</script>' if include_jsonld else ""
    return f'''<!doctype html><html><head>{script}
    <meta property="product:price:amount" content="{price}"><meta property="product:price:currency" content="USD">
    </head><body><h1>{label}</h1><p>Model # {model}</p><p>Model: {model}</p>
    <p>SKU: {sku}</p><p>Abt # ABT-{sku}</p><p>Internet # 325917499</p></body></html>'''


SAMPLE_URLS = {
    "bestbuy": "https://www.bestbuy.com/product/lg-c6-55-2026/6673121",
    "homedepot": "https://www.homedepot.com/p/341947263",
    "abt": "https://www.abt.com/LG-OLED-C6-55/p/240656.html",
}


class OfflineFetcher:
    def __init__(self, pages: dict[str, str]):
        self.pages = pages
        self.requests: list[str] = []

    def get(self, url: str, *, allowed_hosts: set[str]) -> str:
        from urllib.parse import urlparse
        if (urlparse(url).hostname or "") not in allowed_hosts:
            raise ValueError("unexpected host")
        self.requests.append(url)
        if url not in self.pages:
            from collector.scraping.fetch import AccessError
            raise AccessError("no approved local test page")
        return self.pages[url]


def offline_config() -> dict:
    return {
        "source": "scrape", "max_records": 3, "discovery_mode": "seeds",
        "http": {"respect_robots": True},
        "retailers": {
            key: {"enabled": True, "products": [{"url": url, "category": "television",
                                                    "brand": "LG", "model": TV_MODEL}], "category_urls": {}}
            for key, url in SAMPLE_URLS.items()
        }
    }


def offline_pages() -> dict[str, str]:
    return {url: page(TV_MODEL, price=price) for url, price in zip(
        SAMPLE_URLS.values(), ("999.99", "1299.99", "1099.99"))}
