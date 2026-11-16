"""Discover configured products, fetch allowed pages, extract real observations.

A bounded run emits no synthetic listings. Source failures are reported to logs;
all-source failure aborts the batch so workflows cannot report false success.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterator

from collector.scraping.adapters import ADAPTERS
from collector.scraping.extract import ExtractionError, extract_product
from collector.scraping.fetch import AccessError, HtmlFetcher

LOG = logging.getLogger(__name__)


@dataclass
class ScrapeStats:
    attempted: int = 0
    accepted: int = 0
    failed: int = 0
    discovered: int = 0


class CatalogCollector:
    def __init__(self, config: dict, *, retailer_filter: set[str] | None = None,
                 max_records: int = 25, fetcher=None):
        self.config = config
        self.retailer_filter = retailer_filter
        self.max_records = max_records
        self.fetcher = fetcher or HtmlFetcher(**config.get("http", {}))
        self.stats = ScrapeStats()
        self.errors: list[str] = []

    def _candidates(self, retailer: str, settings: dict) -> Iterator[dict]:
        adapter = ADAPTERS[retailer]
        seen: set[str] = set()
        for seed in settings.get("products", []):
            url = adapter.normalize_url(seed["url"])
            if not adapter.is_product_url(url) or url in seen:
                continue
            if seed["category"] not in {"television", "dishwasher"}:
                continue
            seen.add(url)
            yield dict(seed, url=url)
        if self.config.get("discovery_mode", "seeds") != "category":
            return
        for category, urls in settings.get("category_urls", {}).items():
            if category not in {"television", "dishwasher"}:
                continue
            for start_url in urls:
                url = start_url
                pages = 0
                visited: set[str] = set()
                while url and url not in visited and pages < int(self.config.get("max_pages_per_category", 2)):
                    visited.add(url)
                    pages += 1
                    try:
                        html = self.fetcher.get(url, allowed_hosts=set(adapter.hosts))
                    except AccessError as exc:
                        self._fail(retailer, url, exc)
                        break
                    for link in adapter.discover_links(html, url):
                        if link not in seen:
                            seen.add(link)
                            self.stats.discovered += 1
                            yield {"url": link, "category": category}
                    url = adapter.next_page(html, url)

    def _fail(self, retailer: str, url: str, reason: Exception):
        self.stats.failed += 1
        # No API keys, cookies, query strings or raw HTML in logs.
        message = f"{retailer}: {url.split('?')[0]}: {reason}"
        self.errors.append(message)
        LOG.warning("collector skipped product: %s", message)

    def records(self) -> Iterator[dict]:
        """Round-robin retailers so a small run still has cross-store overlap."""
        if self.max_records < 1:
            raise ValueError("max_records must be positive")
        active = []
        for retailer, settings in self.config.get("retailers", {}).items():
            if not settings.get("enabled", False) or (self.retailer_filter and retailer not in self.retailer_filter):
                continue
            if retailer not in ADAPTERS:
                raise ValueError(f"no adapter for enabled retailer {retailer!r}")
            active.append((retailer, iter(self._candidates(retailer, settings))))
        while active and self.stats.accepted < self.max_records:
            next_round = []
            for retailer, candidates in active:
                if self.stats.accepted >= self.max_records:
                    break
                try:
                    seed = next(candidates)
                except StopIteration:
                    continue
                adapter = ADAPTERS[retailer]
                self.stats.attempted += 1
                try:
                    html = self.fetcher.get(seed["url"], allowed_hosts=set(adapter.hosts))
                    record = extract_product(
                        html, seed["url"], adapter, seed["category"],
                        expected_model=seed.get("model"), expected_brand=seed.get("brand"),
                    )
                    self.stats.accepted += 1
                    yield record
                except AccessError as exc:
                    self._fail(retailer, seed["url"], exc)
                    # An explicit denial or rate limit stops attempts for this retailer.
                    if any(token in str(exc).lower() for token in ("401", "403", "429", "robots.txt disallows")):
                        continue
                except (ExtractionError, ValueError) as exc:
                    self._fail(retailer, seed["url"], exc)
                next_round.append((retailer, candidates))
            active = next_round
