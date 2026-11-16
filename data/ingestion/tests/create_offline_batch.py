"""Generate deterministic, network-free integration batch via the production collector."""
import argparse
import json
from collector.main import run
from tests.support import OfflineFetcher, offline_config, offline_pages

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()
    path = run("scrape", "ci-offline-batch", output_dir=args.output_dir,
               max_records=3, config=offline_config(), fetcher=OfflineFetcher(offline_pages()))
    print(json.dumps({"manifest_uri": path, "records": 3}))
