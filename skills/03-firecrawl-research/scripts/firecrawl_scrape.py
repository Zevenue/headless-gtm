#!/usr/bin/env python3
"""
firecrawl_scrape.py — Firecrawl Research extraction engine (Layer 03)

Credit-efficient approach:
  1. map  (1 credit) — discover all URLs on the site
  2. Match URLs to target page types using keyword patterns
  3. scrape (1 credit each) — only scrape confirmed URLs

Modes:
  standard  — Tier 1 + Tier 2 pages (5-8 credits)
  deep      — Tier 1 + Tier 2 + Tier 3 pages (5-11 credits)
  minimal   — Homepage + About only (3 credits)
  extract   — Firecrawl /extract with schema (1 credit)

Storage:
  All data is saved to a run folder on disk. Each domain gets its own JSON file.
  A tracker.json file tracks progress so runs can be resumed if interrupted.

Usage:
  # Single domain
  python3 firecrawl_scrape.py --domain acme.com --mode standard

  # Batch from file (one domain per line)
  python3 firecrawl_scrape.py --batch domains.txt --mode standard

  # Batch from JSON list
  python3 firecrawl_scrape.py --batch domains.json --mode minimal

  # Resume interrupted batch
  python3 firecrawl_scrape.py --resume /path/to/run-folder
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from firecrawl import FirecrawlApp
except ImportError:
    # Deferred: only scraping needs the SDK. Record/tracker helpers stay
    # importable (the contract eval exercises them offline).
    FirecrawlApp = None

# ---------------------------------------------------------------------------
# Page type classification patterns
# Covers EN + TR + BG + RO + GR + DE for multilingual sites
# ---------------------------------------------------------------------------

TIER_1_PATTERNS = {
    "homepage": [],
    "about": [
        "about", "company", "who-we-are", "our-story", "team", "overview",
        "hakkimizda", "hakkinda", "hikayemiz", "kurumsal", "biz-kimiz",
        "za-nas", "za-kompaniyata", "ekip",
        "despre", "despre-noi", "companie",
        "sxetika", "etairia", "poioi-eimaste",
        "ueber-uns", "uber-uns", "unternehmen", "wir-ueber-uns",
    ],
    "careers": [
        "careers", "jobs", "work-with-us", "join-us", "hiring", "join",
        "opportunities", "vacancies",
        "kariyer", "is-ilanlari", "pozisyon", "calisan",
        "karieri", "rabota", "svobodni-pozitsii",
        "cariere", "joburi", "locuri-de-munca",
        "karieres", "theseis-ergasias",
        "karriere", "stellenangebote",
    ],
    "blog": [
        "blog", "news", "insights", "resources", "articles", "updates",
        "press", "media",
        "haberler", "blogliste", "bloglar", "makale", "basin",
        "novini", "stati",
        "noutati", "stiri", "articole",
        "nea", "arthra",
        "neuigkeiten", "nachrichten", "aktuelles", "presse",
    ],
}

TIER_2_PATTERNS = {
    "customers": [
        "customers", "case-studies", "success-stories", "testimonials",
        "case-study", "stories", "results",
        "musteriler", "basari-hikayeleri",
        "klienti", "uspeshni-istorii",
        "clienti", "studii-de-caz",
        "pelates", "periptoseis",
        "kunden", "erfolgsgeschichten", "referenzen",
    ],
    "pricing": [
        "pricing", "plans", "price", "packages",
        "fiyat", "fiyatlar", "paketler",
        "tseni", "planove",
        "pret", "tarife", "preturi",
        "times", "paketa",
        "preise", "kosten", "tarife",
    ],
    "integrations": [
        "integrations", "ecosystem", "partners", "apps", "marketplace",
        "entegrasyonlar", "ortaklar", "is-ortaklari",
        "integratsii", "partnyor",
        "integrari", "parteneri",
        "integrationen", "partner",
    ],
    "product": [
        "product", "platform", "features", "solutions", "how-it-works",
        "technology", "tech",
        "urun", "ozellikler", "cozumler", "teknoloji",
        "produkt", "funktionen", "loesungen", "technologie",
    ],
}

TIER_3_PATTERNS = {
    "changelog": [
        "changelog", "release-notes", "whats-new", "releases", "updates-log",
    ],
    "leadership": [
        "leadership", "management", "executives", "founders",
        "yonetim", "kurucular",
        "fuehrungsteam", "geschaeftsfuehrung",
    ],
}

MAX_SCRAPE_PAGES = 12

# Per-page cap on the markdown carried in records.jsonl. Matches 05's bundle cap
# (signal_io.PAGE_CONTENT_CAP) so nothing 05 would read is lost; scans/*.json
# keep the full content.
RECORD_CONTENT_CAP = 15000

DEFAULT_EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "founder": {"type": "string", "description": "Founder/CEO name(s)"},
        "headcount_clues": {"type": "string", "description": "Team size indicators"},
        "tech_mentions": {"type": "array", "items": {"type": "string"}, "description": "Technologies, tools, platforms mentioned"},
        "funding_clues": {"type": "string", "description": "Any funding, investment, or revenue mentions"},
        "product_category": {"type": "string", "description": "What the company builds/sells"},
        "customers_mentioned": {"type": "array", "items": {"type": "string"}, "description": "Customer/client company names visible on the site (logo grids, case studies, testimonials)"},
        "partners": {"type": "array", "items": {"type": "string"}, "description": "Partner company names shown on the site"},
        "investors": {"type": "array", "items": {"type": "string"}, "description": "Investor/funding partner names shown on the site (backed by, funded by sections)"},
        "year_founded": {"type": "string", "description": "Founding year if mentioned"},
        "locations": {"type": "array", "items": {"type": "string"}, "description": "Office locations / HQ"},
    },
}

# Default run folder base — resolve relative to this skill dir (scripts/ -> skill -> runs/)
RUN_FOLDER_BASE = Path(__file__).resolve().parent.parent / "runs"


# ---------------------------------------------------------------------------
# Run folder + tracker
# ---------------------------------------------------------------------------

def create_run_folder(mode: str, domain_count: int) -> Path:
    """Create a timestamped run folder and return its path."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    name = f"{timestamp}_{mode}_{domain_count}domains"
    run_dir = RUN_FOLDER_BASE / name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "scans").mkdir(exist_ok=True)
    return run_dir


