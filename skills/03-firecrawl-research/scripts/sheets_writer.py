#!/usr/bin/env python3
"""
sheets_writer.py — Write firecrawl-research results to Google Sheets

Reads JSON scan files from a run folder and writes them to a Google Sheet.
Uses gspread + OAuth2 (same auth as the Google Sheets MCP server).

Usage:
  python3 sheets_writer.py --run-dir <path/to/run-folder> --spreadsheet-id <SHEET_ID>
  python3 sheets_writer.py --run-dir <path/to/run-folder> --spreadsheet-id <SHEET_ID> --tab-name "custom-name"
  python3 sheets_writer.py --run-dir <path/to/run-folder> --spreadsheet-id <SHEET_ID> --full-content
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import gspread
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    print("ERROR: Missing dependencies. Run: pip install gspread google-auth")
    sys.exit(1)

TOKEN_PATH = os.environ.get("GOOGLE_TOKEN_PATH", os.path.expanduser("~/.google/token.json"))
CREDS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH", os.path.expanduser("~/.google/credentials.json"))
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Page type columns in order
PAGE_TYPES_STANDARD = ["homepage", "about", "careers", "blog", "customers", "pricing", "integrations", "product"]
PAGE_TYPES_DEEP = PAGE_TYPES_STANDARD + ["changelog", "leadership"]
EXTRACT_FIELDS = ["founder", "headcount_clues", "tech_mentions", "funding_clues",
                   "product_category", "customers_mentioned", "partners", "investors",
                   "year_founded", "locations"]

# Max chars per cell in Google Sheets (limit is 50K, we use 40K for safety)
MAX_CELL_CHARS = 40000


def get_gspread_client() -> gspread.Client:
    """Authenticate and return a gspread client."""
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            Path(TOKEN_PATH).write_text(creds.to_json())
        else:
            print("ERROR: Token expired and cannot refresh. Re-authenticate:")
            print(f"  rm {TOKEN_PATH}")
            print(f"  CREDENTIALS_PATH={CREDS_PATH} TOKEN_PATH={TOKEN_PATH} mcp-google-sheets --auth")
            sys.exit(1)
    return gspread.authorize(creds)


def clean_content(content: str, max_chars: int = MAX_CELL_CHARS) -> str:
    """Clean and truncate markdown content for sheet cells."""
    if not content:
        return ""
    # Remove image markdown (noise in sheets)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    # Simplify link markdown: [text](url) -> text
    text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)
    # Collapse excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    if len(text) > max_chars:
        text = text[:max_chars] + '\n\n... [truncated]'
    return text


def load_scan_files(run_dir: Path) -> list[dict]:
    """Load all scan JSON files from a run folder."""
    scans_dir = run_dir / "scans"
    if not scans_dir.exists():
        print(f"ERROR: No scans directory in {run_dir}")
        sys.exit(1)

    results = []
    for f in sorted(scans_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            results.append(data)
        except Exception as e:
            print(f"  WARNING: Could not read {f.name}: {e}")
    return results


def build_rows(scans: list[dict], mode: str, full_content: bool = True) -> tuple[list, list]:
    """
    Build header row and data rows from scan results.
    Returns (header, rows).
    """
    is_extract = mode == "extract"
    page_types = PAGE_TYPES_DEEP if mode == "deep" else PAGE_TYPES_STANDARD

    # Header
    header = ["Domain", "Status", "Mode", "Date", "URLs Found", "Pages Scraped",
              "Credits Used"]

    if is_extract:
        header += [f.replace("_", " ").title() for f in EXTRACT_FIELDS]
    else:
        header += [pt.replace("_", " ").title() for pt in page_types]

    # Data rows
    rows = []
    for scan in scans:
        row = [
            scan.get("domain", ""),
            scan.get("status", ""),
            scan.get("mode", ""),
            scan.get("timestamp", "")[:10],
            scan.get("site_map", {}).get("total_urls_found", 0),
            scan.get("site_map", {}).get("pages_scraped", 0),
            scan.get("credits_used", 0),
        ]

        if is_extract:
            extracted = scan.get("extract", {})
            for field in EXTRACT_FIELDS:
                val = extracted.get(field, "")
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val)
                row.append(str(val))
        else:
            pages = scan.get("pages", {})

            for pt in page_types:
                page_data = pages.get(pt, {})
                content = page_data.get("content", "")

                if full_content:
                    row.append(clean_content(content))
                else:
                    # Summary mode: char count + first ~500 chars cleaned
                    if content:
                        summary = clean_content(content, max_chars=500)
                        row.append(f"[{len(content)} chars]\n{summary}")
                    else:
                        row.append("")

        rows.append(row)

    return header, rows


def write_to_sheet(spreadsheet_id: str, tab_name: str, header: list, rows: list):
    """Write header + rows to a Google Sheet tab."""
    gc = get_gspread_client()
    sh = gc.open_by_key(spreadsheet_id)

    # Create new tab
    try:
        worksheet = sh.add_worksheet(title=tab_name, rows=len(rows) + 1, cols=len(header))
        print(f"  Created tab: {tab_name}")
    except gspread.exceptions.APIError:
        # Tab already exists - use it
        worksheet = sh.worksheet(tab_name)
        print(f"  Using existing tab: {tab_name}")

    # Write header
    worksheet.update(range_name="A1", values=[header])
    print(f"  Header written ({len(header)} columns)")

    # Write data rows in batches of 20 to avoid API limits
    batch_size = 20
    total_written = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        start_row = i + 2  # row 1 is header
        range_name = f"A{start_row}"

        try:
            worksheet.update(range_name=range_name, values=batch)
            total_written += len(batch)
            print(f"  Rows {start_row}-{start_row + len(batch) - 1} written ({total_written}/{len(rows)})")
        except Exception as e:
            print(f"  ERROR writing rows {start_row}-{start_row + len(batch) - 1}: {e}")
            # Try one row at a time for this batch
            for j, row in enumerate(batch):
                row_num = start_row + j
                try:
                    worksheet.update(range_name=f"A{row_num}", values=[row])
                    total_written += 1
                except Exception as e2:
                    print(f"    ERROR row {row_num} ({row[0]}): {e2}")

    print(f"\n  Done: {total_written}/{len(rows)} rows written to '{tab_name}'")
    print(f"  Sheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")


def main():
    parser = argparse.ArgumentParser(
        description="Write firecrawl-research results to Google Sheets"
    )
    parser.add_argument("--run-dir", required=True,
                        help="Path to the run folder containing scans/")
    parser.add_argument("--spreadsheet-id", required=True,
                        help="Google Spreadsheet ID")
    parser.add_argument("--tab-name",
                        help="Custom tab name (default: auto-generated)")
    parser.add_argument("--summary", action="store_true",
                        help="Write summary mode instead of full content (default: full content)")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"ERROR: Run folder not found: {run_dir}")
        sys.exit(1)

    # Load tracker for mode info
    tracker_path = run_dir / "tracker.json"
    if tracker_path.exists():
        tracker = json.loads(tracker_path.read_text())
        mode = tracker.get("mode", "standard")
        domain_count = tracker.get("total_domains", 0)
    else:
        mode = "standard"
        domain_count = 0

    # Load scan files
    scans = load_scan_files(run_dir)
    if not scans:
        print("ERROR: No scan files found")
        sys.exit(1)

    if domain_count == 0:
        domain_count = len(scans)

    print(f"\nSheets Writer")
    print(f"  Run folder: {run_dir}")
    print(f"  Mode: {mode}")
    print(f"  Scans found: {len(scans)}")
    full_content = not args.summary
    print(f"  Content mode: {'summary' if args.summary else 'full'}")

    # Build rows
    header, rows = build_rows(scans, mode, full_content=full_content)

    # Tab name
    tab_name = args.tab_name or f"extract-{mode}-{len(scans)}-{datetime.now().strftime('%Y-%m-%d')}"

    # Write
    print(f"\nWriting to sheet...")
    write_to_sheet(args.spreadsheet_id, tab_name, header, rows)


if __name__ == "__main__":
    main()
