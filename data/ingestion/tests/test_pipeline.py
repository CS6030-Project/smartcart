import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from collector.main import run
from collector.sources import fixtures
from common.config import load_config
from common.records import normalize_listing, normalize_price
from loader.main import load_batch


class SmartCartDataTests(unittest.TestCase):
    def test_fixture_has_25_distinct_listings(self):
        rows = list(fixtures())
        self.assertEqual(len(rows), 25)
        self.assertEqual(len({x['source_url'] for x in rows}), 25)
        self.assertTrue(all(x['source_type'] == 'synthetic' for x in rows))

    def test_scalable_fixture_500(self):
        rows = list(fixtures(500))
        self.assertEqual(len(rows), 500)
        self.assertEqual(len({r['source_url'] for r in rows}), 500)
        self.assertEqual(len({r['retailer'] for r in rows}), 5)
        self.assertEqual(len({r['model'] for r in rows}), 100)

    def test_yaml_config(self):
        config = load_config()
        self.assertEqual(config['collector']['max_records'], 25)
        self.assertEqual(len(config['collector']['retailers']), 5)

    def test_larger_local_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = run('fixtures', 'test-500', output_dir=tmp, max_records=500)
            report = load_batch(mp, dry_run=True)
            self.assertEqual((report['accepted'], report['rejected']), (500, 0))

    def test_non_usd_without_conversion_is_rejected(self):
        row = list(fixtures())[0]
        row['currency'] = 'EUR'
        with self.assertRaisesRegex(ValueError, 'USD'):
            normalize_listing(row)

    def test_prices(self):
        self.assertEqual(str(normalize_price('$1,499.99')), '1499.99')
        self.assertIsNone(normalize_price(None))
        with self.assertRaises(ValueError):
            normalize_price('-1')

    def test_model_preserves_variant_suffix(self):
        row = list(fixtures())[0]
        row['model'] = 'RF-250-SS'
        self.assertEqual(normalize_listing(row)['model'], 'RF-250-SS')

    def test_missing_required_fields_rejected(self):
        row = list(fixtures())[0]
        del row['model']
        with self.assertRaisesRegex(ValueError, 'model'):
            normalize_listing(row)

    def test_local_collector_loader_dryrun(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = run('fixtures', 'test-001', output_dir=tmp)
            self.assertTrue(Path(manifest_path).exists())
            report = load_batch(manifest_path, dry_run=True)
            self.assertEqual((report['accepted'], report['rejected']), (25, 0))
            self.assertTrue(list((Path(tmp) / 'raw').rglob('*.jsonl.gz')))
            with self.assertRaises(FileExistsError):
                run('fixtures', 'test-001', output_dir=tmp)

    def test_tamper_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = Path(run('fixtures', 'test-002', output_dir=tmp))
            manifest = json.loads(mp.read_text())
            data = Path(tmp) / manifest['files'][0]['path']
            data.write_bytes(b'corrupted')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                load_batch(str(mp), dry_run=True)

    def test_stale_manifest_rejected_and_replay_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = Path(run('fixtures', 'test-003', output_dir=tmp))
            manifest = json.loads(mp.read_text())
            manifest['collected_at'] = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
            mp.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'stale'):
                load_batch(str(mp), dry_run=True)
            self.assertEqual(load_batch(str(mp), dry_run=True, allow_stale=True)['accepted'], 25)

    def test_invalid_category(self):
        row = list(fixtures())[0]
        row['category'] = 'toaster'
        with self.assertRaisesRegex(ValueError, 'unsupported category'):
            normalize_listing(row)

    def test_bestbuy_authorized_adapter_filters_and_limits(self):
        from collector.sources import bestbuy_api
        from unittest.mock import Mock
        example = {'products': [
            {'sku': 123, 'name': 'Example fridge', 'manufacturer': 'Acme',
             'modelNumber': 'RF-001-SS', 'url': 'https://example.com/123',
             'salePrice': 1200, 'categoryPath': [{'name': 'Refrigerators'}]},
            {'sku': 124, 'name': 'Untyped item', 'manufacturer': 'Acme',
             'modelNumber': 'X', 'url': 'https://example.com/124',
             'categoryPath': [{'name': 'Video Games'}]},
        ]}
        fake = Mock()
        fake.json.return_value = example
        fake.raise_for_status.return_value = None
        with patch.dict('os.environ', {'BESTBUY_API_KEY': 'test-key'}), \
             patch('collector.sources.requests.get', return_value=fake) as get:
            records = list(bestbuy_api(max_records=1, page_size=10,
                                       max_pages=1, searches=['refrigerator']))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['model'], 'RF-001-SS')
        self.assertEqual(records[0]['source_type'], 'bestbuy_api')
        self.assertIn('search=refrigerator', get.call_args.args[0])

    def test_bestbuy_requires_api_key(self):
        from collector.sources import bestbuy_api
        with patch.dict('os.environ', {'BESTBUY_API_KEY': ''}):
            with self.assertRaisesRegex(RuntimeError, 'BESTBUY_API_KEY'):
                list(bestbuy_api())


if __name__ == '__main__':
    unittest.main()