def init_tracker(run_dir: Path, domains: list[str], mode: str) -> dict:
    """Create or load tracker.json for the run."""
    tracker_path = run_dir / "tracker.json"
    if tracker_path.exists():
        return json.loads(tracker_path.read_text())

    tracker = {
        "run_id": run_dir.name,
        "mode": mode,
        "created": datetime.now(timezone.utc).isoformat(),
        "total_domains": len(domains),
        "completed": 0,
        "failed": 0,
        "skipped": 0,
        "total_credits": 0,
        "domains": {d: {"status": "pending"} for d in domains},
    }
    tracker_path.write_text(json.dumps(tracker, indent=2))
    return tracker


def update_tracker(run_dir: Path, tracker: dict, domain: str,
                   status: str, credits: int = 0):
    """Update tracker after processing a domain."""
    tracker["domains"][domain]["status"] = status
    tracker["domains"][domain]["credits"] = credits
    tracker["domains"][domain]["completed_at"] = datetime.now(timezone.utc).isoformat()

    if status in ("success", "partial"):
        tracker["completed"] += 1
    elif status == "failed" or status == "blocked":
        tracker["failed"] += 1
    else:
        tracker["skipped"] += 1

    tracker["total_credits"] += credits
    tracker["last_updated"] = datetime.now(timezone.utc).isoformat()

    tracker_path = run_dir / "tracker.json"
    tracker_path.write_text(json.dumps(tracker, indent=2))


def get_pending_domains(tracker: dict) -> list[str]:
    """Return domains that haven't been processed yet."""
    return [d for d, info in tracker["domains"].items()
            if info["status"] == "pending"]


# ---------------------------------------------------------------------------
# URL classification + scoring (unchanged logic)
# ---------------------------------------------------------------------------

def get_page_patterns(mode: str) -> dict[str, list[str]]:
    patterns = dict(TIER_1_PATTERNS)
    if mode in ("standard", "deep"):
        patterns.update(TIER_2_PATTERNS)
    if mode == "deep":
        patterns.update(TIER_3_PATTERNS)
    if mode == "minimal":
        patterns = {"homepage": [], "about": TIER_1_PATTERNS["about"]}
    return patterns


