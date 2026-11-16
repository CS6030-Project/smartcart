"""Retailer URL rules and localized HTML model/SKU evidence extraction.

The shared extractor handles JSON-LD and metadata. Adapters only describe the
few HTML differences that cannot be handled generically.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class RetailerAdapter:
    key: str
    hosts: frozenset[str]
    product_pattern: str
    model_pattern: str
    sku_pattern: str
    price_selectors: tuple[str, ...] = ()

    def is_product_url(self, url: str) -> bool:
        parts = urlparse(url)
        return (parts.scheme == "https" and (parts.hostname or "").lower() in self.hosts
                and bool(re.search(self.product_pattern, parts.path, re.I)))

    def normalize_url(self, url: str) -> str:
        parts = urlparse(url)
        return urlunparse((parts.scheme, parts.netloc.lower(), parts.path.rstrip("/") or "/", "", "", ""))

    def discover_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        seen: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            url = self.normalize_url(urljoin(base_url, anchor["href"]))
            if self.is_product_url(url) and url not in seen:
                seen.add(url)
                urls.append(url)
        return urls

    def next_page(self, html: str, base_url: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        anchor = soup.select_one('a[rel="next"][href]')
        if not anchor:
            return None
        url = urljoin(base_url, anchor["href"])
        parts = urlparse(url)
        if parts.scheme == "https" and (parts.hostname or "").lower() in self.hosts:
            return url
        return None

    def model_from_text(self, text: str) -> str | None:
        match = re.search(self.model_pattern, text, re.I)
        return match.group(1).strip() if match else None

    def sku_from_text(self, text: str) -> str | None:
        match = re.search(self.sku_pattern, text, re.I)
        return match.group(1).strip() if match else None


ADAPTERS: dict[str, RetailerAdapter] = {
    "bestbuy": RetailerAdapter(
        key="bestbuy", hosts=frozenset({"bestbuy.com", "www.bestbuy.com"}),
        product_pattern=r"/(product|site)/[^?#]+",
        model_pattern=r"\bModel\s*(?:Number)?\s*:?\s*([A-Za-z0-9][A-Za-z0-9._/-]{3,35})\b",
        sku_pattern=r"\bSKU\s*:?\s*([0-9]{5,12})\b",
        price_selectors=('meta[property="product:price:amount"]', 'meta[itemprop="price"]'),
    ),
    "homedepot": RetailerAdapter(
        key="homedepot", hosts=frozenset({"homedepot.com", "www.homedepot.com"}),
        product_pattern=r"/p/(?:[^?#]*/)?[0-9]{6,12}$",
        model_pattern=r"\bModel\s*#\s*([A-Za-z0-9][A-Za-z0-9._/-]{3,35})\b",
        sku_pattern=r"\b(?:Internet|Store SKU)\s*#\s*([0-9]{6,12})\b",
        price_selectors=('meta[property="product:price:amount"]', 'meta[itemprop="price"]'),
    ),
    "abt": RetailerAdapter(
        key="abt", hosts=frozenset({"abt.com", "www.abt.com"}),
        product_pattern=r"/p/[0-9]{3,12}\.html$|/[^/]+/p/[0-9]{3,12}\.html$",
        model_pattern=r"\bModel\s*#\s*([A-Za-z0-9][A-Za-z0-9._/-]{3,35})\b",
        sku_pattern=r"\bAbt\s*#\s*([A-Za-z0-9._-]{4,40})\b",
        price_selectors=('meta[property="product:price:amount"]', 'meta[itemprop="price"]'),
    ),
}
