"""Validate source-neutral product offers. Never invent missing identifiers/prices."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
import re

CATEGORIES = {"television", "dishwasher"}


def normalize_price(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError("boolean is not a price")
    try:
        price = Decimal(str(value).strip().replace("$", "").replace(",", ""))
    except InvalidOperation as exc:
        raise ValueError(f"invalid price: {value!r}") from exc
    if not price.is_finite() or price < 0:
        raise ValueError("price must be nonnegative and finite")
    return price.quantize(Decimal("0.01"))


def brand_key(brand: str) -> str:
    """Canonical manufacturer alias key; do not rewrite display branding."""
    compact = re.sub(r"[^a-z0-9]", "", brand.casefold())
    return {"lgelectronics": "lg", "generalelectric": "ge",
            "geappliances": "ge", "samsungelectronics": "samsung"}.get(compact, compact)


def model_key(model: str) -> str:
    """Comparable key only; original model suffix/case retained for display."""
    return re.sub(r"[^A-Z0-9]", "", model.upper())


def normalize_listing(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("listing must be a JSON object")
    for field in ("retailer", "source_url", "brand", "model", "category", "title"):
        if not isinstance(raw.get(field), str) or not raw[field].strip():
            raise ValueError(f"missing required field {field}")
    url = urlparse(raw["source_url"].strip())
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise ValueError("source_url must be a public HTTPS URL")
    category = raw["category"].strip().lower().replace("-", "_").replace(" ", "_")
    if category not in CATEGORIES:
        raise ValueError(f"unsupported category: {category}")
    if not model_key(raw["model"]):
        raise ValueError("manufacturer model has no alphanumeric characters")
    ts = raw.get("collected_at") or datetime.now(timezone.utc).isoformat()
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValueError("collected_at must be ISO-8601") from exc
    if dt.tzinfo is None:
        raise ValueError("collected_at requires a timezone")
    specifications = raw.get("specifications") or {}
    if not isinstance(specifications, dict):
        raise ValueError("specifications must be an object")
    gtin = str(raw.get("gtin") or "").strip() or None
    if gtin and (not gtin.isdigit() or not 8 <= len(gtin) <= 14):
        raise ValueError("GTIN must be 8..14 digits")
    if (raw.get("currency") or "USD").upper() != "USD":
        raise ValueError("only USD is supported")
    if raw.get("source_type") != "scrape":
        raise ValueError("only real scraped source records are loadable")
    condition = (raw.get("condition") or "unknown").lower()
    if condition not in {"unknown", "new", "used", "refurbished", "open_box"}:
        raise ValueError("unrecognized condition")
    return {
        "retailer": raw["retailer"].strip().lower(),
        "source_url": raw["source_url"].strip(),
        "source_listing_id": str(raw.get("source_listing_id") or "").strip() or None,
        "title": raw["title"].strip(),
        "brand": raw["brand"].strip(),
        "model": raw["model"].strip(),
        "model_key": model_key(raw["model"]),
        "brand_key": brand_key(raw["brand"]),
        "category": category,
        "price_usd": normalize_price(raw.get("price")),
        "currency": "USD",
        "specifications": specifications,
        "collected_at": dt.astimezone(timezone.utc),
        "source_type": "scrape",
        "gtin": gtin,
        "seller": str(raw.get("seller") or "").strip() or None,
        "condition": condition,
        "availability": str(raw.get("availability") or "unknown").strip()[:80].lower(),
        "extraction_method": str(raw.get("extraction_method") or "unknown")[:40],
    }
