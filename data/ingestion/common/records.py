"""Source-agnostic listing normalization. Unknown values are preserved as null, never invented."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
import re

CATEGORIES = {'refrigerator', 'television', 'dishwasher', 'washer', 'air_conditioner'}


def normalize_price(value):
    if value is None or value == '':
        return None
    if isinstance(value, bool):
        raise ValueError('boolean is not a price')
    try:
        price = Decimal(str(value).strip().replace('$', '').replace(',', ''))
    except InvalidOperation as exc:
        raise ValueError(f'invalid price: {value!r}') from exc
    if not price.is_finite() or price < 0:
        raise ValueError('price must be nonnegative and finite')
    return price.quantize(Decimal('0.01'))


def normalize_listing(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError('listing must be a JSON object')
    for field in ('retailer', 'source_url', 'brand', 'model', 'category', 'title'):
        if not isinstance(raw.get(field), str) or not raw[field].strip():
            raise ValueError(f'missing required field {field}')
    url = urlparse(raw['source_url'].strip())
    if url.scheme not in ('https', 'http') or not url.netloc:
        raise ValueError('source_url must be an absolute HTTP(S) URL')
    category = raw['category'].strip().lower().replace('-', '_').replace(' ', '_')
    if category not in CATEGORIES:
        raise ValueError(f'unsupported category: {category}')
    ts = raw.get('collected_at') or datetime.now(timezone.utc).isoformat()
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except (ValueError, AttributeError) as exc:
        raise ValueError('collected_at must be ISO 8601') from exc
    if dt.tzinfo is None:
        raise ValueError('collected_at must include timezone')
    specs = raw.get('specifications') or {}
    if not isinstance(specs, dict):
        raise ValueError('specifications must be an object')
    # Never infer an exact model from a product title or discard meaningful identifier suffixes.
    capacity = specs.get('capacityCubicFeet')
    if capacity is not None:
        match = re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(?:cu\.?\s*ft\.?|cubic\s*feet)?\s*', str(capacity), re.I)
        if not match:
            raise ValueError('invalid capacityCubicFeet')
        capacity = float(match.group(1))
    normalized_specs = dict(specs)
    if capacity is not None:
        normalized_specs['capacityCubicFeet'] = capacity
    if 'iceMaker' in normalized_specs and normalized_specs['iceMaker'] is not None and not isinstance(normalized_specs['iceMaker'], bool):
        raise ValueError('iceMaker must be boolean when supplied')
    if (raw.get('currency') or 'USD').upper() != 'USD':
        raise ValueError('only USD prices are supported without currency conversion')
    price = normalize_price(raw.get('price'))
    return {
        'retailer': raw['retailer'].strip().lower(),
        'source_url': raw['source_url'].strip(),
        'source_listing_id': str(raw.get('source_listing_id') or '').strip() or None,
        'title': raw['title'].strip(),
        'brand': raw['brand'].strip(),
        'model': raw['model'].strip(),
        'category': category,
        'price_usd': price,
        'currency': (raw.get('currency') or 'USD').upper(),
        'specifications': normalized_specs,
        'collected_at': dt.astimezone(timezone.utc),
        'source_type': (raw.get('source_type') or 'unknown').lower(),
    }
