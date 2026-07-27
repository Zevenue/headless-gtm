#!/usr/bin/env python3
"""
theirstack_jobs.py - Open-req hiring signals from the TheirStack Jobs API.

Two modes:
  check     Given domains (or an upstream records.jsonl), pull open postings
            per domain. One API call per domain, capped by --per-domain.
  discover  No domain list: search all companies by title/tech/geo filters
            and group results by company. The hiring-defined discovery entry.

Every run gets a free count first (blur_company_data=true costs 0 credits and
returns exact totals), then gates on estimated credits before spending.
TheirStack re-charges for jobs it already returned, so per-domain results are
cached as JSON and reused across runs when the query matches.

Usage:
  # Free count only - no credits spent
  python3 theirstack_jobs.py count --domains stripe.com,notion.so --title "SDR,BDR" --days 30
  python3 theirstack_jobs.py count --title "RevOps,Revenue Operations" --country US --days 14

  # Check a domain list (per-domain pulls, cached, resumable)
  python3 theirstack_jobs.py check --domains stripe.com,notion.so --title "SDR,BDR" --days 30
  python3 theirstack_jobs.py check --records ../01-prospeo-discover/runs/x/records.jsonl --days 30

  # Discover companies currently hiring for a role
  python3 theirstack_jobs.py discover --title "Sales Development" --country US \
      --min-employees 50 --max-employees 500 --days 14 --max-jobs 200

  # Resume an interrupted run
  python3 theirstack_jobs.py check --resume --run-dir runs/2026-07-24-sdr-check

  # Credit balance
  python3 theirstack_jobs.py credits

Environment:
  THEIRSTACK_API_KEY - required. https://app.theirstack.com/settings/api
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

BASE_URL = "https://api.theirstack.com"
CREDIT_GATE = 500          # confirm before any pull estimated above this many credits
PER_DOMAIN_DEFAULT = 10    # max jobs fetched (= credits spent) per domain in check mode
PAGE_SIZE_DEFAULT = 25     # jobs per page in discover mode; each returned job = 1 credit
SNIPPET_LEN = 400
REQUEST_DELAY = 0.4        # polite spacing between calls; TheirStack publishes no RPM

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Auth + HTTP
# ---------------------------------------------------------------------------

def _load_dotenv_fallback() -> None:
    """Minimal .env loader so the script has no hard dependency on python-dotenv."""
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
        return
    except ImportError:
        pass
    for candidate in (".env", os.path.join(os.getcwd(), ".env")):
        if os.path.isfile(candidate):
            with open(candidate, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip("'\""))
            return


def get_api_key() -> str:
    key = os.environ.get("THEIRSTACK_API_KEY", "").strip()
    if not key:
        _load_dotenv_fallback()
        key = os.environ.get("THEIRSTACK_API_KEY", "").strip()
    if not key:
        sys.exit(
            "ERROR: THEIRSTACK_API_KEY is not set (env or .env).\n"
            "Get a key at https://app.theirstack.com/settings/api"
        )
    return key


def api_request(method: str, endpoint: str, body: dict | None = None) -> dict:
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body is not None else None
    req = Request(url, data=data, headers=headers, method=method)
    for attempt in range(3):
        try:
            with urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            detail = e.read().decode(errors="replace") if e.fp else ""
            if e.code in (429, 500, 502, 503) and attempt < 2:
                wait = 5 * (attempt + 1)
                print(f"  HTTP {e.code}, retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            sys.exit(f"API error {e.code} on {endpoint}: {detail[:500]}")
        except URLError as e:
            if attempt < 2:
                time.sleep(5)
                continue
            sys.exit(f"Network error on {endpoint}: {e}")
    sys.exit(f"Giving up on {endpoint} after retries")


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

def normalize_domain(value: str) -> str:
    """Bare lowercase host: no scheme, no www., no port, no path (chain key rule)."""
    value = (value or "").strip()
    if not value:
        return ""
    if "://" not in value:
        value = "http://" + value
    host = urlparse(value).netloc or ""
    host = host.rsplit("@", 1)[-1].split(":", 1)[0].lower()
    return host[4:] if host.startswith("www.") else host


def _split(arg: str | None) -> list[str]:
    return [part.strip() for part in (arg or "").split(",") if part.strip()]


def build_filters(args) -> dict:
    """API body filters shared by count/check/discover (company filter added per mode)."""
    body: dict = {"posted_at_max_age_days": args.days}
    if getattr(args, "title", None):
        body["job_title_or"] = _split(args.title)
    if getattr(args, "seniority", None):
        body["job_seniority_or"] = _split(args.seniority)
    if getattr(args, "tech", None):
        body["company_technology_slug_or"] = _split(args.tech)
    if getattr(args, "country", None):
        body["job_country_code_or"] = [c.upper() for c in _split(args.country)]
    if getattr(args, "company_country", None):
        body["company_country_code_or"] = [c.upper() for c in _split(args.company_country)]
    if getattr(args, "min_employees", None) is not None:
        body["min_employee_count"] = args.min_employees
    if getattr(args, "max_employees", None) is not None:
        body["max_employee_count"] = args.max_employees
    if getattr(args, "funding", None):
        body["funding_stage_or"] = _split(args.funding)
    if getattr(args, "remote", None):
        body["remote"] = True
    return body


def query_hash(filters: dict) -> str:
    """Stable hash of the non-company filters - the cache compatibility key."""
    canonical = json.dumps(
        {k: v for k, v in sorted(filters.items()) if not k.startswith("company_domain")},
        sort_keys=True,
    )
    return hashlib.sha1(canonical.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Free count + credit gate
# ---------------------------------------------------------------------------

def sizing_count(filters: dict) -> tuple[int, int, int]:
    """Total matching (jobs, companies, credits_billed) via a limit-1 count.

    Without company-identifier filters the blurred request is genuinely free.
    WITH company_domain_or, TheirStack silently disables blur and bills each
    returned job - limit 1 caps that at 1 credit (0 if nothing matches).
    Verified live 2026-07-24 against the balance ledger and OpenAPI spec.
    """
    body = dict(filters)
    body.update({"blur_company_data": True, "include_total_results": True,
                 "limit": 1, "page": 0})
    result = api_request("POST", "/v1/jobs/search", body)
    meta = result.get("metadata") or {}
    total_jobs = int(meta.get("total_results", result.get("total_results", 0)) or 0)
    total_companies = int(meta.get("total_companies", 0) or 0)
    domain_filtered = bool(filters.get("company_domain_or"))
    billed = min(total_jobs, 1) if domain_filtered else 0
    return total_jobs, total_companies, billed


def credit_gate(estimate: int, gate: int, assume_yes: bool, breakdown: str) -> None:
    print(f"Estimated spend: up to {estimate} credits (1 credit = 1 job returned)",
          file=sys.stderr)
    if breakdown:
        print(breakdown, file=sys.stderr)
    if estimate <= gate or assume_yes:
        return
    if not sys.stdin.isatty():
        sys.exit(
            f"ABORT: estimate {estimate} credits exceeds the {gate}-credit gate and "
            "no TTY is available to confirm. Re-run with --yes to approve, or lower "
            "--max-jobs / --per-domain / tighten --title."
        )
    answer = input(f"Estimate {estimate} credits exceeds the {gate}-credit gate. "
                   "Proceed? [y/N] ").strip().lower()
    if answer not in ("y", "yes"):
        sys.exit("Aborted by user.")


# ---------------------------------------------------------------------------
# Job + record shaping
# ---------------------------------------------------------------------------

def curate_job(job: dict) -> dict:
    """The per-job fields the chain keeps. Full API payloads stay out of records."""
    desc = re.sub(r"\s+", " ", (job.get("description") or "")).strip()
    hiring_team = [
        {"name": person.get("full_name") or person.get("name"),
         "title": person.get("role") or person.get("title"),
         "linkedin_url": person.get("linkedin_url")}
        for person in (job.get("hiring_team") or [])
        if isinstance(person, dict)
    ]
    return {
        "title": job.get("job_title"),
        "url": job.get("url") or job.get("final_url") or job.get("source_url"),
        "date_posted": job.get("date_posted"),
        "location": job.get("short_location") or job.get("location"),
        "remote": job.get("remote"),
        "seniority": job.get("seniority"),
        "employment_status": (job.get("employment_statuses") or [None])[0],
        "salary": job.get("salary_string"),
        "hiring_team": hiring_team,
        "description_snippet": desc[:SNIPPET_LEN],
    }


def company_fields(job: dict) -> dict:
    """Free firmographics that ride along on every job's company_object."""
    co = job.get("company_object") or {}
    return {
        "company": co.get("name") or job.get("company") or "",
        "employee_count": co.get("employee_count"),
        "funding_stage": co.get("funding_stage"),
        "total_funding_usd": co.get("total_funding_usd"),
        "industry": co.get("industry"),
        "company_hq": ", ".join(p for p in (co.get("city"), co.get("country")) if p),
    }


