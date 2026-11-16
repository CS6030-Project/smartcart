"""Small YAML config loader; Cloud Run env vars override deployment-specific values."""
from __future__ import annotations
import os
from pathlib import Path
import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"


def load_config(path: str | None = None) -> dict:
    config_path = Path(path or os.getenv("INGESTION_CONFIG", DEFAULT_CONFIG))
    with config_path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream) or {}
    if not isinstance(config, dict) or not isinstance(config.get("collector"), dict) or not isinstance(config.get("loader"), dict):
        raise ValueError("config requires collector and loader sections")
    collector = config["collector"]
    for key in ("max_records",):
        if int(collector.get(key, 0)) < 1:
            raise ValueError(f"collector.{key} must be positive")
    if not isinstance(collector.get("retailers"), list) or not collector["retailers"]:
        raise ValueError("collector.retailers must be a nonempty list")
    return config


def positive_int(value: int | str, label: str) -> int:
    number = int(value)
    if number <= 0:
        raise ValueError(f"{label} must be positive")
    return number
