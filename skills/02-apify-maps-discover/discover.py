#!/usr/bin/env python3
"""apify-maps-discover — Google Maps discovery via the Apify "Compass" actor.

Actor: compass~crawler-google-places
Docs:  https://apify.com/compass/crawler-google-places/api
Auth:  APIFY_API_TOKEN  (Apify Console → Settings → Integrations → API token)

Writes a chain run folder runs/<run-id>/ per ../headless-gtm-shared/CONVENTIONS.md:
records.jsonl (the shared format 03+ consume) + tracker.json + meta.json,
plus prospects.json (full 15-field ProspectRecords, see ../headless-gtm-shared/schema.py)
and a records.csv human export.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import sys

_SHARED = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "headless-gtm-shared")
)
if os.path.isdir(_SHARED):
    sys.path.insert(0, _SHARED)
try:
    import common  # noqa: E402
    from schema import make_record, write_csv, write_json  # noqa: E402
except ImportError:
    sys.exit(
        f"ERROR: cannot find headless-gtm-shared/common.py (looked in {_SHARED}).\n"
        "Copy skills/headless-gtm-shared/ next to this skill - the chain reads its record "
        "contract and shared helpers from there."
    )

common.load_env(__file__)

SOURCE = "apify"
ACTOR_ID = "compass~crawler-google-places"
RUN_SYNC_URL = (
    f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
)

# --- Cost model (EDIT IF VENDOR PRICING CHANGES) ---------------------------
# Step-2 doc quotes "$2.10/1K results + $2/1K for emails".
# Apify's public actor page currently shows ~$1.50/1K. We default to the doc's
# figure (more conservative for budgeting); flip if you confirm otherwise.
COST_PER_1K_PLACES = 2.10
COST_PER_1K_EMAILS = 2.00
# ---------------------------------------------------------------------------


def estimate_cost(max_results: int, include_emails: bool) -> tuple[float, str]:
    places = (max_results / 1000.0) * COST_PER_1K_PLACES
    emails = (max_results / 1000.0) * COST_PER_1K_EMAILS if include_emails else 0.0
    total = places + emails
    breakdown = (
        f"  places: {max_results} x ${COST_PER_1K_PLACES}/1K = ${places:.2f}\n"
        f"  emails: {'on' if include_emails else 'off'} = ${emails:.2f}"
    )
    return total, breakdown


def build_input(args) -> dict:
    payload = {
        "searchStringsArray": [args.search_term],
        "locationQuery": args.geo,
        "maxCrawledPlacesPerSearch": args.max_results,
        "language": "en",
        "skipClosedPlaces": True,
    }
    if args.min_rating:
        # Compass takes an enum word, not a number — allowed: "", two, twoAndHalf,
        # three, threeAndHalf, four, fourAndHalf. Floor to the nearest step so a
        # 4.2 request filters at "four" rather than silently over-filtering.
        stars_enum = {2.0: "two", 2.5: "twoAndHalf", 3.0: "three",
                      3.5: "threeAndHalf", 4.0: "four", 4.5: "fourAndHalf"}
        floored = max((s for s in stars_enum if s <= args.min_rating), default=None)
        if floored:
            payload["placeMinimumStars"] = stars_enum[floored]
    if args.include_emails:
        # Compass exposes contact enrichment via these toggles.
        payload["scrapeContacts"] = True
    if getattr(args, "with_review_dates", False):
        # last_review_date needs the per-place detail page (extra cost/latency).
        payload["scrapePlaceDetailPage"] = True
    return payload


def adapt(item: dict):
    loc = item.get("location") or {}
    return make_record(
        source=SOURCE,
        name=item.get("title", ""),
        website=item.get("website", "") or "",
        phone=item.get("phone", "") or "",
        full_address=item.get("address", "") or "",
        city=item.get("city", "") or "",
        region=item.get("state", "") or "",
        rating=item.get("totalScore"),
        reviews_count=item.get("reviewsCount"),
        latitude=loc.get("lat"),
        longitude=loc.get("lng"),
        place_id=item.get("placeId", "") or "",
        category=(item.get("categoryName")
                  or (item.get("categories") or [""])[0] or ""),
        # Only present when scrapePlaceDetailPage is on (--with-review-dates).
        # Best-effort field name; verify against your actor's output shape.
        last_review_date=_extract_last_review_date(item),
    )


# Firmographic fields this skill contributes to the chain's records.jsonl
# (see ../headless-gtm-shared/CONVENTIONS.md). The chain keys on `domain` and reads `company`.
CHAIN_FIELDS = ("phone", "full_address", "city", "region",
                "rating", "reviews_count", "place_id", "category")


def to_chain_record(rec: dict) -> dict:
    """Map a ProspectRecord to the shared records.jsonl shape downstream reads.

    Renames `name` → `company`, joins on `domain`, and leaves `person` null for
    06-resolution to fill. Firmographic fields pass through untouched (additive).
    """
    out = {"company": rec.get("name", ""), "domain": rec.get("domain", ""),
           "person": None}
    out.update({k: rec.get(k) for k in CHAIN_FIELDS})
    return out


def write_records_jsonl(records: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(to_chain_record(rec), ensure_ascii=False) + "\n")


def write_run_folder(records: list[dict], run_dir: str, slug: str, meta: dict) -> None:
    """Write the chain run folder per ../headless-gtm-shared/CONVENTIONS.md:
    records.jsonl + tracker.json + meta.json, plus the full-fidelity
    prospects.json (all 15 ProspectRecord fields) and records.csv human export.

    The Compass call is a single sync request, so the tracker is a completion
    marker rather than resume state — it exists so every chain run folder has
    the same three files.
    """
    os.makedirs(run_dir, exist_ok=True)
    write_json(records, os.path.join(run_dir, "prospects.json"))
    write_csv(records, os.path.join(run_dir, "records.csv"))
    write_records_jsonl(records, os.path.join(run_dir, "records.jsonl"))
    with open(os.path.join(run_dir, "tracker.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "run_id": slug,
            "status": "done",
            "records": len(records),
        }, fh, indent=2)
        fh.write("\n")
    meta = dict(meta)
    meta.setdefault("run_id", slug)
    meta.setdefault("deviations", [])
    with open(os.path.join(run_dir, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _extract_last_review_date(item: dict) -> str:
    for key in ("lastReviewDate", "lastReview", "mostRecentReviewDate"):
        if item.get(key):
            return str(item[key])
    reviews = item.get("reviews") or []
    if reviews and isinstance(reviews, list):
        first = reviews[0] or {}
        return str(first.get("publishedAtDate") or first.get("publishAt") or "")
    return ""


def main() -> None:
    parser = common.base_arg_parser("Apify Compass")
    parser.add_argument("--with-review-dates", action="store_true",
                        help="scrape per-place detail pages for last_review_date "
                             "(extra cost/latency)")
    args = parser.parse_args()
    est, breakdown = estimate_cost(args.max_results, args.include_emails)
    common.cost_gate(est, estimate_only=args.estimate_only,
                     assume_yes=args.yes, breakdown=breakdown)

    token = common.get_key_or_die(
        "APIFY_API_TOKEN",
        "Get a token at https://console.apify.com → Settings → Integrations",
    )

    import requests  # lazy: estimate-only path needs no network deps

    print(f"Running actor {ACTOR_ID} (sync)…", file=sys.stderr)
    resp = requests.post(
        RUN_SYNC_URL,
        params={"token": token},
        json=build_input(args),
        timeout=300,
    )
    if resp.status_code >= 400:
        sys.exit(f"Apify error {resp.status_code}: {resp.text[:500]}")
    items = resp.json()
    records = [adapt(it) for it in items]

    out_dir = common.resolve_out_dir(args.out, __file__)
    slug = common.slugify("02-apify", args.search_term, args.geo)
    run_dir = os.path.join(out_dir, slug)
    write_run_folder(records, run_dir, slug, {
        "source": SOURCE,
        "actor": ACTOR_ID,
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "query": {"search_term": args.search_term, "geo": args.geo,
                  "max_results": args.max_results, "min_rating": args.min_rating,
                  "include_emails": args.include_emails},
        "returned": len(records),
        "estimated_cost_usd": round(est, 2),
        "cost_model": {"per_1k_places": COST_PER_1K_PLACES,
                       "per_1k_emails": COST_PER_1K_EMAILS},
    })
    print(f"Wrote {len(records)} records → {run_dir}/ "
          f"(records.jsonl + tracker.json + meta.json, +prospects.json, +records.csv)")


if __name__ == "__main__":
    main()