def summarize(domain_entry: dict, days: int, title_filter: str | None) -> list[str]:
    """filters_matched strings - the compact display form downstream tools union."""
    jobs = domain_entry.get("jobs") or []
    if not jobs:
        scope = f" matching '{title_filter}'" if title_filter else ""
        return [f"no open roles{scope} in last {days}d"]
    latest = max((j.get("date_posted") or "" for j in jobs), default="")
    scope = f" '{title_filter}'" if title_filter else ""
    lines = [f"{len(jobs)} open{scope} role(s) in last {days}d (latest {latest})"]
    titles = [j.get("title") for j in jobs if j.get("title")][:3]
    if titles:
        lines.append("hiring: " + "; ".join(titles))
    return lines


def to_chain_record(domain: str, entry: dict, upstream: dict | None,
                    days: int, title_filter: str | None) -> dict:
    """Merge hiring fields into the upstream record. Upstream fields win -
    the chain contract is additive, a downstream skill never overwrites."""
    record = dict(upstream or {})
    record.setdefault("company", entry.get("company") or domain)
    record["domain"] = domain  # always the normalized chain key
    record.setdefault("person", None)
    additions = {
        "open_roles_count": len(entry.get("jobs") or []),
        "roles_window_days": days,
        "roles_title_filter": title_filter or "",
        "jobs": entry.get("jobs") or [],
    }
    for key in ("employee_count", "funding_stage", "total_funding_usd",
                "industry", "company_hq"):
        if entry.get(key) not in (None, ""):
            additions[key] = entry[key]
    for key, value in additions.items():
        if record.get(key) in (None, "", []):
            record[key] = value
    merged = list(record.get("filters_matched") or [])
    for line in summarize(entry, days, title_filter):
        if line not in merged:
            merged.append(line)
    record["filters_matched"] = merged
    return record


