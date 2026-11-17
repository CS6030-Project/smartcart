"""Evidence-based product extraction (JSON-LD first, visible HTML fallback).

Unknown values remain unknown. A seed's expected model is used to *validate*,
never to invent an identifier absent from the page.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup
from collector.scraping.adapters import RetailerAdapter


class ExtractionError(ValueError):
    pass


def _nodes(data: Any):
    if isinstance(data, list):
        for item in data:
            yield from _nodes(item)
    elif isinstance(data, dict):
        yield data
        for key in ("@graph", "mainEntity", "hasVariant"):
            if key in data:
                yield from _nodes(data[key])


def _is_product(obj: dict) -> bool:
    types = obj.get("@type", [])
    if isinstance(types, str):
        types = [types]
    return any(str(t).split("/")[-1].lower() == "product" for t in types)


def _first(value):
    if isinstance(value, list):
        return _first(value[0]) if value else None
    return value


def _text(value) -> str | None:
    if isinstance(value, dict):
        value = value.get("name") or value.get("value")
    value = _first(value)
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _meta(soup: BeautifulSoup, *names: str) -> str | None:
    for name in names:
        for attr in ("property", "name", "itemprop"):
            tag = soup.find("meta", attrs={attr: name})
            if tag and tag.get("content"):
                return tag["content"].strip()
    return None


def _offer_price(product: dict) -> tuple[str | None, str | None, str | None, str | None]:
    offers = product.get("offers") or []
    if isinstance(offers, dict):
        offers = [offers]
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        price = offer.get("price")
        if price is None and isinstance(offer.get("priceSpecification"), dict):
            price = offer["priceSpecification"].get("price")
        # AggregateOffer.lowPrice is a range, not a guaranteed direct selling price.
        if price is None and "AggregateOffer" in str(offer.get("@type", "")):
            continue
        if price is not None:
            return (str(price), _text(offer.get("priceCurrency")),
                    _text(offer.get("availability")), _text(offer.get("seller")))
    return None, None, None, None


def _extract_size(text: str, category: str) -> dict:
    specs: dict = {}
    if category == "television":
        match = re.search(r"\b(\d{2,3})\s*(?:[\"“”]|-?\s*inch(?:es)?\b|\s*in\b)", text, re.I)
        if match and 20 <= int(match.group(1)) <= 120:
            specs["screenInches"] = int(match.group(1))
        for token in ("OLED", "QLED", "Mini LED", "LED"):
            if re.search(r"\b" + re.escape(token) + r"\b", text, re.I):
                specs["displayType"] = token
                break
        if re.search(r"\b4K\b", text, re.I):
            specs["resolution"] = "4K"
    elif category == "dishwasher":
        match = re.search(r"\b(\d{2}(?:\.\d+)?)\s*(?:[\"“”]|-?\s*inch(?:es)?\b|\s*in\b)", text, re.I)
        if match and 17 <= float(match.group(1)) <= 25:
            specs["widthInches"] = float(match.group(1))
        match = re.search(r"\b(\d{2})\s*dBA\b", text, re.I)
        if match and 35 <= int(match.group(1)) <= 70:
            specs["noiseDb"] = int(match.group(1))
    for finish in ("fingerprint resistant stainless", "stainless steel", "slate", "black stainless", "white", "black"):
        if re.search(re.escape(finish), text, re.I):
            specs["finish"] = finish.title()
            break
    return specs


def extract_product(html: str, url: str, adapter: RetailerAdapter, category: str,
                    *, expected_model: str | None = None, expected_brand: str | None = None) -> dict:
    if category not in {"television", "dishwasher"}:
        raise ExtractionError(f"unsupported category: {category}")
    if not adapter.is_product_url(url):
        raise ExtractionError("not a supported retailer product URL")
    soup = BeautifulSoup(html, "html.parser")
    products: list[dict] = []
    for tag in soup.find_all("script", type=lambda v: v and "ld+json" in v.lower()):
        try:
            payload = json.loads(tag.string or tag.get_text())
        except (ValueError, TypeError):
            continue
        products.extend(obj for obj in _nodes(payload) if _is_product(obj))
    # Favor the Product whose manufacturer model matches the independently verified seed.
    product = next((p for p in products if expected_model and
                    _text(p.get("model") or p.get("mpn")) and
                    _text(p.get("model") or p.get("mpn")).upper() == expected_model.upper()),
                   products[0] if products else {})
    title = (_text(product.get("name")) or _meta(soup, "og:title", "twitter:title") or
             (soup.h1.get_text(" ", strip=True) if soup.h1 else None))
    body = soup.get_text(" ", strip=True)
    description = (_text(product.get("description")) or
                   _meta(soup, "description", "og:description", "twitter:description"))
    if description:
        # Descriptions can contain HTML markup or nonbreaking/duplicated whitespace.
        description = re.sub(r"\s+", " ", BeautifulSoup(description, "html.parser")
                             .get_text(" ", strip=True)).strip()[:4000] or None
        if description and description.casefold() == (title or "").casefold():
            description = None
    brand = _text(product.get("brand")) or _meta(soup, "product:brand", "brand")
    if not brand and expected_brand and re.search(r"\b" + re.escape(expected_brand) + r"\b", (title or "") + " " + body[:1500], re.I):
        brand = expected_brand
    if not brand and title:
        known_brands = ("LG Electronics", "KitchenAid", "Frigidaire", "Whirlpool", "Samsung", "Bosch", "Hisense", "Maytag", "Miele", "Sony", "TCL", "Vizio", "LG", "GE")
        brand = next((b for b in known_brands if re.match(r"^" + re.escape(b) + r"\b", title, re.I)), None)
    model = _text(product.get("model")) or _text(product.get("mpn")) or adapter.model_from_text(body)
    if not model and expected_model and re.search(r"(?<!\w)" + re.escape(expected_model) + r"(?!\w)", (title or "") + " " + body, re.I):
        model = expected_model
    if not model or not brand or not title:
        raise ExtractionError("missing verified manufacturer model, brand or title")
    if expected_model and re.sub(r"[^A-Z0-9]", "", model.upper()) != re.sub(r"[^A-Z0-9]", "", expected_model.upper()):
        raise ExtractionError(f"page model {model!r} conflicts with selected model {expected_model!r}")
    if expected_brand and brand.casefold() != expected_brand.casefold() and expected_brand.casefold() not in brand.casefold():
        raise ExtractionError(f"page brand {brand!r} conflicts with selected brand {expected_brand!r}")
    price, currency, availability, seller = _offer_price(product)
    if price is None:
        price = _meta(soup, "product:price:amount", "price", "product:price")
    if price is None:
        # Only an explicitly labelled offer price, never the first arbitrary $ amount
        # in the document (which may be MSRP, financing, a bundle or a variant).
        for selector in ("[itemprop=price]", "[data-testid=customer-price]", "[data-testid=product-price]"):
            tag = soup.select_one(selector)
            if not tag:
                continue
            candidate = tag.get("content") or tag.get_text(" ", strip=True)
            match = re.search(r"\$?\s*([0-9][0-9,]*\.[0-9]{2})", candidate)
            if match:
                price = match.group(1)
                break
    if not currency:
        currency = _meta(soup, "product:price:currency", "priceCurrency") or "USD"
    if not availability:
        availability = _meta(soup, "product:availability", "availability")
    gtin = next((_text(product[k]) for k in ("gtin14", "gtin13", "gtin12", "gtin", "gtin8") if product.get(k)), None)
    if not gtin:
        visible_id = re.search(r"\b(?:UPC|GTIN(?:-1[234])?)\s*#?\s*:?\s*([0-9]{12,14})\b", body, re.I)
        gtin = visible_id.group(1) if visible_id else None
    if gtin and (not gtin.isdigit() or not 8 <= len(gtin) <= 14):
        gtin = None
    specs = _extract_size(title, category)
    if description:
        for key, value in _extract_size(description, category).items():
            specs.setdefault(key, value)
    # Normalized structured properties where semantics are sufficiently explicit.
    extra = product.get("additionalProperty") or []
    if isinstance(extra, dict):
        extra = [extra]
    for item in extra if isinstance(extra, list) else []:
        if not isinstance(item, dict):
            continue
        key = (_text(item.get("name")) or "").casefold().strip()
        value = _text(item.get("value"))
        if not value:
            continue
        if key in ("color", "finish", "finish color"):
            specs.setdefault("finish", value[:100])
        elif category == "television" and key in ("display technology", "display type"):
            specs.setdefault("displayType", value[:80])
        elif category == "television" and key in ("resolution", "display resolution"):
            specs.setdefault("resolution", value[:80])
        elif category == "dishwasher" and key in ("noise level", "noise rating"):
            match = re.search(r"(\d{2})\s*(?:dba|db)?", value, re.I)
            if match and 35 <= int(match.group(1)) <= 70:
                specs.setdefault("noiseDb", int(match.group(1)))
    for key, dest in (("color", "finish"), ("size", "size")):
        val = _text(product.get(key))
        if val and dest not in specs:
            specs[dest] = val
    condition = "unknown"
    condition_text = _text(product.get("itemCondition")) or ""
    if "refurb" in condition_text.lower():
        condition = "refurbished"
    elif "used" in condition_text.lower() or "openbox" in condition_text.lower():
        condition = "used"
    elif "new" in condition_text.lower():
        condition = "new"
    return {
        "retailer": adapter.key,
        "source_url": adapter.normalize_url(url),
        "source_listing_id": _text(product.get("sku")) or adapter.sku_from_text(body),
        "brand": brand,
        "model": model,
        "category": category,
        "title": title,
        "description": description,
        "price": price,
        "currency": currency.upper(),
        "gtin": gtin,
        "condition": condition,
        "seller": seller,
        "availability": (availability or "unknown").split("/")[-1].lower(),
        "specifications": specs,
        "source_type": "scrape",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "extraction_method": "jsonld" if product else "html",
    }
