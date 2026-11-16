from __future__ import annotations

import gzip
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from collector.main import run
from collector.scraping.adapters import ADAPTERS
from collector.scraping.catalog import CatalogCollector
from collector.scraping.extract import ExtractionError, extract_product
from collector.scraping.fetch import AccessError, HtmlFetcher
from common.records import brand_key, model_key, normalize_listing, normalize_price
from loader.main import load_batch
from tests.support import (DISH_MODEL, TV_MODEL, OfflineFetcher,
                           SAMPLE_URLS, offline_config, offline_pages, page)


class ExtractionTests(unittest.TestCase):
    def test_jsonld_exact_tv_and_offer(self):
        url = SAMPLE_URLS["bestbuy"]
        data = extract_product(page(TV_MODEL), url, ADAPTERS["bestbuy"], "television", expected_model=TV_MODEL)
        row = normalize_listing(data)
        self.assertEqual(row["model"], TV_MODEL)
        self.assertEqual(row["price_usd"], normalize_price("999.99"))
        self.assertEqual(row["specifications"]["screenInches"], 55)
        self.assertEqual(row["specifications"]["displayType"], "OLED")
        self.assertEqual(row["availability"], "instock")
        self.assertEqual(row["source_type"], "scrape")

    def test_html_fallback_dishwasher(self):
        url = "https://www.homedepot.com/p/325917499"
        item = extract_product(page(DISH_MODEL, brand="GE", category="dishwasher",
                                    price="579.00", include_jsonld=False),
                               url, ADAPTERS["homedepot"], "dishwasher", expected_model=DISH_MODEL)
        self.assertEqual(item["extraction_method"], "html")
        self.assertEqual(item["specifications"]["widthInches"], 24.0)
        self.assertEqual(item["model"], DISH_MODEL)
        self.assertEqual(normalize_listing(item)["price_usd"], normalize_price(579))

    def test_rejects_conflicting_variant(self):
        url = SAMPLE_URLS["bestbuy"]
        with self.assertRaisesRegex(ExtractionError, "conflicts"):
            extract_product(page(TV_MODEL, mismatch=True), url, ADAPTERS["bestbuy"],
                            "television", expected_model=TV_MODEL)

    def test_rejects_model_not_on_page(self):
        url = SAMPLE_URLS["abt"]
        html = '<html><body><h1>LG television</h1></body></html>'
        with self.assertRaisesRegex(ExtractionError, "missing verified"):
            extract_product(html, url, ADAPTERS["abt"], "television", expected_model=TV_MODEL)

    def test_brand_aliases_do_not_split_variants(self):
        self.assertEqual(brand_key("LG"), brand_key("LG Electronics"))
        self.assertEqual(brand_key("GE"), brand_key("GE Appliances"))
        self.assertEqual(brand_key("Samsung"), brand_key("Samsung Electronics"))

    def test_model_key_retains_distinct_variants(self):
        self.assertNotEqual(model_key("OLED55C6PUA"), model_key("OLED65C6PUA"))
        self.assertNotEqual(model_key("GDT650SYVFS"), model_key("GDT650SMVES"))
        self.assertEqual(model_key("OLED-55C6PUA"), model_key("OLED55C6PUA"))

    def test_rejects_bad_data(self):
        with self.assertRaisesRegex(ValueError, "USD"):
            normalize_listing({**extract_product(page(TV_MODEL), SAMPLE_URLS['abt'],
                        ADAPTERS['abt'], 'television'), 'currency': 'EUR'})
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            normalize_price(-4)

    def test_url_discovery_and_pagination_host_check(self):
        adapter = ADAPTERS["abt"]
        html = '''<a href="/LG-OLED-C6-55/p/240656.html">one</a>
        <a href="/LG-OLED-C6-55/p/240656.html">duplicate</a>
        <a href="https://evil.example/p/123456.html">offsite</a>
        <a rel="next" href="/OLED-TVs/c/2282.html?page=2">next</a>'''
        self.assertEqual(adapter.discover_links(html, "https://www.abt.com/OLED-TVs/c/2282.html"),
                         [SAMPLE_URLS["abt"]])
        self.assertEqual(adapter.next_page(html, "https://www.abt.com/OLED-TVs/c/2282.html"),
                         "https://www.abt.com/OLED-TVs/c/2282.html?page=2")

    def test_crawler_reports_blocked_sources_without_inventing_data(self):
        collector = CatalogCollector(offline_config(), max_records=3, fetcher=OfflineFetcher({}))
        self.assertEqual(list(collector.records()), [])
        self.assertEqual(collector.stats.failed, 3)


class PipelineTests(unittest.TestCase):
    def test_local_live_code_path_bounded_to_two(self):
        with tempfile.TemporaryDirectory() as root:
            manifest_path = Path(run("scrape", "offline-test-a", output_dir=root,
                                     max_records=2, config=offline_config(),
                                     fetcher=OfflineFetcher(offline_pages())))
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["record_count"], 2)
            self.assertEqual(manifest["priced_records"], 2)
            report = load_batch(str(manifest_path), dry_run=True)
            self.assertEqual(report["accepted"], 2)
            self.assertEqual(report["rejected"], 0)
            raw = Path(root) / manifest["files"][0]["path"]
            content = gzip.decompress(raw.read_bytes()).decode().splitlines()
            self.assertEqual(len(content), 2)
            self.assertTrue(all(json.loads(v)["source_type"] == "scrape" for v in content))

    def test_end_to_end_three_real_model_observations(self):
        with tempfile.TemporaryDirectory() as root:
            mp = run("scrape", "offline-test-b", output_dir=root, max_records=3,
                     config=offline_config(), fetcher=OfflineFetcher(offline_pages()))
            report = load_batch(mp, dry_run=True)
            self.assertEqual(report["accepted"], 3)
            self.assertEqual(report["source"], "scrape")

    def test_zero_valid_products_never_writes_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(RuntimeError, "zero valid real products"):
                run("scrape", "blocked", output_dir=root, config=offline_config(),
                    fetcher=OfflineFetcher({}))
            self.assertEqual(list(Path(root).rglob("*.json")), [])

    def test_tampered_raw_bytes_detected(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(run("scrape", "offline-test-c", output_dir=root,
                            config=offline_config(), fetcher=OfflineFetcher(offline_pages())))
            manifest = json.loads(path.read_text())
            data = Path(root) / manifest["files"][0]["path"]
            data.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                load_batch(str(path), dry_run=True)

    def test_stale_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(run("scrape", "offline-test-d", output_dir=root,
                            config=offline_config(), fetcher=OfflineFetcher(offline_pages())))
            manifest = json.loads(path.read_text())
            manifest["collected_at"] = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "stale"):
                load_batch(str(path), dry_run=True)


if __name__ == "__main__":
    unittest.main()