# ---------------------------------------------------------------------------
# Run folder plumbing
# ---------------------------------------------------------------------------

def slugify(*parts: str) -> str:
    tokens = []
    for part in parts:
        token = re.sub(r"[^a-z0-9]+", "-", str(part).lower()).strip("-")
        if token:
            tokens.append(token)
    return "-".join([dt.date.today().isoformat()] + tokens)


def resolve_run_dir(args, mode: str) -> str:
    if getattr(args, "run_dir", None):
        run_dir = os.path.abspath(args.run_dir)
    else:
        base = os.path.abspath(args.out) if getattr(args, "out", None) \
            else os.path.join(SKILL_DIR, "runs")
        slug = args.run_id or slugify(mode, (args.title or "").split(",")[0] or "jobs")
        run_dir = os.path.join(base, slug)
    os.makedirs(os.path.join(run_dir, "domains"), exist_ok=True)
    return run_dir


def load_json(path: str, default):
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return default


def save_json(path: str, payload) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def find_cached(domain: str, qhash: str, current_run: str) -> dict | None:
    """Look for this domain in any prior run with the same query hash.
    TheirStack re-charges for repeat pulls, so a cache hit is real money saved."""
    runs_root = os.path.dirname(current_run)
    if not os.path.isdir(runs_root):
        return None
    for run_id in sorted(os.listdir(runs_root), reverse=True):
        candidate = os.path.join(runs_root, run_id, "domains", f"{domain}.json")
        if os.path.isfile(candidate):
            payload = load_json(candidate, None)
            if payload and payload.get("query_hash") == qhash:
                return payload
    return None


def get_balance() -> dict | None:
    """Credit balance; endpoint is undocumented but live. None if it ever 404s."""
    try:
        return api_request("GET", "/v0/billing/credit-balance")
    except SystemExit:
        return None


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