def classify_url(url: str, base: str, page_types: list[str],
                 patterns: dict[str, list[str]]) -> str | None:
    parsed_base = urlparse(base)
    parsed = urlparse(url)
    base_domain = parsed_base.netloc.replace("www.", "")
    url_domain = parsed.netloc.replace("www.", "")
    if not url_domain.endswith(base_domain):
        return None
    if url_domain != base_domain and not url_domain.startswith("www."):
        return None

    path = parsed.path.lower().strip("/")
    segments = [s.split(".")[0] for s in path.split("/") if s]
    clean_path = "/".join(segments)

    for page_type in page_types:
        if page_type == "homepage":
            continue
        kws = patterns.get(page_type, [])
        for kw in kws:
            if (clean_path == kw
                    or clean_path.startswith(kw + "/")
                    or ("/" + kw + "/") in ("/" + clean_path + "/")
                    or any(seg == kw for seg in segments)
                    # Prefix match: "about-roboforce", "careers-at-acme" etc.
                    # Only for single-word keywords to avoid false positives
                    or ("-" not in kw and any(
                        seg.startswith(kw + "-") for seg in segments
                    ))):
                return page_type
    return None


def score_url(url: str) -> tuple:
    path = urlparse(url).path.strip("/")
    segments = path.split("/")
    has_locale = bool(
        re.match(r'^[a-z]{2}(-[a-z]{2,4})?$', segments[0])
    ) if segments and segments[0] else False
    return (1 if has_locale else 0, len(segments), len(path))


def pick_best_urls(all_urls: list[str], base: str, mode: str) -> dict[str, str]:
    patterns = get_page_patterns(mode)
    page_types = list(patterns.keys())
    matches: dict[str, list[str]] = {pt: [] for pt in page_types if pt != "homepage"}

    for url in all_urls:
        pt = classify_url(url, base, page_types, patterns)
        if pt and pt in matches:
            matches[pt].append(url)

    result: dict[str, str] = {}
    if "homepage" in page_types:
        result["homepage"] = base.rstrip("/")

    for pt, urls in matches.items():
        if urls:
            result[pt] = min(urls, key=score_url)
    return result


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------

def _scrape_one(app: FirecrawlApp, url: str, formats: list) -> object:
    """Single scrape call, returns raw response."""
    return app.scrape(url, formats=formats, only_main_content=False, wait_for=1500)


def _extract_content(response) -> tuple[str, int]:
    """Pull markdown + credits_used from a scrape response."""
    content = ""
    credits = 1  # default assumption
    if hasattr(response, "markdown"):
        content = response.markdown or ""
    elif isinstance(response, dict):
        content = response.get("markdown", "")
    # Read actual credits from metadata
    if hasattr(response, "metadata") and hasattr(response.metadata, "credits_used"):
        credits = response.metadata.credits_used or 1
    return content, credits


def scrape_pages(app: FirecrawlApp, url_map: dict[str, str]) -> tuple[list[dict], int]:
    """Scrape each confirmed URL. Returns (results, total_scrape_credits)."""
    results = []
    total_scrape_credits = 0
    for page_type, url in url_map.items():
        try:
            response = _scrape_one(app, url, ["markdown"])
            content, page_credits = _extract_content(response)

            total_scrape_credits += page_credits

            status = "success"
            if len(content.strip()) < 100:
                status = "thin_content"

            page_result = {
                "type": page_type,
                "url": url,
                "content": content,
                "content_length": len(content),
                "status": status,
                "credits": page_credits,
            }

            results.append(page_result)
            credit_tag = f" [{page_credits}cr]" if page_credits > 1 else ""
            print(f"  + {page_type}: {url} ({len(content)} chars) [{status}]{credit_tag}")

        except Exception as e:
            results.append({
                "type": page_type, "url": url, "content": "",
                "content_length": 0, "status": "failed", "error": str(e),
            })
            print(f"  x {page_type} ({url}): {e}", file=sys.stderr)

    return results, total_scrape_credits


def run_extract(app: FirecrawlApp, url: str, schema: dict | None = None) -> dict:
    if schema is None:
        schema = DEFAULT_EXTRACT_SCHEMA
    try:
        result = app.extract(
            [url],
            prompt="Extract GTM-relevant company information from this website. "
                   "Look for logo grids, trusted-by sections, partner sections, "
                   "and funding/investor sections to find company names.",
            schema=schema,
        )
        # Extract data from response object
        if hasattr(result, "data"):
            extracted = result.data
        elif isinstance(result, dict):
            extracted = result
        else:
            extracted = {}
        return {"url": url, "status": "success", "extracted": extracted, "credits_used": 1}
    except Exception as e:
        return {"url": url, "status": "failed", "error": str(e), "credits_used": 1}


