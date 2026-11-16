"""Load and validate the local/cloud collection configuration."""
from __future__ import annotations
import os
from pathlib import Path
import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"


def load_config(path: str | None = None) -> dict:
    config_path = Path(path or os.getenv("INGESTION_CONFIG", DEFAULT_CONFIG))
    with config_path.open(encoding="utf-8") as stream:
        cfg = yaml.safe_load(stream) or {}
    if not isinstance(cfg, dict) or not isinstance(cfg.get("collector"), dict) or not isinstance(cfg.get("loader"), dict):
        raise ValueError("config requires collector and loader sections")
    col = cfg["collector"]
    if col.get("source", "scrape") != "scrape":
        raise ValueError("collector.source must be scrape")
    if int(col.get("max_records", 0)) < 1:
        raise ValueError("collector.max_records must be positive")
    if col.get("discovery_mode", "seeds") not in ("seeds", "category"):
        raise ValueError("discovery_mode must be seeds or category")
    if not isinstance(col.get("retailers"), dict) or not col["retailers"]:
        raise ValueError("collector.retailers must be a nonempty mapping")
    for retailer, settings in col["retailers"].items():
        if not isinstance(settings, dict):
            raise ValueError(f"retailer {retailer} requires configuration")
        for seed in settings.get("products", []):
            if not isinstance(seed, dict) or not all(seed.get(key) for key in ("url", "category")):
                raise ValueError(f"invalid configured seed for {retailer}")
    return cfg


def positive_int(value: int | str, label: str) -> int:
    number = int(value)
    if number <= 0:
        raise ValueError(f"{label} must be positive")
    return number
