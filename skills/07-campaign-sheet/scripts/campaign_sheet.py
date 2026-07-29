#!/usr/bin/env python3
"""
campaign_sheet.py - turn a terminal records.jsonl into an owner-readable
campaign sheet plus a HubSpot-import-shaped CSV.

07-campaign-sheet is the chain's exit door. It reads whatever records.jsonl a
run produced - a qualified list, a signal-ranked set, or a fully resolved one -
and writes two derived, human-facing files. It adds no chain fields and nothing
downstream reads its output, per headless-gtm-shared/CONVENTIONS.md (CSV is a
derived export only).

  <working-dir>/runs/<run-id>/
  |-- campaign-sheet.md    who to contact first and why, ranked by signal score
  |-- campaign-sheet.csv   HubSpot default import headers, one row per record

The CSV degrades with the data: the First Name / Last Name / Email columns
appear only when at least one record carries a resolved contact (06 ran), and
a Listing URL column appears only when at least one record carries one
(directory-sourced runs). The Company / Website / Phone / Lifecycle / Notes
columns are always present.

Stdlib only - no API keys, no network. Runnable on a synthetic fixture with
zero accounts.

Usage:
  python3 campaign_sheet.py --records ./runs/<run-id>/records.jsonl
  python3 campaign_sheet.py --records path/to/records.jsonl --title "HVAC - Ontario"
  python3 campaign_sheet.py --records path/to/records.jsonl --run-id 2026-07-29-07-hvac
"""

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

# --- shared helpers (stdlib-only path resolution, no third-party deps) -------
_SHARED = Path(__file__).resolve().parents[2] / "headless-gtm-shared"
if _SHARED.is_dir():
    sys.path.insert(0, str(_SHARED))
try:
    from common import runs_base, slugify
except ImportError:
    sys.exit(
        f"ERROR: cannot find headless-gtm-shared/common.py (looked in {_SHARED}).\n"
        "Copy skills/headless-gtm-shared/ next to this skill - campaign_sheet.py "
        "resolves its run folder with common.runs_base()."
    )

LIFECYCLE_STAGE = "Lead"   # every exported contact enters HubSpot as a Lead
NOTE_MAX = 200             # cap the Notes cell so the CSV stays readable
DETAIL_CARDS = 15          # rows shown as full cards before the compact table


def read_records(path: Path) -> list:
    if not path.is_file():
        sys.exit(f"ERROR: no records file at {path}")
    records = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"  skip records.jsonl:{i}: does not parse ({e})", file=sys.stderr)
    if not records:
        sys.exit(f"ERROR: {path} has no usable records")
    return records


# --- field readers: tolerate every stage's shape ----------------------------

def company_of(rec: dict) -> str:
    return (rec.get("company") or rec.get("name") or "").strip() or "(unnamed)"


def website_of(rec: dict) -> str:
    site = (rec.get("website") or "").strip()
    if site:
        return site
    domain = (rec.get("domain") or "").strip()
    return f"https://{domain}" if domain else ""


def city_of(rec: dict) -> str:
    for key in ("city", "region"):
        value = (rec.get(key) or "").strip()
        if value:
            return value
    return (rec.get("full_address") or "").strip()


def top_signal(rec: dict):
    """Highest-score signal dict, or None when 05 has not run."""
    signals = rec.get("signals")
    if not isinstance(signals, list):
        return None
    scored = [s for s in signals if isinstance(s, dict)]
    if not scored:
        return None
    return max(scored, key=lambda s: s.get("score") or 0)


def approach_of(rec: dict) -> str:
    sig = top_signal(rec)
    if sig and sig.get("approach"):
        return sig["approach"]
    fallback = rec.get("fallback_approach")
    if isinstance(fallback, dict):
        return fallback.get("approach") or ""
    return ""


def score_of(rec: dict):
    sig = top_signal(rec)
    return (sig.get("score") or 0) if sig else 0