def scrape_domain(domain: str, mode: str = "standard",
                  schema: dict | None = None,
                  map_limit: int = 200) -> dict:
    """Scrape a single domain and return a research packet."""
    if FirecrawlApp is None:
        print("ERROR: firecrawl-py not installed. Run: pip install firecrawl-py")
        sys.exit(1)
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("ERROR: FIRECRAWL_API_KEY not found. Add it to your .env file.")
        sys.exit(1)

    app = FirecrawlApp(api_key=api_key)

    if not domain.startswith("http"):
        base = f"https://{domain}"
    else:
        base = domain
    base = base.rstrip("/")

    clean_domain = urlparse(base).netloc.replace("www.", "")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"\nCrawling: {base} (mode: {mode})")

    # Extract-only mode
    if mode == "extract":
        result = run_extract(app, base, schema)
        return {
            "domain": clean_domain, "mode": "extract", "timestamp": timestamp,
            "site_map": {"total_urls_found": 0, "pages_matched": 0,
                         "pages_scraped": 0, "pages_failed": 0},
            "pages": {}, "extract": result.get("extracted", {}),
            "credits_used": 1, "status": result["status"],
        }

    # Step 1: Map (1 credit)
    print(f"  [1/2] Mapping site URLs (1 credit)...")
    try:
        map_response = app.map(base, limit=map_limit)
        raw = (map_response.links if hasattr(map_response, "links")
               else (map_response if isinstance(map_response, list) else []))
        all_urls = [str(u.url) if hasattr(u, "url") else str(u) for u in (raw or [])]
        print(f"         Found {len(all_urls)} URLs")
    except Exception as e:
        print(f"  ERROR: map failed: {e}", file=sys.stderr)
        all_urls = [base]

    # Step 2: Classify
    url_map = pick_best_urls(all_urls, base, mode)
    found_types = list(url_map.keys())
    patterns = get_page_patterns(mode)
    missing = [pt for pt in patterns if pt not in url_map]

    print(f"         Matched: {', '.join(found_types) if found_types else 'none'}")
    if missing:
        print(f"         Not found: {', '.join(missing)}")

    if not url_map:
        return {
            "domain": clean_domain, "mode": mode, "timestamp": timestamp,
            "site_map": {"total_urls_found": len(all_urls), "pages_matched": 0,
                         "pages_scraped": 0, "pages_failed": 0},
            "pages": {}, "credits_used": 1, "status": "no_pages_found",
        }

    # Step 3: Scrape
    scrape_count = min(len(url_map), MAX_SCRAPE_PAGES)
    print(f"  [2/2] Scraping {scrape_count} pages...\n")
    pages, scrape_credits = scrape_pages(app, url_map)

    total_credits = 1 + scrape_credits  # 1 for map + actual scrape credits
    succeeded = sum(1 for p in pages if p["status"] == "success")
    failed = sum(1 for p in pages if p["status"] == "failed")

    pages_dict = {}
    for p in pages:
        page_entry = {
            "url": p["url"], "content": p["content"],
            "content_length": p["content_length"], "status": p["status"],
        }
        pages_dict[p["type"]] = page_entry

    overall_status = "success"
    if failed > 0 and succeeded == 0:
        overall_status = "blocked"
    elif failed > 0:
        overall_status = "partial"

    output = {
        "domain": clean_domain, "mode": mode, "timestamp": timestamp,
        "site_map": {
            "total_urls_found": len(all_urls), "pages_matched": len(url_map),
            "pages_scraped": succeeded, "pages_failed": failed,
        },
        "pages": pages_dict, "credits_used": total_credits, "status": overall_status,
    }

    print(f"\n  Summary: {succeeded} pages scraped | ~{total_credits} credits")
    return output


# ---------------------------------------------------------------------------
# Batch runner with tracker
# ---------------------------------------------------------------------------

