"""Collect a bounded batch of raw listings to local disk or Cloud Storage."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from common.config import load_config, positive_int
from collector.sources import fixtures, bestbuy_api


def run(source: str, run_id: str, *, bucket_name: str | None = None,
        output_dir: str | None = None, max_records: int = 25,
        retailers: list[str] | None = None, bestbuy: dict | None = None,
        max_pages: int | None = None) -> str:
    if not run_id or not all(ch.isalnum() or ch in "-_" for ch in run_id):
        raise ValueError("run_id must consist of letters, numbers, hyphens or underscores")
    max_records = positive_int(max_records, "max_records")
    if bool(bucket_name) == bool(output_dir):
        raise ValueError("provide exactly one of bucket_name or output_dir")
    if source == "fixtures":
        provider = fixtures(max_records, retailers=retailers)
    elif source == "bestbuy":
        options = dict(bestbuy or {})
        if max_pages is not None:
            options["max_pages"] = max_pages
        provider = bestbuy_api(max_records=max_records, **options)
    else:
        raise ValueError(f"unsupported source: {source}")
    rows = list(provider)
    if not rows:
        raise RuntimeError("collection returned zero records; no completed manifest written")
    now = datetime.now(timezone.utc)
    prefix = f"raw/{now:%Y-%m-%d}/{run_id}"
    payload = gzip.compress(
        "".join(json.dumps(row, separators=(",", ":"), default=str) + "\n" for row in rows).encode(),
        mtime=0,
    )
    path = f"{prefix}/{source}.jsonl.gz"
    manifest_path = f"manifests/{run_id}.json"
    manifest = {
        "schema_version": 1, "run_id": run_id, "status": "COMPLETED",
        "source": source, "source_type": "synthetic" if source == "fixtures" else "api",
        "collected_at": now.isoformat(), "record_count": len(rows),
        "files": [{"path": path, "sha256": hashlib.sha256(payload).hexdigest(), "records": len(rows)}],
    }
    manifest_bytes = json.dumps(manifest, indent=2).encode()
    if bucket_name:
        from google.cloud import storage
        bucket = storage.Client().bucket(bucket_name)
        bucket.blob(path).upload_from_string(payload, content_type="application/gzip", if_generation_match=0)
        bucket.blob(manifest_path).upload_from_string(manifest_bytes, content_type="application/json", if_generation_match=0)
        return f"gs://{bucket_name}/{manifest_path}"
    root = Path(output_dir)
    for relative_path, body in ((path, payload), (manifest_path, manifest_bytes)):
        destination = root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as handle:
            handle.write(body)
    return str(root / manifest_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="YAML configuration file (default: data/ingestion/config.yaml)")
    parser.add_argument("--source", choices=("fixtures", "bestbuy"))
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--run-id", default=os.getenv("RUN_ID") or f"manual-{uuid4().hex[:12]}")
    parser.add_argument("--bucket", default=os.getenv("RAW_BUCKET"))
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    config = load_config(args.config)["collector"]
    source = args.source or os.getenv("SOURCE_MODE") or config["source"]
    max_records = args.max_records or os.getenv("MAX_RECORDS") or config["max_records"]
    uri = run(source, args.run_id, bucket_name=args.bucket, output_dir=args.output_dir,
              max_records=max_records, retailers=config["retailers"],
              bestbuy=config.get("bestbuy"), max_pages=args.max_pages)
    print(json.dumps({"manifest_uri": uri, "source": source, "max_records": int(max_records)}))


if __name__ == "__main__":
    main()