def person_of(rec: dict) -> dict:
    name = (rec.get("person_name") or "").strip()
    first, last = "", ""
    if name:
        parts = name.split()
        first, last = parts[0], " ".join(parts[1:])
    return {
        "name": name,
        "first": first,
        "last": last,
        "title": (rec.get("matched_title") or "").strip(),
        "email": (rec.get("email") or "").strip(),
        "status": (rec.get("verification_status") or "").strip(),
    }


def note_of(rec: dict) -> str:
    """The Notes cell: top signal plus recommended approach, one line."""
    sig = top_signal(rec)
    approach = approach_of(rec)
    bits = []
    if sig:
        stype = sig.get("signal_type") or "signal"
        sentence = (sig.get("signal_sentence") or "").strip()
        bits.append(f"{stype}: {sentence}" if sentence else stype)
    else:
        fallback = rec.get("fallback_approach")
        if isinstance(fallback, dict) and fallback.get("angle"):
            bits.append(f"angle: {fallback['angle']}")
    if approach:
        bits.append(f"approach: {approach}")
    return " | ".join(bits)[:NOTE_MAX]


def has_contact(rec: dict) -> bool:
    person = person_of(rec)
    return bool(person["name"] or person["email"])


# --- CSV: mapping-driven, HubSpot default import headers ---------------------

def listing_of(rec: dict) -> str:
    return (rec.get("listing_url") or "").strip()


# Each column is (header, reader, cond). cond None -> always emitted;
# "contacts" -> only when at least one record carries a resolved person/email
# (06 ran); "listing" -> only when at least one record carries a listing_url
# (directory-sourced runs). Either way a run without the data gets no dead
# columns. Adding a column is one tuple here - the flattening is data, not code.
COLUMN_SPECS = [
    ("First Name",      lambda r: person_of(r)["first"],          "contacts"),
    ("Last Name",       lambda r: person_of(r)["last"],           "contacts"),
    ("Email",           lambda r: person_of(r)["email"],          "contacts"),
    ("Company Name",    company_of,                               None),
    ("Website URL",     website_of,                               None),
    ("Phone Number",    lambda r: (r.get("phone") or "").strip(), None),
    ("Listing URL",     listing_of,                               "listing"),
    ("Lifecycle Stage", lambda r: LIFECYCLE_STAGE,                None),
    ("Notes",           note_of,                                  None),
]


def build_csv(records: list, path: Path, flags: dict) -> int:
    cols = [c for c in COLUMN_SPECS if c[2] is None or flags.get(c[2])]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([header for header, _, _ in cols])
        for rec in records:
            writer.writerow([reader(rec) for _, reader, _ in cols])
    return len(cols)


# --- Markdown: owner-readable, ranked ---------------------------------------

def _card(rank: int, rec: dict) -> str:
    lines = [f"### {rank}. {company_of(rec)}" + (f" - {city_of(rec)}" if city_of(rec) else "")]
    sig = top_signal(rec)
    if sig:
        sentence = (sig.get("signal_sentence") or "").strip()
        source = (sig.get("source_url") or "").strip()
        why = f"{sig.get('signal_type') or 'signal'}"
        if sentence:
            why += f' - "{sentence}"'
        if source:
            why += f" ({source})"
        lines.append(f"- **Why now:** {why}")
    else:
        lines.append("- **Why now:** no ranked signal - carried on ICP fit; rank with 05 before prioritizing")
    approach = approach_of(rec)
    if approach:
        lines.append(f"- **Approach:** {approach}")
    person = person_of(rec)
    if person["name"] or person["email"]:
        who = person["name"] or "(contact)"
        if person["title"]:
            who += f", {person['title']}"
        if person["email"]:
            who += f" - {person['email']}"
        if person["status"]:
            who += f" ({person['status']})"
        lines.append(f"- **Contact:** {who}")
    elif website_of(rec):
        lines.append("- **Contact:** not resolved - run 06-resolution-email-person for send-ready addresses")
    else:
        lines.append("- **Contact:** no website listed - phone / the listing link is the "
                     "channel (06 needs a domain to resolve an email)")
    site, phone = website_of(rec), (rec.get("phone") or "").strip()
    meta = " · ".join(x for x in [site, phone, listing_of(rec)] if x)
    if meta:
        lines.append(f"- **Reach:** {meta}")
    return "\n".join(lines)