def run_batch(domains: list[str], mode: str, run_dir: Path | None = None,
              map_limit: int = 200, delay: float = 2.0,
              upstream: dict | None = None) -> Path:
    """
    Run extraction on a list of domains with progress tracking.
    Returns path to the run folder.
    """
    # Dedup
    domains = list(dict.fromkeys(domains))

    if run_dir is None:
        run_dir = create_run_folder(mode, len(domains))

    # Persist upstream chain records once so resume and the record writer can
    # inherit their fields (records evolve down the chain, never restart).
    upstream_path = run_dir / "upstream.jsonl"
    if upstream and not upstream_path.exists():
        with open(upstream_path, "w", encoding="utf-8") as f:
            for rec in upstream.values():
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    tracker = init_tracker(run_dir, domains, mode)
    pending = get_pending_domains(tracker)

    print(f"\n{'='*60}")
    print(f"Firecrawl Research - Batch Run")
    print(f"  Run folder: {run_dir}")
    print(f"  Mode: {mode}")
    print(f"  Total domains: {len(domains)}")
    print(f"  Pending: {len(pending)}")
    print(f"  Already done: {tracker['completed']}")
    print(f"{'='*60}\n")

    for i, domain in enumerate(pending):
        idx = len(domains) - len(pending) + i + 1
        print(f"\n[{idx}/{len(domains)}] {domain}")

        try:
            result = scrape_domain(domain, mode=mode, map_limit=map_limit)

            # Save domain JSON to scans folder
            safe_name = domain.replace("/", "_").replace(":", "")
            scan_path = run_dir / "scans" / f"{safe_name}.json"
            scan_path.write_text(json.dumps(result, indent=2))

            update_tracker(run_dir, tracker, domain, result["status"], result["credits_used"])
            print(f"  Saved: {scan_path.name} | Status: {result['status']}")

        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            update_tracker(run_dir, tracker, domain, "failed", 0)

        # Rate limit pause between domains
        if i < len(pending) - 1:
            time.sleep(delay)

    # Write records.jsonl + meta.json for downstream skills
    write_records_jsonl(run_dir, tracker)
    write_meta(run_dir, tracker)

    # Final summary
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE")
    print(f"  Completed: {tracker['completed']}/{len(domains)}")
    print(f"  Failed: {tracker['failed']}")
    print(f"  Total credits: {tracker['total_credits']}")
    print(f"  Run folder: {run_dir}")
    print(f"{'='*60}")

    return run_dir


def load_upstream_records(run_dir: Path) -> dict:
    """domain -> upstream chain record, from the upstream.jsonl saved at batch start."""
    upstream_path = run_dir / "upstream.jsonl"
    if not upstream_path.exists():
        return {}
    out = {}
    for line in upstream_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict) and rec.get("domain"):
            out[str(rec["domain"]).lower()] = rec
    return out


def write_records_jsonl(run_dir: Path, tracker: dict):
    """Write shared-format records.jsonl for downstream skills.

    Per _shared/CONVENTIONS.md stage 03 adds: scraped_markdown (by page type,
    capped at RECORD_CONTENT_CAP chars/page — scans/*.json keep the full text),
    pages_scraped, scrape_status. Upstream fields are inherited, never
    overwritten; filters_matched unions upstream labels with has_<page> labels.
    """
    scans_dir = run_dir / "scans"
    jsonl_path = run_dir / "records.jsonl"
    upstream = load_upstream_records(run_dir)
    count = 0

    with open(jsonl_path, "w") as f:
        for domain, info in tracker["domains"].items():
            if info.get("status") not in ("success", "partial"):
                continue

            safe_name = domain.replace("/", "_").replace(":", "")
            scan_path = scans_dir / f"{safe_name}.json"
            scraped_markdown = {}
            pages_found = []
            scrape_status = info.get("status", "")
            if scan_path.exists():
                scan = json.loads(scan_path.read_text())
                scrape_status = scan.get("status", scrape_status)
                for ptype, page in (scan.get("pages") or {}).items():
                    if not isinstance(page, dict):
                        continue
                    pages_found.append(f"has_{ptype}")
                    content = page.get("content") or ""
                    if content.strip():
                        scraped_markdown[ptype] = content[:RECORD_CONTENT_CAP]

            record = dict(upstream.get(domain.lower(), {}))
            record.setdefault("company", domain)
            record["domain"] = record.get("domain") or domain
            record.setdefault("person", None)
            record["scraped_markdown"] = scraped_markdown
            record["pages_scraped"] = len(scraped_markdown)
            record["scrape_status"] = scrape_status
            merged = list(record.get("filters_matched") or [])
            merged += [p for p in pages_found if p not in merged]
            record["filters_matched"] = merged
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    print(f"  records.jsonl: {count} records written to {jsonl_path}")


