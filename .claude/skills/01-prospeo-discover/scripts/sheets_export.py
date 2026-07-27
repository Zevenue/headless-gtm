#!/usr/bin/env python3
"""
sheets_export.py — Fetch Prospeo company search results and write chain records

Fetches all pages from Prospeo /search-company and writes the run folder the
rest of the chain consumes (per _shared/CONVENTIONS.md):

  <skill-dir>/runs/<run-id>/
  ├── records.jsonl   # one company per line — company, domain, industry, size,
  │                   # location, funding, revenue, keywords, filters_matched
  ├── tracker.json    # pages fetched / total, run status
  └── meta.json       # filters, counts, credits used/remaining

Google Sheets export is OPT-IN (--sheets, or implied by --spreadsheet-id /
--tab-name). The chain never depends on the Sheet.

Auth (environment variables, nothing hardcoded):
  PROSPEO_API_KEY         required
  GOOGLE_TOKEN_PATH       optional, default ~/.google/token.json (Sheets only)
  GOOGLE_CREDENTIALS_PATH optional, default ~/.google/credentials.json (Sheets only)

Usage:
  python3 sheets_export.py --filters filters.json --dry-run
  python3 sheets_export.py --filters filters.json
  python3 sheets_export.py --filters filters.json --run-id 2026-07-26-saas-us
  python3 sheets_export.py --filters filters.json --sheets
  python3 sheets_export.py --filters filters.json --spreadsheet-id SHEET_ID --tab-name "my-search"
  python3 sheets_export.py --filters filters.json --max-pages 10

filters.json example:
  {
    "company_location_search": {"include": ["United States"]},
    "company_industry": {"include": ["Software Development"]},
    "company_headcount_range": ["51-100", "101-200"],
    "company_type": {"status": "Private"},
    "company_revenue": {"min": "1M", "max": "50M"}
  }
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

PROSPEO_API_KEY = os.environ.get("PROSPEO_API_KEY", "")
PROSPEO_BASE_URL = "https://api.prospeo.io"
TOKEN_PATH = os.path.expanduser(os.environ.get("GOOGLE_TOKEN_PATH", "~/.google/token.json"))
CREDS_PATH = os.path.expanduser(os.environ.get("GOOGLE_CREDENTIALS_PATH", "~/.google/credentials.json"))
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

SKILL_DIR = Path(__file__).resolve().parent.parent

RESULTS_HEADER = [
    "Company", "Domain", "Industry", "Employees", "Employee Range",
    "HQ City", "HQ State", "Country", "Revenue", "Funding Stage",
    "Total Funding", "Latest Funding Date", "LinkedIn URL", "Keywords", "Founded"
]


def prospeo_request(endpoint: str, method: str = "GET", body: dict = None) -> dict:
    """Make a request to the Prospeo API."""
    try:
        import requests
    except ImportError:
        print("ERROR: Missing requests. Run: pip install requests")
        sys.exit(1)
    url = f"{PROSPEO_BASE_URL}{endpoint}"
    headers = {
        "X-KEY": PROSPEO_API_KEY,
        "Content-Type": "application/json",
    }
    try:
        if method == "POST":
            resp = requests.post(url, headers=headers, json=body, timeout=30)
        else:
            resp = requests.get(url, headers=headers, timeout=30)
        return resp.json()
    except Exception as e:
        print(f"  ERROR: API request failed: {e}")
        return {"error": True, "error_code": str(e)}


def get_account_info() -> dict:
    """Get Prospeo account info."""
    return prospeo_request("/account-information")


def search_companies(filters: dict, page: int = 1) -> dict:
    """Search companies with given filters."""
    return prospeo_request("/search-company", method="POST", body={
        "page": page,
        "filters": filters,
    })


def _nested_or_flat(company: dict, container: str, *keys: str) -> str:
    """Read a field that may be nested under `container` (e.g. location/funding)
    or flat on the company object, depending on the API response shape."""
    sub = company.get(container)
    if isinstance(sub, dict):
        for k in keys:
            v = sub.get(k)
            if v not in (None, ""):
                return v
    for k in keys:
        v = company.get(k)
        if v not in (None, ""):
            return v
    return ""


def norm_domain(raw: str) -> str:
    d = str(raw or "").strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = re.sub(r"^www\.", "", d)
    return d.split("/")[0].rstrip(".")


def build_filter_labels(filters: dict) -> list:
    """Human-readable filter labels for filters_matched."""
    labels = []
    for key, val in filters.items():
        label = key.replace("company_", "").replace("_", " ").title()
        if isinstance(val, dict):
            inc = val.get("include", [])
            if inc:
                labels.append(f"{label}: {', '.join(str(v) for v in inc)}")
            elif val.get("status"):
                labels.append(f"{label}: {val['status']}")
            else:
                labels.append(label)
        elif isinstance(val, list):
            labels.append(f"{label}: {', '.join(str(v) for v in val)}")
        else:
            labels.append(f"{label}: {val}")
    return labels


def to_chain_record(company: dict, filter_labels: list) -> dict:
    """One company -> the shared per-stage record shape (CONVENTIONS.md, stage 01):
    company, domain, industry, size, location, funding, revenue, keywords, description.

    `description` carries Prospeo's company summary so the next chain step
    (01-icp-qualify) can judge business-nature without re-pulling the search."""
    keywords = company.get("keywords") or []
    if not isinstance(keywords, list):
        keywords = []
    location = ", ".join(str(part) for part in (
        _nested_or_flat(company, "location", "city"),
        _nested_or_flat(company, "location", "state"),
        _nested_or_flat(company, "location", "country"),
    ) if part)
    return {
        "company": company.get("name", ""),
        "domain": norm_domain(company.get("domain") or company.get("website")
                              or company.get("primary_domain") or ""),
        "person": None,
        "industry": company.get("industry", ""),
        "size": company.get("employee_range") or company.get("employee_count") or "",
        "location": location,
        "funding": {
            "stage": _nested_or_flat(company, "funding", "last_funding_type"),
            "total": _nested_or_flat(company, "funding", "total_funding"),
            "last_date": _nested_or_flat(company, "funding", "last_funding_date"),
        },
        "revenue": company.get("revenue_range_printed", ""),
        "keywords": keywords[:15],
        "description": (company.get("description_ai")
                        or company.get("description")
                        or company.get("description_seo") or "")[:800],
        "filters_matched": list(filter_labels),
    }


def extract_company_row(company: dict) -> list:
    """Extract a single company into a row matching RESULTS_HEADER.

    Location and funding fields can arrive nested (company["location"]["city"])
    or flat (company["city"]); this handles both so columns don't silently blank.
    """
    keywords = company.get("keywords") or []
    if not isinstance(keywords, list):
        keywords = []

    return [
        company.get("name", ""),
        company.get("domain") or company.get("website") or company.get("primary_domain") or "",
        company.get("industry", ""),
        company.get("employee_count", ""),
        company.get("employee_range", ""),
        _nested_or_flat(company, "location", "city"),
        _nested_or_flat(company, "location", "state"),
        _nested_or_flat(company, "location", "country"),
        company.get("revenue_range_printed", ""),
        _nested_or_flat(company, "funding", "last_funding_type"),
        _nested_or_flat(company, "funding", "total_funding"),
        _nested_or_flat(company, "funding", "last_funding_date"),
        company.get("linkedin_url", ""),
        ", ".join(str(k) for k in keywords[:15]),
        company.get("founded", ""),
    ]


# ---------------------------------------------------------------------------
# Run folder (the chain contract — always written)
# ---------------------------------------------------------------------------

def default_run_id(filters: dict) -> str:
    """Date-prefixed slug from the most distinctive filters."""
    parts = []
    ind = filters.get("company_industry")
    if isinstance(ind, dict) and ind.get("include"):
        parts.append(str(ind["include"][0]))
    loc = filters.get("company_location_search")
    if isinstance(loc, dict) and loc.get("include"):
        parts.append(str(loc["include"][0]))
    slug = "-".join(re.sub(r"[^a-z0-9]+", "-", p.lower()).strip("-") for p in parts if p)
    date = datetime.now().strftime("%Y-%m-%d")
    return f"{date}-{slug}" if slug else f"{date}-prospeo-search"


def write_run_folder(run_dir: Path, companies: list, filters: dict,
                     total_count: int, pages_fetched: int, pages_total: int,
                     credits_used: int, credits_remaining) -> Path:
    """Write records.jsonl + tracker.json + meta.json per _shared/CONVENTIONS.md."""
    run_dir.mkdir(parents=True, exist_ok=True)
    filter_labels = build_filter_labels(filters)

    records_path = run_dir / "records.jsonl"
    with open(records_path, "w", encoding="utf-8") as f:
        for company in companies:
            f.write(json.dumps(to_chain_record(company, filter_labels),
                               ensure_ascii=False) + "\n")

    status = "done" if pages_fetched >= pages_total else "partial"
    (run_dir / "tracker.json").write_text(json.dumps({
        "run_id": run_dir.name,
        "status": status,
        "pages": {"fetched": pages_fetched, "planned": pages_total},
        "records": len(companies),
    }, indent=2) + "\n")

    (run_dir / "meta.json").write_text(json.dumps({
        "run_id": run_dir.name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "prospeo:/search-company",
        "filters": filters,
        "total_count": total_count,
        "pages_fetched": pages_fetched,
        "credits_used": credits_used,
        "credits_remaining": credits_remaining,
        "deviations": [],
    }, indent=2, ensure_ascii=False) + "\n")

    print(f"  Run folder: {run_dir}")
    print(f"  records.jsonl: {len(companies)} records ({status})")
    return records_path


# ---------------------------------------------------------------------------
# Google Sheets (opt-in export — the chain never depends on this)
# ---------------------------------------------------------------------------

def get_gspread_client():
    """Authenticate and return a gspread client. Sheets deps load lazily."""
    try:
        import gspread
        from google.auth.transport.requests import Request as AuthRequest
        from google.oauth2.credentials import Credentials
    except ImportError:
        print("ERROR: Missing Sheets deps. Run: pip install gspread google-auth")
        sys.exit(1)
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(AuthRequest())
            Path(TOKEN_PATH).write_text(creds.to_json())
        else:
            print(f"ERROR: Google token at {TOKEN_PATH} is expired and cannot refresh.")
            print(f"  Delete it and re-run your Google OAuth flow to regenerate the token,")
            print(f"  using the client credentials at {CREDS_PATH}.")
            sys.exit(1)
    return gspread.authorize(creds)


def build_filter_summary(filters: dict) -> list:
    """Build human-readable filter summary for the Search Info tab."""
    rows = [["Field", "Value"]]

    mapping = {
        "company_location_search": "Location",
        "company_industry": "Industries",
        "company_headcount_range": "Headcount Range",
        "company_headcount_custom": "Headcount Custom",
        "company_type": "Company Type",
        "company_keywords": "Keywords",
        "company_revenue": "Revenue",
        "company_funding": "Funding",
        "company_technology": "Technology",
        "company_lookalike": "Lookalike",
        "company_headcount_growth": "Headcount Growth",
        "company_job_posting_hiring_for": "Hiring For",
        "company_job_posting_quantity": "Job Posting Count",
        "company_attributes": "Attributes",
        "company_founded": "Founded",
        "company_news": "News",
        "company_email_provider": "Email Provider",
        "company_products_services": "Products/Services",
        "company_icp": "ICP",
        "company_key_execs": "Key Execs",
        "company_website_traffic": "Website Traffic",
    }

    for key, val in filters.items():
        label = mapping.get(key, key)
        if isinstance(val, (dict, list)):
            rows.append([label, json.dumps(val, ensure_ascii=False)])
        else:
            rows.append([label, str(val)])

    return rows


def write_results(spreadsheet_id: str, tab_name: str, rows: list, gc):
    """Write company rows to the Results tab in batches."""
    import gspread
    sh = gc.open_by_key(spreadsheet_id)

    try:
        worksheet = sh.add_worksheet(title=tab_name, rows=len(rows) + 1, cols=len(RESULTS_HEADER))
        print(f"  Created tab: {tab_name}")
    except gspread.exceptions.APIError:
        worksheet = sh.worksheet(tab_name)
        print(f"  Using existing tab: {tab_name}")

    # Write header
    worksheet.update(range_name="A1", values=[RESULTS_HEADER])

    # Write data in batches of 50 rows
    batch_size = 50
    total_written = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        start_row = i + 2

        try:
            worksheet.update(range_name=f"A{start_row}", values=batch)
            total_written += len(batch)
            print(f"  Rows {start_row}-{start_row + len(batch) - 1} written ({total_written}/{len(rows)})")
        except Exception as e:
            print(f"  ERROR batch at row {start_row}: {e}")
            # Retry one by one
            for j, row in enumerate(batch):
                row_num = start_row + j
                try:
                    worksheet.update(range_name=f"A{row_num}", values=[row])
                    total_written += 1
                except Exception as e2:
                    print(f"    ERROR row {row_num}: {e2}")

        # Google Sheets API allows ~60 writes/min - pace the batches
        if i + batch_size < len(rows):
            time.sleep(1)

    return total_written


def write_search_info(spreadsheet_id: str, filters: dict, total_companies: int,
                      pages_exported: int, credits_used: int, credits_remaining: int,
                      gc):
    """Write the Search Info metadata tab."""
    import gspread
    sh = gc.open_by_key(spreadsheet_id)

    try:
        worksheet = sh.add_worksheet(title="Search Info", rows=30, cols=2)
    except gspread.exceptions.APIError:
        worksheet = sh.worksheet("Search Info")

    info_rows = build_filter_summary(filters)
    info_rows.append(["", ""])
    info_rows.append(["Total Companies Found", str(total_companies)])
    info_rows.append(["Pages Exported", str(pages_exported)])
    info_rows.append(["Credits Used", str(credits_used)])
    info_rows.append(["Export Date", datetime.now().strftime("%Y-%m-%d %H:%M")])
    info_rows.append(["Credits Remaining", str(credits_remaining)])

    worksheet.update(range_name="A1", values=info_rows)
    print(f"  Search Info tab written ({len(info_rows)} rows)")


def export_to_sheets(args, filters: dict, companies: list, total_count: int,
                     pages_fetched: int, credits_used: int, credits_remaining):
    """The opt-in Sheets flow: create/open spreadsheet, write both tabs."""
    print("\nConnecting to Google Sheets...")
    gc = get_gspread_client()

    if args.spreadsheet_id:
        spreadsheet_id = args.spreadsheet_id
        print(f"  Using existing spreadsheet: {spreadsheet_id}")
    else:
        loc = filters.get("company_location_search", {}).get("include", [""])[0] if isinstance(filters.get("company_location_search"), dict) else ""
        ind = filters.get("company_industry", {}).get("include", [""])[0][:20] if isinstance(filters.get("company_industry"), dict) else ""
        hc = ", ".join(filters.get("company_headcount_range", [])) if isinstance(filters.get("company_headcount_range"), list) else ""
        title = f"Prospeo Discovery — {ind} {loc} {hc} — {datetime.now().strftime('%Y-%m-%d')}".strip()
        sh = gc.create(title)
        spreadsheet_id = sh.id
        print(f"  Created spreadsheet: {title}")
        print(f"  ID: {spreadsheet_id}")

    print("\nWriting Search Info tab...")
    write_search_info(spreadsheet_id, filters, total_count, pages_fetched,
                      credits_used, credits_remaining, gc)

    all_rows = [extract_company_row(c) for c in companies]
    tab_name = args.tab_name or "Results"
    print(f"\nWriting {len(all_rows)} companies to '{tab_name}' tab...")
    total_written = write_results(spreadsheet_id, tab_name, all_rows, gc)
    print(f"  Sheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    return total_written


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fetch Prospeo search results into a chain run folder; Sheets export opt-in")
    parser.add_argument("--filters", required=True, help="Path to filters JSON file")
    parser.add_argument("--run-id", help="Run folder name (default: date + industry/location slug)")
    parser.add_argument("--out", help="Base output dir (default: <skill-dir>/runs)")
    parser.add_argument("--max-pages", type=int, default=1000, help="Max pages to fetch (default: 1000)")
    parser.add_argument("--dry-run", action="store_true", help="Preview filters and count without fetching")
    parser.add_argument("--sheets", action="store_true", help="Also export to Google Sheets")
    parser.add_argument("--spreadsheet-id", help="Existing spreadsheet ID (implies --sheets)")
    parser.add_argument("--tab-name", help="Custom Results tab name (implies --sheets)")
    parser.add_argument("--yes", action="store_true", help="Skip the >10-page confirmation prompt")
    args = parser.parse_args()

    if args.spreadsheet_id or args.tab_name:
        args.sheets = True

    if not PROSPEO_API_KEY:
        print("ERROR: Set the PROSPEO_API_KEY environment variable.")
        sys.exit(1)

    # Load filters
    filters_path = Path(args.filters)
    if not filters_path.exists():
        print(f"ERROR: Filters file not found: {filters_path}")
        sys.exit(1)
    filters = json.loads(filters_path.read_text())

    # Account check
    print("\nProspeo Export")
    print("=" * 50)
    acct = get_account_info()
    if acct.get("error"):
        print(f"ERROR: Could not get account info: {acct}")
        sys.exit(1)
    resp = acct["response"]
    credits_start = resp["remaining_credits"]
    print(f"  Plan: {resp['current_plan']} | Credits: {credits_start}")

    # First page to get total count
    print("\nFetching page 1...")
    result = search_companies(filters, page=1)
    if result.get("error"):
        print(f"ERROR: Search failed: {result.get('error_code', result)}")
        if result.get("filter_error"):
            print(f"  Filter error: {result['filter_error']}")
        sys.exit(1)

    pagination = result["pagination"]
    total_count = pagination["total_count"]
    total_pages = pagination["total_page"]
    pages_to_fetch = min(total_pages, args.max_pages)

    print(f"  Found {total_count} companies across {total_pages} pages")
    print(f"  Will fetch {pages_to_fetch} pages ({pages_to_fetch} credits)")

    if args.dry_run:
        print("\n  [DRY RUN] No fetch performed.")
        sys.exit(0)

    # Cost guard
    if pages_to_fetch > 10 and not args.yes:
        if not sys.stdin.isatty():
            sys.exit(f"ABORT: {pages_to_fetch} pages = {pages_to_fetch} credits and no TTY "
                     "to confirm. Re-run with --yes to approve, or lower --max-pages.")
        confirm = input(f"\n  Fetch {pages_to_fetch} pages = {pages_to_fetch} credits. Proceed? (y/n): ")
        if confirm.lower() != "y":
            print("  Cancelled.")
            sys.exit(0)

    # Collect all companies (raw dicts — rows and records both derive from these)
    companies = [c["company"] for c in result["results"]]
    print(f"  Page 1: {len(result['results'])} companies")
    pages_fetched = 1

    for page in range(2, pages_to_fetch + 1):
        time.sleep(0.5)  # Rate limit Prospeo
        print(f"  Fetching page {page}/{pages_to_fetch}...")
        result = search_companies(filters, page=page)
        if result.get("error"):
            print(f"    ERROR on page {page}: {result.get('error_code')}")
            break
        companies.extend(c["company"] for c in result["results"])
        pages_fetched = page
        print(f"  Page {page}: {len(result['results'])} companies (total: {len(companies)})")

    credits_used = pages_fetched
    print(f"\n  Fetched {len(companies)} companies using {credits_used} credits")

    acct_after = get_account_info()
    credits_remaining = acct_after.get("response", {}).get(
        "remaining_credits", credits_start - credits_used)

    # Run folder — the chain contract, written on every run
    print("\nWriting run folder...")
    run_id = args.run_id or default_run_id(filters)
    base = Path(args.out) if args.out else SKILL_DIR / "runs"
    records_path = write_run_folder(
        base / run_id, companies, filters, total_count,
        pages_fetched, pages_to_fetch, credits_used, credits_remaining)

    # Sheets — opt-in human export
    if args.sheets:
        export_to_sheets(args, filters, companies, total_count,
                         pages_fetched, credits_used, credits_remaining)

    # Summary
    print(f"\n{'=' * 50}")
    print("Done.")
    print(f"  Companies: {len(companies)}")
    print(f"  Credits used: {credits_used} | remaining: {credits_remaining}")
    print(f"  Records: {records_path}")


if __name__ == "__main__":
    main()