def build_markdown(records: list, title: str, records_path: Path, contacts: bool) -> str:
    heading = title.strip() or "Campaign sheet"
    out = [f"# Campaign sheet - {heading}", ""]
    out.append(
        f"{len(records)} targets, ranked by signal. **Nothing here has been sent.** "
        "Approve this sheet on screen before anything leaves it."
    )
    out.append("")
    out.append(
        f"Generated {date.today().isoformat()} from `{records_path}`. "
        "The CSV beside this file imports into HubSpot with every row set to "
        "Lifecycle Stage = Lead; the drafted email sequence is the copy to send once approved."
    )
    out.append("")
    out.append("## Who to contact first")
    out.append("")
    shown = records[:DETAIL_CARDS]
    for i, rec in enumerate(shown, 1):
        out.append(_card(i, rec))
        out.append("")

    rest = records[DETAIL_CARDS:]
    if rest:
        out.append(f"## The rest of the ranked list ({len(rest)} more)")
        out.append("")
        out.append("| # | Company | Where | Top signal | Approach | Contact |")
        out.append("|---|---|---|---|---|---|")
        for i, rec in enumerate(rest, DETAIL_CARDS + 1):
            sig = top_signal(rec)
            signal_cell = (sig.get("signal_type") if sig else "") or "-"
            person = person_of(rec)
            contact_cell = person["email"] or person["name"] or "unresolved"
            out.append(
                f"| {i} | {company_of(rec)} | {city_of(rec) or '-'} | "
                f"{signal_cell} | {approach_of(rec) or '-'} | {contact_cell} |"
            )
        out.append("")

    out.append("## Before you send")
    out.append("")
    out.append(
        "- Nothing in this repo sends. This sheet and the drafted sequence are the deliverable; "
        "importing the CSV and sending is the owner's step, after this approval."
    )
    if not contacts:
        out.append(
            "- No contacts are resolved yet - the CSV carries companies only. "
            "Run 06-resolution-email-person on the approved rows for send-ready addresses, then regenerate."
        )
    out.append(
        "- Import order in HubSpot: map the columns as shown, keep Lifecycle Stage = Lead, "
        "and dedupe on Email (or Company Name when no email is present)."
    )
    out.append("")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(
        description="Build an owner campaign sheet + HubSpot-shaped CSV from records.jsonl"
    )
    parser.add_argument("--records", required=True,
                        help="path to the terminal records.jsonl")
    parser.add_argument("--out", default=None,
                        help="base output dir (default: ./runs/ under the CWD)")
    parser.add_argument("--run-id", default=None,
                        help="run folder name (default: date + 07-campaign-sheet slug)")
    parser.add_argument("--title", default="",
                        help="campaign title for the sheet heading, e.g. 'HVAC - Ontario'")
    args = parser.parse_args()

    records_path = Path(args.records).expanduser().resolve()
    records = read_records(records_path)

    # Rank: highest top-signal score first; unscored rows fall to the bottom
    # but stay in the sheet (stable sort preserves upstream order within ties).
    records.sort(key=score_of, reverse=True)
    contacts = any(has_contact(r) for r in records)
    flags = {"contacts": contacts,
             "listing": any(listing_of(r) for r in records)}

    base = Path(args.out).expanduser() if args.out else Path(runs_base(__file__))
    run_id = args.run_id or slugify("07-campaign-sheet", args.title or records_path.stem)
    run_dir = base / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    csv_path = run_dir / "campaign-sheet.csv"
    md_path = run_dir / "campaign-sheet.md"
    ncols = build_csv(records, csv_path, flags)
    md_path.write_text(build_markdown(records, args.title, records_path, contacts),
                       encoding="utf-8")

    print(f"campaign sheet: {len(records)} rows, {ncols} CSV columns"
          f"{' (with contacts)' if contacts else ' (companies only)'}")
    print(f"  {md_path}")
    print(f"  {csv_path}")


if __name__ == "__main__":
    main()
