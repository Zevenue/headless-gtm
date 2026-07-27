"""Normalized ProspectRecord schema shared by the discovery skills.

Every discovery tool (Apify Compass, and any sibling Maps/places source)
normalizes its raw output to this one 15-field record so results are
comparable and dedup-able across tools. The field list and derivation rules
are documented in 02-apify-maps-discover/reference/output-schema.md.

Stdlib only - no third-party imports.
"""

from __future__ import annotations

import csv
import json
import os
import re
from urllib.parse import urlparse

# Canonical field order - JSON key order and CSV column order both follow this.
FIELDS = [
    "name",
    "domain",
    "website",
    "phone",
    "full_address",
    "city",
    "region",
    "rating",
    "reviews_count",
    "latitude",
    "longitude",
    "place_id",
    "category",
    "last_review_date",
    "source",
]


def domain_from_url(url: str) -> str:
    """Bare lowercase host: no scheme, no www., no port, no user@, no path.

    Returns "" when there is no usable website value.
    """
    if not url:
        return ""
    url = url.strip()
    if not url:
        return ""
    if "://" not in url:
        url = "http://" + url
    host = urlparse(url).netloc or ""
    if "@" in host:  # strip any user@ prefix
        host = host.rsplit("@", 1)[-1]
    host = host.split(":", 1)[0]  # strip port
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _to_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value):
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def make_record(
    source: str,
    name: str = "",
    website: str = "",
    phone: str = "",
    full_address: str = "",
    city: str = "",
    region: str = "",
    rating=None,
    reviews_count=None,
    latitude=None,
    longitude=None,
    place_id: str = "",
    category: str = "",
    last_review_date: str = "",
) -> dict:
    """Build a normalized ProspectRecord. `domain` is derived from `website`.

    Numeric fields coerce to float/int and become None on bad or empty input
    rather than raising - one malformed row must not kill a 2,000-row run.
    """
    return {
        "name": (name or "").strip(),
        "domain": domain_from_url(website or ""),
        "website": (website or "").strip(),
        "phone": (phone or "").strip(),
        "full_address": (full_address or "").strip(),
        "city": (city or "").strip(),
        "region": (region or "").strip(),
        "rating": _to_float(rating),
        "reviews_count": _to_int(reviews_count),
        "latitude": _to_float(latitude),
        "longitude": _to_float(longitude),
        "place_id": (place_id or "").strip(),
        "category": (category or "").strip(),
        "last_review_date": (last_review_date or "").strip(),
        "source": source,
    }


def dedup_key(record: dict) -> str:
    """Cross-tool dedup key: domain, else normalized name+city, else place_id.

    place_id is last on purpose - each tool mints its own ids, so keying on it
    would stop the same business merging across tools.
    """
    if record.get("domain"):
        return record["domain"]
    name = re.sub(r"[^a-z0-9]+", "", (record.get("name") or "").lower())
    city = re.sub(r"[^a-z0-9]+", "", (record.get("city") or "").lower())
    if name:
        return f"{name}|{city}"
    return record.get("place_id", "")


def write_json(records: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def write_csv(records: list[dict], path: str) -> None:
    """Same 15 columns as FIELDS, header row included, None -> blank cell."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            writer.writerow({k: ("" if rec.get(k) is None else rec.get(k)) for k in FIELDS})