CSV_COLUMNS = ["domain", "company", "open_roles_count", "roles_window_days",
               "top_titles", "latest_posted", "employee_count", "funding_stage",
               "industry", "company_hq"]


def write_outputs(run_dir: str, records: list[dict]) -> None:
    with open(os.path.join(run_dir, "records.jsonl"), "w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    with open(os.path.join(run_dir, "records.csv"), "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            jobs = record.get("jobs") or []
            writer.writerow({
                **{k: ("" if record.get(k) is None else record.get(k))
                   for k in CSV_COLUMNS},
                "top_titles": "; ".join(j.get("title") or "" for j in jobs[:3]),
                "latest_posted": max((j.get("date_posted") or "" for j in jobs),
                                     default=""),
            })


def finalize(run_dir: str, mode: str, filters: dict, records: list[dict],
             jobs_fetched: int, cache_hits: int,
             balance_before: dict | None, count_credits: int = 0) -> None:
    write_outputs(run_dir, records)
    balance_after = get_balance()
    hiring = sum(1 for r in records if (r.get("open_roles_count") or 0) > 0)
    spent = jobs_fetched + count_credits
    meta = {
        "mode": mode,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "filters": filters,
        "query_hash": query_hash(filters),
        "domains_out": len(records),
        "domains_hiring": hiring,
        "jobs_fetched_this_run": jobs_fetched,
        "count_credits": count_credits,
        "credits_spent_estimate": spent,
        "cache_hits": cache_hits,
        "balance_before": balance_before,
        "balance_after": balance_after,
    }
    save_json(os.path.join(run_dir, "meta.json"), meta)
    print(f"\n{len(records)} record(s) -> {run_dir}/records.jsonl (+.csv, meta.json)")
    print(f"{hiring} of {len(records)} domain(s) with open roles; "
          f"{jobs_fetched} job(s) fetched + ~{count_credits} sizing "
          f"(~{spent} credits), {cache_hits} cache hit(s). Postings can lag - "
          "the settled balance delta in meta.json is the true spend.")


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def read_upstream(path: str) -> dict[str, dict]:
    upstream: dict[str, dict] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            domain = normalize_domain(row.get("domain") or "")
            if domain:
                row["domain"] = domain  # the chain key is always the normalized form
                upstream[domain] = row
    if not upstream:
        sys.exit(f"ERROR: no rows with a domain in {path}")
    return upstream


def collect_domains(args) -> dict[str, dict]:
    """domain -> upstream record (empty dict when the domain came from --domains)."""
    if args.records:
        return read_upstream(args.records)
    if args.domains:
        return {normalize_domain(d): {} for d in _split(args.domains) if normalize_domain(d)}
    sys.exit("ERROR: provide --domains or --records (or use discover mode)")


def run_check(args) -> None:
    run_dir = resolve_run_dir(args, "check")
    tracker_path = os.path.join(run_dir, "tracker.json")
    tracker = load_json(tracker_path, {"mode": "check", "domains": {}})

    if args.resume:
        filters = load_json(os.path.join(run_dir, "meta.json"), {}).get("filters") \
            or load_json(os.path.join(run_dir, "filters.json"), None)
        if not filters:
            sys.exit("ERROR: --resume needs an existing run dir with filters.json/meta.json")
        upstream = load_json(os.path.join(run_dir, "upstream.json"), {})
    else:
        filters = build_filters(args)
        upstream = collect_domains(args)
        save_json(os.path.join(run_dir, "filters.json"), filters)
        save_json(os.path.join(run_dir, "upstream.json"), upstream)

    qhash = query_hash(filters)
    # On --resume the CLI flags are absent; the saved filters are the truth.
    days = filters.get("posted_at_max_age_days", args.days)
    title_display = args.title or ",".join(filters.get("job_title_or") or []) or None
    domains = list(upstream.keys())
    pending = [d for d in domains
               if tracker["domains"].get(d, {}).get("status") != "done"]

    # Sizing count -> honest upper bound. Domain-filtered, so it bills ~1
    # credit itself (blur silently disables on company identifiers).
    count_filters = dict(filters)
    count_filters["company_domain_or"] = domains
    total_jobs, total_companies, count_billed = sizing_count(count_filters)
    estimate = min(total_jobs, len(pending) * args.per_domain) + count_billed
    breakdown = (f"  {total_jobs} matching job(s) across {total_companies} of "
                 f"{len(domains)} domain(s); cap {args.per_domain}/domain over "
                 f"{len(pending)} unfetched domain(s); sizing count itself "
                 f"billed ~{count_billed} credit(s)")
    if args.count_only:
        print(breakdown.strip())
        print(f"(count-only: ~{count_billed} credit(s) - domain-filtered counts "
              "are not free)")
        return
    credit_gate(estimate, args.credit_gate, args.yes, breakdown)

    balance_before = get_balance()
    jobs_fetched = 0
    cache_hits = 0
    for i, domain in enumerate(pending, 1):
        cached = None if args.no_cache else find_cached(domain, qhash, run_dir)
        if cached:
            payload = cached
            cache_hits += 1
            print(f"[{i}/{len(pending)}] {domain}: cache hit "
                  f"({len(payload.get('jobs') or [])} job(s), 0 credits)")
        else:
            body = dict(filters)
            body.update({"company_domain_or": [domain],
                         "limit": args.per_domain, "page": 0,
                         "order_by": [{"field": "date_posted", "desc": True}]})
            result = api_request("POST", "/v1/jobs/search", body)
            raw_jobs = result.get("data", [])
            jobs_fetched += len(raw_jobs)
            payload = {"domain": domain, "query_hash": qhash,
                       "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
                       "jobs": [curate_job(j) for j in raw_jobs]}
            if raw_jobs:
                payload.update(company_fields(raw_jobs[0]))
            print(f"[{i}/{len(pending)}] {domain}: {len(raw_jobs)} job(s)")
            time.sleep(REQUEST_DELAY)
        save_json(os.path.join(run_dir, "domains", f"{domain}.json"), payload)
        tracker["domains"][domain] = {"status": "done",
                                      "jobs": len(payload.get("jobs") or [])}
        save_json(tracker_path, tracker)

    records = []
    for domain in domains:
        entry = load_json(os.path.join(run_dir, "domains", f"{domain}.json"), {})
        records.append(to_chain_record(domain, entry, upstream.get(domain),
                                       days, title_display))
    finalize(run_dir, "check", filters, records, jobs_fetched, cache_hits,
             balance_before, count_credits=count_billed)


def run_discover(args) -> None:
    filters = build_filters(args)
    if not any(k in filters for k in
               ("job_title_or", "job_seniority_or", "company_technology_slug_or")):
        sys.exit("ERROR: discover mode needs at least --title, --seniority, or --tech "
                 "- an unfiltered pull of every job posted is never worth credits.")

    total_jobs, total_companies, _ = sizing_count(filters)  # no company filter -> free
    estimate = min(total_jobs, args.max_jobs)
    breakdown = (f"  {total_jobs} matching job(s) across {total_companies} compan(ies); "
                 f"fetching up to --max-jobs {args.max_jobs}")
    if args.count_only:
        print(breakdown.strip())
        print("(count-only: 0 credits spent - no company filter, blur holds)")
        return
    credit_gate(estimate, args.credit_gate, args.yes, breakdown)

    run_dir = resolve_run_dir(args, "discover")
    save_json(os.path.join(run_dir, "filters.json"), filters)
    balance_before = get_balance()
    qhash = query_hash(filters)

    by_domain: dict[str, dict] = {}
    jobs_fetched = 0
    page = 0
    while jobs_fetched < min(total_jobs, args.max_jobs):
        body = dict(filters)
        body.update({"limit": min(args.page_size, args.max_jobs - jobs_fetched),
                     "page": page,
                     "order_by": [{"field": "date_posted", "desc": True}]})
        result = api_request("POST", "/v1/jobs/search", body)
        raw_jobs = result.get("data", [])
        if not raw_jobs:
            break
        jobs_fetched += len(raw_jobs)
        for job in raw_jobs:
            domain = normalize_domain(job.get("company_domain") or "")
            if not domain:
                continue
            entry = by_domain.setdefault(
                domain, {"domain": domain, "query_hash": qhash,
                         "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
                         "jobs": [], **company_fields(job)})
            entry["jobs"].append(curate_job(job))
        print(f"page {page}: {len(raw_jobs)} job(s), "
              f"{len(by_domain)} compan(ies) so far")
        page += 1
        time.sleep(REQUEST_DELAY)

    for domain, entry in by_domain.items():
        save_json(os.path.join(run_dir, "domains", f"{domain}.json"), entry)
    save_json(os.path.join(run_dir, "tracker.json"),
              {"mode": "discover", "pages_fetched": page, "jobs_fetched": jobs_fetched})

    records = [to_chain_record(domain, entry, None, args.days, args.title)
               for domain, entry in sorted(by_domain.items())]
    finalize(run_dir, "discover", filters, records, jobs_fetched, 0, balance_before)


def run_count(args) -> None:
    filters = build_filters(args)
    if args.domains or args.records:
        filters["company_domain_or"] = list(collect_domains(args).keys())
    total_jobs, total_companies, billed = sizing_count(filters)
    print(json.dumps({"total_jobs": total_jobs, "total_companies": total_companies,
                      "count_credits_billed": billed, "filters": filters}, indent=2))
    if billed:
        print("(domain-filtered count: blur disables on company identifiers - "
              f"this call billed ~{billed} credit; quiet domains bill 0)",
              file=sys.stderr)
    else:
        print("(free count: 0 credits spent)", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def add_filter_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", help="comma-separated title keywords (job_title_or)")
    parser.add_argument("--seniority", help="comma-separated seniority levels (job_seniority_or)")
    parser.add_argument("--tech", help="comma-separated technology slugs the company uses")
    parser.add_argument("--country", help="ISO2 job country codes, e.g. US,CA")
    parser.add_argument("--company-country", help="ISO2 company HQ country codes")
    parser.add_argument("--min-employees", type=int)
    parser.add_argument("--max-employees", type=int)
    parser.add_argument("--funding", help="funding stages, e.g. seed,series_a")
    parser.add_argument("--remote", action="store_true", default=None)
    parser.add_argument("--days", type=int, default=30,
                        help="max posting age in days (default 30)")


def add_run_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--credit-gate", type=int, default=CREDIT_GATE,
                        help=f"confirm above this many credits (default {CREDIT_GATE})")
    parser.add_argument("--yes", action="store_true",
                        help="skip the credit-gate confirmation")
    parser.add_argument("--count-only", action="store_true",
                        help="print the free count and exit - 0 credits")
    parser.add_argument("--out", help="runs base dir (default <skill>/runs/)")
    parser.add_argument("--run-id", help="run folder slug (default date+mode+title)")
    parser.add_argument("--run-dir", help="exact run folder (for --resume)")


def main() -> None:
    parser = argparse.ArgumentParser(description="TheirStack open-req hiring signals")
    sub = parser.add_subparsers(dest="command")

    p_count = sub.add_parser("count", help="free count of matching jobs/companies")
    p_count.add_argument("--domains")
    p_count.add_argument("--records", help="upstream records.jsonl to read domains from")
    add_filter_flags(p_count)

    p_check = sub.add_parser("check", help="pull open roles for a domain list")
    p_check.add_argument("--domains", help="comma-separated company domains")
    p_check.add_argument("--records", help="upstream records.jsonl (fields carry through)")
    p_check.add_argument("--per-domain", type=int, default=PER_DOMAIN_DEFAULT,
                         help=f"max jobs (credits) per domain (default {PER_DOMAIN_DEFAULT})")
    p_check.add_argument("--no-cache", action="store_true",
                         help="skip prior-run reuse and refetch every domain")
    p_check.add_argument("--resume", action="store_true")
    add_filter_flags(p_check)
    add_run_flags(p_check)

    p_disc = sub.add_parser("discover", help="find companies hiring for a role")
    p_disc.add_argument("--max-jobs", type=int, default=200,
                        help="total jobs (credits) ceiling for the pull (default 200)")
    p_disc.add_argument("--page-size", type=int, default=PAGE_SIZE_DEFAULT)
    add_filter_flags(p_disc)
    add_run_flags(p_disc)

    sub.add_parser("credits", help="API credit balance")

    args = parser.parse_args()
    if args.command == "count":
        run_count(args)
    elif args.command == "check":
        run_check(args)
    elif args.command == "discover":
        run_discover(args)
    elif args.command == "credits":
        balance = get_balance()
        print(json.dumps(balance, indent=2) if balance else
              "Balance endpoint unavailable - check https://app.theirstack.com/settings/usage")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
