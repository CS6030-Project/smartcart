"""Load an exact, completed raw batch from GCS or local disk into PostgreSQL."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from common.records import normalize_listing
from common.config import load_config, positive_int


def load_batch(manifest_uri: str, *, dry_run: bool = False, allow_stale: bool = False,
               max_age_hours: int = 48) -> dict:
    if manifest_uri.startswith('gs://'):
        from google.cloud import storage
        parts = urlparse(manifest_uri)
        bucket_name = parts.netloc
        manifest_path = parts.path.lstrip('/')
        bucket = storage.Client().bucket(bucket_name)
        manifest = json.loads(bucket.blob(manifest_path).download_as_bytes())
        read_bytes = lambda name: bucket.blob(name).download_as_bytes()
        origin = f'gs://{bucket_name}/'
    else:
        manifest_path = Path(manifest_uri).resolve()
        # Collector writes local manifests in <root>/manifests/<run>.json.
        root = manifest_path.parent.parent
        manifest = json.loads(manifest_path.read_text())
        read_bytes = lambda name: (root / name).read_bytes()
        origin = str(root) + '/'

    if manifest.get('status') != 'COMPLETED' or manifest.get('schema_version') != 1:
        raise ValueError('not a supported completed batch')
    if not manifest.get('files') or not manifest.get('run_id'):
        raise ValueError('manifest is incomplete')
    collected = datetime.fromisoformat(manifest['collected_at'].replace('Z', '+00:00'))
    if collected.tzinfo is None:
        raise ValueError('manifest missing timezone')
    age_hours = (datetime.now(timezone.utc) - collected).total_seconds() / 3600
    if not allow_stale and (age_hours > max_age_hours or age_hours < -1):
        raise ValueError(f'batch is stale or future-dated: {age_hours:.1f} hours old')

    normalized = []
    rejections = []
    seen_paths = set()
    total = 0
    for item in manifest['files']:
        name = item['path']
        if name in seen_paths or not name.startswith('raw/') or '..' in Path(name).parts:
            raise ValueError('invalid or duplicate raw object path')
        seen_paths.add(name)
        data = read_bytes(name)
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError(f'checksum mismatch: {name}')
        lines = gzip.decompress(data).decode().splitlines()
        if len(lines) != item['records']:
            raise ValueError('record count mismatch')
        total += len(lines)
        for number, line in enumerate(lines, 1):
            try:
                record = normalize_listing(json.loads(line))
                record['raw_object_uri'] = origin + name
                normalized.append(record)
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                rejections.append(f'{name}:{number}: {exc}')
    if total != manifest['record_count']:
        raise ValueError('manifest total record count mismatch')
    if not normalized:
        raise ValueError('batch has zero valid records; refusing to load')
    report = {'run_id': manifest['run_id'], 'source': manifest['source'],
              'accepted': len(normalized), 'rejected': len(rejections),
              'errors': rejections[:10], 'dry_run': dry_run}
    if dry_run:
        return report

    import psycopg
    from psycopg.types.json import Jsonb
    from pathlib import Path as PathType
    sql = (PathType(__file__).resolve().parent.parent / 'sql' / '001_catalog.sql').read_text()
    # Host may be /cloudsql/PROJECT:REGION:INSTANCE (Cloud SQL Unix socket) or localhost.
    with psycopg.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=os.getenv('DB_PORT', '5432'),
        dbname=os.getenv('DB_NAME', 'smartcart'),
        user=os.getenv('DB_USER', 'smartcart'),
        password=os.getenv('DB_PASSWORD', ''),
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute('''INSERT INTO catalog.ingestion_runs
              (run_id, manifest_uri, source, source_type, collected_at, accepted_count, rejected_count)
              VALUES (%s,%s,%s,%s,%s,%s,%s)
              ON CONFLICT(run_id) DO UPDATE SET
              finished_at=now(), accepted_count=EXCLUDED.accepted_count,
              rejected_count=EXCLUDED.rejected_count''',
              (manifest['run_id'], manifest_uri, manifest['source'], manifest['source_type'],
               collected, len(normalized), len(rejections)))
            for r in normalized:
                cur.execute('''INSERT INTO catalog.retailer_listings
                  (retailer,source_url,source_listing_id,brand,model,category,title,
                   price_usd,currency,specifications,source_type,raw_object_uri,collected_at,last_run_id)
                  VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                  ON CONFLICT(source_url) DO UPDATE SET
                   source_listing_id=EXCLUDED.source_listing_id,
                   brand=EXCLUDED.brand,model=EXCLUDED.model,category=EXCLUDED.category,
                   title=EXCLUDED.title,price_usd=EXCLUDED.price_usd,
                   currency=EXCLUDED.currency,specifications=EXCLUDED.specifications,
                   source_type=EXCLUDED.source_type,raw_object_uri=EXCLUDED.raw_object_uri,
                   collected_at=EXCLUDED.collected_at,last_run_id=EXCLUDED.last_run_id,
                   updated_at=now()
                  WHERE catalog.retailer_listings.collected_at <= EXCLUDED.collected_at''',
                  (r['retailer'], r['source_url'], r['source_listing_id'], r['brand'],
                   r['model'], r['category'], r['title'], r['price_usd'],
                   r['currency'], Jsonb(r['specifications']), r['source_type'],
                   r['raw_object_uri'], r['collected_at'], manifest['run_id']))
    return report


def latest_completed_uri(bucket_name: str, *, max_age_hours: int = 48) -> str:
    """Recovery-only discovery. Scheduled workflows ALWAYS pass the exact manifest URI."""
    if not bucket_name:
        raise ValueError('RAW_BUCKET required for --latest-completed')
    from google.cloud import storage
    client = storage.Client()
    candidates = []
    for blob in client.list_blobs(bucket_name, prefix='manifests/'):
        if blob.name.endswith('.json') and blob.time_created:
            age = (datetime.now(timezone.utc) - blob.time_created).total_seconds() / 3600
            if 0 <= age <= max_age_hours:
                candidates.append(blob)
    if not candidates:
        raise ValueError('no recent manifest found; refusing to ingest a stale batch')
    for blob in sorted(candidates, key=lambda b: b.time_created, reverse=True):
        try:
            manifest = json.loads(blob.download_as_bytes())
            if manifest.get('status') == 'COMPLETED' and manifest.get('schema_version') == 1:
                return f'gs://{bucket_name}/{blob.name}'
        except (ValueError, TypeError, json.JSONDecodeError):
            continue
    raise ValueError('no recent, completed manifest found')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest-uri', default=os.getenv('MANIFEST_URI'))
    p.add_argument('--latest-completed', action='store_true', help='Recovery only: discover newest recent completed GCS manifest')
    p.add_argument('--bucket', default=os.getenv('RAW_BUCKET'))
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--allow-stale', action='store_true')
    p.add_argument('--config')
    p.add_argument('--max-age-hours', type=int)
    args = p.parse_args()
    config = load_config(args.config)['loader']
    max_age_hours = positive_int(args.max_age_hours or os.getenv('MAX_AGE_HOURS') or config['max_age_hours'], 'max_age_hours')
    if args.latest_completed:
        if args.allow_stale:
            p.error('--latest-completed cannot be combined with --allow-stale')
        manifest_uri = latest_completed_uri(args.bucket, max_age_hours=max_age_hours)
    else:
        manifest_uri = args.manifest_uri
    if not manifest_uri:
        p.error('--manifest-uri required, or explicitly use --latest-completed (recovery only)')
    report = load_batch(manifest_uri, dry_run=args.dry_run,
                        allow_stale=args.allow_stale, max_age_hours=max_age_hours)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
