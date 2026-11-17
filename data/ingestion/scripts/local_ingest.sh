#!/usr/bin/env bash
        # Run from any location: bash data/ingestion/scripts/local_ingest.sh [retailers] [max_records]
        # Reuses compose.yaml and its existing named Postgres volume. Never deletes the volume.
        set -euo pipefail
        ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
        cd "$ROOT"
        if [[ ! -f .env ]]; then
          echo "Missing .env; copy .env.example, set local PostgreSQL credentials, and retry." >&2
          exit 1
        fi
        # .env is local developer-owned configuration, never committed to Git.
        set -a
        source ./.env
        set +a
        : "${POSTGRES_USER:?POSTGRES_USER required in .env}"
        : "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required in .env}"
        : "${POSTGRES_DB:?POSTGRES_DB required in .env}"
        RETAILERS="${1:-abt,homedepot,bestbuy}"
        MAX_RECORDS="${2:-9}"
        RUN_ID="local-$(date -u +%Y%m%dT%H%M%S)-$$"
        OUT="${LOCAL_INGEST_DIR:-$ROOT/.local/ingestion}"
        PYTHON="${PYTHON:-python3}"
        echo "[smartcart] starting or reusing compose postgres (data retained)"
        docker compose up -d --wait postgres
        cd "$ROOT/data/ingestion"
        echo "[smartcart] scraping retailer=$RETAILERS max_records=$MAX_RECORDS run_id=$RUN_ID"
        "$PYTHON" -m collector.main --source scrape --retailers "$RETAILERS" \
          --max-records "$MAX_RECORDS" --run-id "$RUN_ID" --output-dir "$OUT"
        MANIFEST="$OUT/manifests/$RUN_ID.json"
        echo "[smartcart] validating completed batch locally: $MANIFEST"
        "$PYTHON" -m loader.main --manifest-uri "$MANIFEST" --dry-run
        export DB_HOST=127.0.0.1
        export DB_PORT="${POSTGRES_PORT:-5432}"
        export DB_NAME="$POSTGRES_DB"
        export DB_USER="$POSTGRES_USER"
        export DB_PASSWORD="$POSTGRES_PASSWORD"
        echo "[smartcart] writing to LOCAL Postgres only (not Cloud SQL)"
        "$PYTHON" -m loader.main --manifest-uri "$MANIFEST"
        echo "[smartcart] done; local manifest: $MANIFEST"
        echo "[smartcart] query with: docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB"
