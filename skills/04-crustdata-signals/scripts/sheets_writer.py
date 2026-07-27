#!/usr/bin/env python3
"""
sheets_writer.py - Write CrustData signal results to Google Sheets

Reads per-domain JSON files from a run folder and writes 5 tabs:
  1. Signal Summary  - 1 row per domain, signal analysis columns
  2. Recent Hires    - 1 row per person (from person search)
  3. Funding         - 1 row per funding round
  4. Company Growth  - 1 row per domain with headcount metrics
  5. Department Growth - 1 row per domain-department combo

Usage:
  python3 sheets_writer.py --run-dir outputs/run-20260702-143000 --spreadsheet-id <SHEET_ID>
  python3 sheets_writer.py --run-dir outputs/run-20260702-143000 --create-new --title "CrustData Signals Jul 2026"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import gspread
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    print("ERROR: Missing dependencies. Run: pip install gspread google-auth")
    sys.exit(1)

TOKEN_PATH = os.path.expanduser("~/.google/token.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

BATCH_SIZE = 20  # rows per API call

# Departments to track (from CrustData's by_role fields)
DEPARTMENTS = [
    "engineering", "sales", "operations", "marketing", "human_resources",
    "finance", "product", "business_development", "information_technology",
    "support", "legal", "administrative", "consulting", "data_science",
    "arts_and_design",
]


def get_gspread_client() -> gspread.Client:
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            Path(TOKEN_PATH).write_text(creds.to_json())
        else:
            print("ERROR: Token expired. Re-authenticate:")
            print(f"  rm {TOKEN_PATH}")
            print("  mcp-google-sheets --auth")
            sys.exit(1)
    return gspread.authorize(creds)


def load_domain_jsons(run_dir: Path) -> list[dict]:
    results = []
    for f in sorted(run_dir.glob("*.json")):
        if f.name == "tracker.json":
            continue
        try:
            data = json.loads(f.read_text())
            results.append(data)
        except Exception as e:
            print(f"  WARNING: Could not read {f.name}: {e}")
    return results


# ---------------------------------------------------------------------------
# Data extraction helpers
# ---------------------------------------------------------------------------

def safe_get(d: dict, *keys, default=""):
    """Safely traverse nested dicts."""
    current = d
    for k in keys:
        if isinstance(current, dict):
            current = current.get(k)
        else:
            return default
        if current is None:
            return default
    return current


def compute_growth_from_timeseries(timeseries: list, months_back: int) -> tuple:
    """Compute growth from timeseries data. Returns (pct, absolute, old_count, new_count)."""
    if not timeseries or len(timeseries) < 2:
        return ("", "", "", "")
    latest = timeseries[-1]
    latest_count = latest.get("employee_count", 0)
    # Find entry closest to N months ago
    weeks_back = int(months_back * 4.33)
    idx = max(0, len(timeseries) - weeks_back)
    old = timeseries[idx]
    old_count = old.get("employee_count", 0)
    if old_count == 0:
        return ("", "", old_count, latest_count)
    pct = round(((latest_count - old_count) / old_count) * 100, 1)
    absolute = latest_count - old_count
    return (pct, absolute, old_count, latest_count)


def get_company_data(result: dict) -> dict | None:
    """Extract company_data from enrich result."""
    enrich = result.get("enrich", {})
    matches = enrich.get("matches", [])
    if not matches:
        return None
    return matches[0].get("company_data", {})


def format_investors(funding: dict) -> str:
    """Get top investors as comma-separated string."""
    investors = funding.get("investors", [])
    if investors:
        return ", ".join(investors[:5])
    return ""


def format_date(date_str: str) -> str:
    if not date_str:
        return ""
    return str(date_str)[:10]


# ---------------------------------------------------------------------------
# Signal analysis
# ---------------------------------------------------------------------------

def analyze_funding_signal(funding: dict) -> str:
    if not funding:
        return ""
    parts = []
    last_type = funding.get("last_round_type", "")
    last_amount = funding.get("last_round_amount_usd")
    last_date = funding.get("last_fundraise_date", "")
    total = funding.get("total_investment_usd")

    if last_type and last_date:
        try:
            d = datetime.strptime(str(last_date)[:10], "%Y-%m-%d")
            days_ago = (datetime.now() - d).days
            amount_str = f"${last_amount/1e6:.1f}M" if last_amount else ""
            round_str = last_type.replace("_", " ").title()
            if days_ago <= 90:
                parts.append(f"{round_str} {amount_str} raised {days_ago}d ago - FRESH CAPITAL")
            elif days_ago <= 180:
                parts.append(f"{round_str} {amount_str} raised {days_ago//30}mo ago")
            elif days_ago <= 365:
                parts.append(f"{round_str} {amount_str} raised {days_ago//30}mo ago")
        except (ValueError, TypeError):
            pass

    milestones = funding.get("milestones", [])
    if milestones:
        parts.append(f"{len(milestones)} rounds total")

    if total:
        parts.append(f"${total/1e6:.1f}M total raised")

    return " | ".join(parts) if parts else ""


def analyze_growth_signal(headcount: dict) -> str:
    if not headcount:
        return ""
    parts = []
    total = headcount.get("total", 0)
    ts = headcount.get("timeseries", [])

    if ts and len(ts) >= 52:
        pct_12m, abs_12m, old, new = compute_growth_from_timeseries(ts, 12)
        if pct_12m != "":
            if pct_12m > 20:
                parts.append(f"Growing {pct_12m}% YoY (+{abs_12m} employees) - STRONG GROWTH")
            elif pct_12m > 0:
                parts.append(f"Growing {pct_12m}% YoY (+{abs_12m} employees)")
            elif pct_12m < -10:
                parts.append(f"Declining {pct_12m}% YoY ({abs_12m} employees)")
    elif ts and len(ts) >= 26:
        pct_6m, abs_6m, old, new = compute_growth_from_timeseries(ts, 6)
        if pct_6m != "":
            parts.append(f"{pct_6m}% over 6 months ({'+' if abs_6m > 0 else ''}{abs_6m})")

    if total:
        parts.append(f"{total} employees now")

    return " | ".join(parts) if parts else ""


def analyze_dept_signal(headcount: dict) -> str:
    if not headcount:
        return ""
    by_role = headcount.get("by_role_absolute", {})
    by_role_pct = headcount.get("by_role_percent", {})
    if not by_role:
        return ""

    # Key departments to highlight (case-insensitive match against actual keys)
    target_depts = ["engineering", "sales", "marketing", "product management", "operations"]
    parts = []
    for target in target_depts:
        for key in by_role:
            if key.lower() == target or key.lower().replace(" ", "_") == target:
                count = by_role[key]
                pct = by_role_pct.get(key, 0)
                if count and pct and isinstance(pct, (int, float)) and pct > 10:
                    parts.append(f"{key} {pct:.0f}%")
                break
    return " | ".join(parts) if parts else ""


def analyze_hiring_signal(hires: list, hiring: dict) -> str:
    if not hires and not hiring:
        return ""
    parts = []

    # C-suite / senior hires
    senior_titles = []
    for h in hires:
        title = ""
        exp = h.get("experience", {}).get("employment_details", {})
        current = exp.get("current", [])
        if current and isinstance(current, list) and len(current) > 0:
            title = current[0].get("title", "")
            seniority = current[0].get("seniority_level", "")
        elif isinstance(current, dict):
            title = current.get("title", "")
            seniority = current.get("seniority_level", "")
        else:
            continue

        if seniority and seniority.upper() in ("VP", "CXO", "DIRECTOR", "PARTNER", "OWNER"):
            senior_titles.append(title)

    if senior_titles:
        parts.append(f"Senior hires: {', '.join(senior_titles[:3])}")

    if hires:
        parts.append(f"{len(hires)} new hires found")

    openings = hiring.get("openings_count", 0) if hiring else 0
    if openings:
        parts.append(f"{openings} open roles")

    return " | ".join(parts) if parts else ""


# ---------------------------------------------------------------------------
# Build sheet data
# ---------------------------------------------------------------------------

def build_signal_summary(results: list[dict]) -> tuple[list, list]:
    header = [
        "Domain", "Company", "Founded", "Type", "Industries", "HQ", "Country",
        "Headcount", "6m Growth %", "6m Growth Abs", "YoY Growth %", "YoY Growth Abs",
        "Total Funding (USD)", "Last Round", "Last Amount (USD)", "Last Date", "Top Investors",
        "Open Roles", "Recent Hires",
        "Funding Signal", "Growth Signal", "Dept Signal", "Hiring Signal", "Signal Summary",
    ]
    rows = []
    for r in results:
        cd = get_company_data(r)
        if not cd:
            rows.append([r.get("domain", ""), "NO MATCH"] + [""] * (len(header) - 2))
            continue

        bi = cd.get("basic_info", {})
        hc = cd.get("headcount", {})
        fu = cd.get("funding", {})
        hi = cd.get("hiring", {})
        hires = r.get("recent_hires", [])
        ts = hc.get("timeseries", [])

        # Compute fresh growth from timeseries
        pct_6m, abs_6m, _, _ = compute_growth_from_timeseries(ts, 6) if ts else ("", "", "", "")
        pct_12m, abs_12m, _, _ = compute_growth_from_timeseries(ts, 12) if ts else ("", "", "", "")

        # Signal analysis
        funding_sig = analyze_funding_signal(fu)
        growth_sig = analyze_growth_signal(hc)
        dept_sig = analyze_dept_signal(hc)
        hiring_sig = analyze_hiring_signal(hires, hi)

        # Combined summary
        signals = [s for s in [funding_sig, growth_sig, dept_sig, hiring_sig] if s]
        summary = " || ".join(signals) if signals else "No signals detected"

        # basic_info.industries is often null — fall back to taxonomy fields
        industries = bi.get("industries") or []
        if not industries:
            tax = cd.get("taxonomy", {})
            industries = tax.get("categories") or tax.get("professional_network_industries") or []
        industries_str = ", ".join(industries) if isinstance(industries, list) else str(industries or "")

        rows.append([
            r.get("domain", ""),
            bi.get("name", ""),
            bi.get("year_founded", ""),
            bi.get("company_type", ""),
            industries_str,
            safe_get(cd, "locations", "headquarters", default=""),
            safe_get(cd, "locations", "country", default=""),
            hc.get("total", ""),
            pct_6m, abs_6m, pct_12m, abs_12m,
            fu.get("total_investment_usd", ""),
            fu.get("last_round_type", ""),
            fu.get("last_round_amount_usd", ""),
            format_date(fu.get("last_fundraise_date", "")),
            format_investors(fu),
            hi.get("openings_count", "") if hi else "",
            len(hires),
            funding_sig, growth_sig, dept_sig, hiring_sig, summary,
        ])

    return header, rows


def build_recent_hires(results: list[dict]) -> tuple[list, list]:
    header = ["Domain", "Company", "Person Name", "Title", "Start Date", "Days Since Joining",
              "Seniority", "Function", "Location"]
    rows = []
    for r in results:
        domain = r.get("domain", "")
        cd = get_company_data(r)
        company = safe_get(cd, "basic_info", "name", default=domain) if cd else domain

        for h in r.get("recent_hires", []):
            bp = h.get("basic_profile", {})
            exp = h.get("experience", {}).get("employment_details", {})
            current = exp.get("current", [])

            # Handle current as list or dict
            if isinstance(current, list) and current:
                cur = current[0]
            elif isinstance(current, dict):
                cur = current
            else:
                cur = {}

            name = bp.get("name", "")
            title = cur.get("title", "")
            start_date = cur.get("start_date", "")
            seniority = cur.get("seniority_level", "")
            function = cur.get("function_category", "")
            location = ""
            loc = bp.get("location")
            if isinstance(loc, dict):
                parts = [loc.get("city", ""), loc.get("state", ""), loc.get("country", "")]
                location = ", ".join(p for p in parts if p)
            elif isinstance(loc, str):
                location = loc

            # Calculate days since joining
            days_since = ""
            if start_date:
                try:
                    sd = datetime.strptime(str(start_date)[:10], "%Y-%m-%d")
                    days_since = (datetime.now() - sd).days
                except (ValueError, TypeError):
                    pass

            rows.append([domain, company, name, title, format_date(start_date),
                         days_since, seniority, function, location])

    return header, rows


def build_funding(results: list[dict]) -> tuple[list, list]:
    header = ["Domain", "Company", "Round Date", "Round Type", "Amount (USD)",
              "Lead Investors", "All Investors"]
    rows = []
    for r in results:
        domain = r.get("domain", "")
        cd = get_company_data(r)
        if not cd:
            continue
        company = safe_get(cd, "basic_info", "name", default=domain)
        milestones = safe_get(cd, "funding", "milestones", default=[])
        if not isinstance(milestones, list):
            continue
        for m in milestones:
            date = m.get("date") or m.get("funding_date") or m.get("announced_date", "")
            round_type = m.get("round_type") or m.get("funding_type", "")
            amount = m.get("amount_usd") or m.get("money_raised", "")
            lead = m.get("lead_investors", [])
            lead_str = ", ".join(lead) if isinstance(lead, list) else str(lead or "")
            investors = m.get("investors", [])
            inv_str = ", ".join(investors) if isinstance(investors, list) else str(investors or "")
            rows.append([domain, company, format_date(str(date)), round_type, amount, lead_str, inv_str])

    return header, rows


def build_company_growth(results: list[dict]) -> tuple[list, list]:
    header = [
        "Domain", "Company", "Current Headcount",
        "MoM %", "MoM Abs", "QoQ %", "QoQ Abs",
        "6m %", "6m Abs", "YoY %", "YoY Abs", "2Y %", "2Y Abs",
        "HC 6mo Ago", "HC 12mo Ago", "HC 24mo Ago",
        "Largest Country",
    ]
    rows = []
    for r in results:
        domain = r.get("domain", "")
        cd = get_company_data(r)
        if not cd:
            rows.append([domain, "NO MATCH"] + [""] * (len(header) - 2))
            continue
        company = safe_get(cd, "basic_info", "name", default=domain)
        hc = cd.get("headcount", {})
        ts = hc.get("timeseries", [])

        # Compute fresh growth from timeseries
        pct_1m, abs_1m, _, _ = compute_growth_from_timeseries(ts, 1) if ts else ("", "", "", "")
        pct_3m, abs_3m, _, _ = compute_growth_from_timeseries(ts, 3) if ts else ("", "", "", "")
        pct_6m, abs_6m, hc_6m, _ = compute_growth_from_timeseries(ts, 6) if ts else ("", "", "", "")
        pct_12m, abs_12m, hc_12m, _ = compute_growth_from_timeseries(ts, 12) if ts else ("", "", "", "")
        pct_24m, abs_24m, hc_24m, _ = compute_growth_from_timeseries(ts, 24) if ts else ("", "", "", "")

        rows.append([
            domain, company, hc.get("total", ""),
            pct_1m, abs_1m, pct_3m, abs_3m,
            pct_6m, abs_6m, pct_12m, abs_12m, pct_24m, abs_24m,
            hc_6m, hc_12m, hc_24m,
            hc.get("largest_headcount_country", ""),
        ])

    return header, rows


def _find_key_ci(d: dict, target: str):
    """Case-insensitive + underscore-tolerant dict key lookup."""
    norm = target.lower().replace("_", " ")
    for k in d:
        if k.lower().replace("_", " ") == norm:
            return k
    return None


def build_department_growth(results: list[dict]) -> tuple[list, list]:
    header = ["Domain", "Company", "Department", "Current Headcount",
              "6m Ago", "YoY Ago", "6m Growth %", "YoY Growth %"]
    rows = []
    for r in results:
        domain = r.get("domain", "")
        cd = get_company_data(r)
        if not cd:
            continue
        company = safe_get(cd, "basic_info", "name", default=domain)
        hc = cd.get("headcount", {})
        by_role = hc.get("by_role_absolute", {})

        # Also check by_function_timeseries for richer data
        func_ts = hc.get("by_function_timeseries", {})
        current_func = func_ts.get("CURRENT_FUNCTION", {}) if isinstance(func_ts, dict) else {}

        # Iterate over all departments actually present in the data
        all_depts = set()
        for k in by_role:
            all_depts.add(k)
        for k in current_func:
            all_depts.add(k)

        for dept_name in sorted(all_depts):
            current_count = by_role.get(dept_name, 0)
            if not current_count:
                dept_ts = current_func.get(dept_name, [])
                if dept_ts and isinstance(dept_ts, list) and len(dept_ts) > 0:
                    current_count = dept_ts[-1].get("headcount", 0) if isinstance(dept_ts[-1], dict) else 0
            if not current_count:
                continue

            # Growth from timeseries
            dept_ts = current_func.get(dept_name, [])
            hc_6m_ago = ""
            hc_12m_ago = ""
            growth_6m_pct = ""
            growth_12m_pct = ""

            # Timeseries is monthly — index -7 = 6mo ago, -13 = 12mo ago
            if isinstance(dept_ts, list) and len(dept_ts) >= 7:
                entry = dept_ts[-7]
                hc_6m_ago = entry.get("employee_count", entry.get("headcount", "")) if isinstance(entry, dict) else ""
                if hc_6m_ago and hc_6m_ago > 0:
                    growth_6m_pct = round(((current_count - hc_6m_ago) / hc_6m_ago) * 100, 1)
            if isinstance(dept_ts, list) and len(dept_ts) >= 13:
                entry = dept_ts[-13]
                hc_12m_ago = entry.get("employee_count", entry.get("headcount", "")) if isinstance(entry, dict) else ""
                if hc_12m_ago and hc_12m_ago > 0:
                    growth_12m_pct = round(((current_count - hc_12m_ago) / hc_12m_ago) * 100, 1)

            rows.append([
                domain, company, dept_name,
                current_count, hc_6m_ago, hc_12m_ago, growth_6m_pct, growth_12m_pct,
            ])

    return header, rows


# ---------------------------------------------------------------------------
# Sheet writing
# ---------------------------------------------------------------------------

def write_tab(sh: gspread.Spreadsheet, tab_name: str, header: list, rows: list):
    """Write header + rows to a tab. Creates tab if needed."""
    if not rows:
        print(f"  [{tab_name}] No data, skipping")
        return

    try:
        worksheet = sh.add_worksheet(title=tab_name, rows=len(rows) + 1, cols=len(header))
        print(f"  [{tab_name}] Created tab")
    except gspread.exceptions.APIError:
        worksheet = sh.worksheet(tab_name)
        worksheet.clear()
        # Resize to fit new data
        worksheet.resize(rows=len(rows) + 1, cols=max(len(header), worksheet.col_count))
        print(f"  [{tab_name}] Using existing tab (cleared + resized)")

    # Write header
    worksheet.update(range_name="A1", values=[header])

    # Write rows in batches
    total_written = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        start_row = i + 2
        try:
            # Convert all values to strings/numbers safe for Sheets
            safe_batch = []
            for row in batch:
                safe_row = []
                for val in row:
                    if val is None:
                        safe_row.append("")
                    elif isinstance(val, (int, float)):
                        safe_row.append(val)
                    else:
                        safe_row.append(str(val))
                safe_batch.append(safe_row)
            worksheet.update(range_name=f"A{start_row}", values=safe_batch)
            total_written += len(batch)
        except Exception as e:
            print(f"    ERROR batch at row {start_row}: {e}")
            # Retry row by row
            for j, row in enumerate(batch):
                try:
                    safe_row = [str(v) if v is not None else "" for v in row]
                    worksheet.update(range_name=f"A{start_row + j}", values=[safe_row])
                    total_written += 1
                except Exception as e2:
                    print(f"    ERROR row {start_row + j}: {e2}")

    print(f"  [{tab_name}] {total_written}/{len(rows)} rows written")


def main():
    parser = argparse.ArgumentParser(description="Write CrustData signals to Google Sheets")
    parser.add_argument("--run-dir", nargs="+", required=True,
                        help="One or more run folders with JSON files (combines all)")
    parser.add_argument("--spreadsheet-id", help="Write to existing Google Sheet")
    parser.add_argument("--create-new", action="store_true", help="Create a new Google Sheet")
    parser.add_argument("--title", default="CrustData Signals", help="Title for new sheet")
    args = parser.parse_args()

    # Load and dedupe from all run dirs
    results = []
    seen_domains = set()
    for rd in args.run_dir:
        run_dir = Path(rd)
        if not run_dir.exists():
            print(f"WARNING: Run folder not found, skipping: {run_dir}")
            continue
        for r in load_domain_jsons(run_dir):
            domain = r.get("domain", "")
            if domain not in seen_domains:
                results.append(r)
                seen_domains.add(domain)
            else:
                print(f"  Skipping duplicate: {domain}")

    if not results:
        print("ERROR: No JSON files found in any run folder")
        sys.exit(1)

    if not args.spreadsheet_id and not args.create_new:
        print("ERROR: Provide --spreadsheet-id or --create-new")
        sys.exit(1)

    print(f"\nSheets Writer")
    print(f"  Run folders: {len(args.run_dir)}")
    print(f"  Domains: {len(results)} (deduped)")

    # Connect to Google Sheets
    gc = get_gspread_client()

    if args.create_new:
        sh = gc.create(args.title)
        spreadsheet_id = sh.id
        # Share with self for access
        share_email = os.environ.get("SHEETS_SHARE_EMAIL")
        if share_email:
            sh.share(share_email, perm_type="user", role="writer")
        print(f"  Created new sheet: {args.title}")
        print(f"  ID: {spreadsheet_id}")
    else:
        spreadsheet_id = args.spreadsheet_id
        sh = gc.open_by_key(spreadsheet_id)
        print(f"  Writing to: {sh.title}")

    # Build all tabs
    print(f"\nBuilding data...")

    summary_h, summary_r = build_signal_summary(results)
    print(f"  Signal Summary: {len(summary_r)} rows")

    hires_h, hires_r = build_recent_hires(results)
    print(f"  Recent Hires: {len(hires_r)} rows")

    funding_h, funding_r = build_funding(results)
    print(f"  Funding: {len(funding_r)} rows")

    growth_h, growth_r = build_company_growth(results)
    print(f"  Company Growth: {len(growth_r)} rows")

    dept_h, dept_r = build_department_growth(results)
    print(f"  Department Growth: {len(dept_r)} rows")

    # Write all tabs
    print(f"\nWriting to sheet...")

    ts = datetime.now().strftime("%m%d")
    write_tab(sh, f"Signal Summary {ts}", summary_h, summary_r)
    write_tab(sh, f"Recent Hires {ts}", hires_h, hires_r)
    write_tab(sh, f"Funding {ts}", funding_h, funding_r)
    write_tab(sh, f"Company Growth {ts}", growth_h, growth_r)
    write_tab(sh, f"Dept Growth {ts}", dept_h, dept_r)

    print(f"\nDone! Sheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")


if __name__ == "__main__":
    main()
