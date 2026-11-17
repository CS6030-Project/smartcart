"""Bounded live product ingestion to immutable local/GCS batches.

The same extraction logic is used locally and in Cloud Run. Neither environment
manufactures or substitutes listings when retailers cannot be fetched.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from collector.scraping.catalog import CatalogCollector
from common.config import load_config, positive_int
from common.records import normalize_listing

LOG = logging.getLogger(__name__)


def run(source: str, run_id: str, *, bucket_name: str | None = None,
        output_dir: str | None = None, max_records: int = 25,
        config: dict | None = None, retailer_filter: set[str] | None = None,
        fetcher=None, namespace: str | None = None) -> str:
    if source != "scrape":
        raise ValueError("only real scraping source is supported")
    if not run_id or not all(ch.isalnum() or ch in "-_" for ch in run_id):
        raise ValueError("run_id must contain only letters, numbers, hyphens or underscores")
    max_records = positive_int(max_records, "max_records")
    if namespace and not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,39}", namespace):
        raise ValueError("namespace must contain only lowercase letters, digits, underscores or hyphens")
    if bool(bucket_name) == bool(output_dir):
        raise ValueError("provide exactly one of bucket_name or output_dir")
    col_config = config or load_config()["collector"]
    collector = CatalogCollector(col_config, retailer_filter=retailer_filter,
                                 max_records=max_records, fetcher=fetcher)
    now = datetime.now(timezone.utc)
    scope = f"{namespace}/" if namespace else ""
    prefix = f"{scope}raw/{now:%Y-%m-%d}/{run_id}"
    raw_path = f"{prefix}/scrape.jsonl.gz"
    manifest_path = f"{scope}manifests/{run_id}.json"
    LOG.info("ingestion start run_id=%s target=%s namespace=%s max_records=%s",
             run_id, "gs://" + bucket_name if bucket_name else str(output_dir),
             namespace or "default", max_records)

    # Spool a compressed batch on disk instead of materializing every row in RAM.
    with tempfile.TemporaryDirectory(prefix="smartcart-collector-") as temp:
        gz_path = Path(temp) / "scrape.jsonl.gz"
        accepted = 0
        priced = 0
        with gz_path.open("wb") as output:
            with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as gz:
                for row in collector.records():
                    # Validate with the *same* normalization contract as the loader.
                    try:
                        checked = normalize_listing(row)
                    except ValueError as exc:
                        collector._fail(row.get("retailer", "unknown"), row.get("source_url", ""), exc)
                        continue
                    gz.write((json.dumps(row, separators=(",", ":")) + "\n").encode())
                    accepted += 1
                    if checked["price_usd"] is not None:
                        priced += 1
        LOG.info("collection summary run_id=%s accepted=%s priced=%s attempted=%s failed=%s per_retailer=%s",
                 run_id, accepted, priced, collector.stats.attempted,
                 collector.stats.failed, collector.diagnostics())
        if accepted == 0:
            detail = "; ".join(collector.errors[:3]) or "no products were discovered"
            raise RuntimeError(f"zero valid real products; batch not published: {detail}")
        digest = hashlib.sha256()
        with gz_path.open("rb") as content:
            for chunk in iter(lambda: content.read(1024 * 1024), b""):
                digest.update(chunk)
        manifest = {
            "schema_version": 1, "run_id": run_id, "status": "COMPLETED",
            "source": "scrape", "source_type": "scrape", "collected_at": now.isoformat(),
            "record_count": accepted,
            "priced_records": priced,
            "attempted": collector.stats.attempted,
            "failed": collector.stats.failed,
            "discovered": collector.stats.discovered,
            "namespace": namespace,
            "diagnostics": {"retailers": collector.diagnostics(),
                            "error_examples": collector.errors[:9]},
            "files": [{"path": raw_path, "sha256": digest.hexdigest(), "records": accepted}],
        }
        manifest_bytes = json.dumps(manifest, indent=2).encode()
        if bucket_name:
            from google.cloud import storage
            bucket = storage.Client().bucket(bucket_name)
            bucket.blob(raw_path).upload_from_filename(str(gz_path), content_type="application/gzip", if_generation_match=0)
            bucket.blob(manifest_path).upload_from_string(manifest_bytes, content_type="application/json", if_generation_match=0)
            uri = f"gs://{bucket_name}/{manifest_path}"
        else:
            root = Path(output_dir)
            destination = root / raw_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as target, gz_path.open("rb") as content:
                shutil.copyfileobj(content, target)
            destination = root / manifest_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as handle:
                handle.write(manifest_bytes)
            uri = str(destination)
    LOG.info("scrape complete: %s records (%s priced), %s attempts, %s failed",
             accepted, priced, collector.stats.attempted, collector.stats.failed)
    return uri


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    p = argparse.ArgumentParser(description="SmartCart real product collection")
    p.add_argument("--config", help="YAML source configuration")
    p.add_argument("--source", choices=("scrape",))
    p.add_argument("--max-records", type=int, help="Maximum accepted products in this run")
    p.add_argument("--retailers", help="Comma-separated enabled retailer keys")
    p.add_argument("--discovery-mode", choices=("seeds", "category"))
    p.add_argument("--run-id", default=os.getenv("RUN_ID") or f"manual-{uuid4().hex[:12]}")
    p.add_argument("--bucket", default=os.getenv("RAW_BUCKET"))
    p.add_argument("--output-dir")
    p.add_argument("--namespace", help="Optional isolated raw/manifest prefix, e.g. local-test")
    p.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING"),
                   default=os.getenv("LOG_LEVEL", "INFO").upper())
    args = p.parse_args()
    logging.getLogger().setLevel(args.log_level)
    cfg = load_config(args.config)["collector"]
    source = args.source or os.getenv("SOURCE_MODE") or cfg["source"]
    size = args.max_records if args.max_records is not None else os.getenv("MAX_RECORDS", cfg["max_records"])
    mode = args.discovery_mode or os.getenv("DISCOVERY_MODE")
    if mode:
        if mode not in ("seeds", "category"):
            p.error("invalid discovery mode")
        cfg["discovery_mode"] = mode
    filter_str = args.retailers or os.getenv("RETAILERS")
    subset = set(x.strip() for x in filter_str.split(",") if x.strip()) if filter_str else None
    uri = run(source, args.run_id, bucket_name=args.bucket,
              output_dir=args.output_dir, max_records=int(size), config=cfg,
              retailer_filter=subset, namespace=args.namespace)
    print(json.dumps({"manifest_uri": uri, "source": source, "max_records": int(size)}))


if __name__ == "__main__":
    main()