def write_meta(run_dir: Path, tracker: dict):
    """Write meta.json per _shared/CONVENTIONS.md (run metadata + deviation log)."""
    meta_path = run_dir / "meta.json"
    existing = {}
    if meta_path.exists():
        try:
            existing = json.loads(meta_path.read_text())
        except json.JSONDecodeError:
            existing = {}
    meta = {
        "run_id": tracker.get("run_id", run_dir.name),
        "mode": tracker.get("mode", ""),
        "created": tracker.get("created", ""),
        "updated": datetime.now(timezone.utc).isoformat(),
        "domains": tracker.get("total_domains", 0),
        "completed": tracker.get("completed", 0),
        "failed": tracker.get("failed", 0),
        "credits_used": tracker.get("total_credits", 0),
        "deviations": existing.get("deviations", []),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")


def load_domains_from_file(path: str) -> tuple[list[str], dict]:
    """Load domains from a text file (one per line), JSON array, or a chain
    records.jsonl. Returns (domains, upstream_records_by_domain) — upstream
    records are non-empty only for records.jsonl input."""
    p = Path(path)
    content = p.read_text().strip()

    if content.startswith("["):
        entries = json.loads(content)
        domains, upstream = [], {}
        for e in entries:
            if isinstance(e, dict) and e.get("domain"):
                domains.append(str(e["domain"]))
                upstream[str(e["domain"]).lower()] = e
            elif isinstance(e, str):
                domains.append(e)
        return domains, upstream

    lines = [line.strip() for line in content.splitlines()
             if line.strip() and not line.strip().startswith("#")]
    if lines and lines[0].startswith("{"):
        # records.jsonl from an upstream skill
        domains, upstream = [], {}
        for i, line in enumerate(lines, 1):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"WARNING: {p}:{i} is not valid JSON, skipped ({e})", file=sys.stderr)
                continue
            if isinstance(rec, dict) and rec.get("domain"):
                domains.append(str(rec["domain"]))
                upstream[str(rec["domain"]).lower()] = rec
        return domains, upstream

    return lines, {}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Firecrawl Research - extract LLM-ready content from company websites"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--domain", help="Single domain (e.g. acme.com)")
    group.add_argument("--batch", help="File with domains (one per line or JSON array)")
    group.add_argument("--resume", help="Resume a previous run (path to run folder)")

    parser.add_argument("--mode", default="standard",
                        choices=["standard", "deep", "minimal", "extract"],
                        help="Scan mode (default: standard)")
    parser.add_argument("--map-limit", type=int, default=200,
                        help="Max URLs to discover per domain (default: 200)")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Seconds between domains in batch mode (default: 2)")
    args = parser.parse_args()

    if args.resume:
        # Resume an existing run
        run_dir = Path(args.resume)
        if not (run_dir / "tracker.json").exists():
            print(f"ERROR: No tracker.json found in {run_dir}")
            sys.exit(1)
        tracker = json.loads((run_dir / "tracker.json").read_text())
        domains = list(tracker["domains"].keys())
        mode = tracker["mode"]
        print(f"Resuming run: {run_dir.name} ({mode} mode)")
        run_batch(domains, mode, run_dir=run_dir, map_limit=args.map_limit,
                  delay=args.delay)
        return

    if args.batch:
        # Batch mode — a domains file, JSON array, or an upstream records.jsonl
        domains, upstream = load_domains_from_file(args.batch)
        if not domains:
            print("ERROR: No domains found in file")
            sys.exit(1)
        run_dir = run_batch(domains, args.mode, map_limit=args.map_limit,
                            delay=args.delay, upstream=upstream)
        print(f"\nTo write results to Google Sheet, run:")
        print(f"  python3 scripts/sheets_writer.py \\")
        print(f"    --run-dir {run_dir} \\")
        print(f"    --spreadsheet-id <SHEET_ID>")
        return

    # Single domain — same run-folder contract as a batch of one
    run_dir = run_batch([args.domain], args.mode, map_limit=args.map_limit,
                        delay=args.delay)
    print(f"\nRun folder: {run_dir}")
    print(f"\nTo write to Google Sheet:")
    print(f"  python3 scripts/sheets_writer.py \\")
    print(f"    --run-dir {run_dir} \\")
    print(f"    --spreadsheet-id <SHEET_ID>")


if __name__ == "__main__":
    main()
