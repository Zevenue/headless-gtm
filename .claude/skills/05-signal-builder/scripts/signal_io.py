#!/usr/bin/env python3
"""signal_io.py — chain I/O for the signal-builder skill (05).

Stdlib only. Three subcommands:

  collect    Merge upstream records + scraped pages + structured signals into
             per-domain evidence bundles under a run folder.
  emit       Validate judged signals for one domain and append the combined
             record to the run's records.jsonl.
  status     Show done/pending counts for a run.
  deviation  Append a contract-deviation note to a run's meta.json (see
             _shared/CONVENTIONS.md — any run that can't follow the documented
             contract records what it did and why).

The judgment itself is NOT here — the model reads each bundle, judges, and
calls `emit` with the resulting signal JSON. This script only moves and
validates data, so an interrupted batch can resume without losing work.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PAGE_CONTENT_CAP = 15000          # chars per page kept in a bundle
MAX_SIGNALS = 5
APPROACHES = {"PQS", "PVP", "Pain-led"}
SOURCE_RE = re.compile(r"^(https?://\S+|[a-z0-9_-]+:[a-z0-9_.-]+:\S+)$", re.I)


# ---------------------------------------------------------------- helpers

def norm_domain(raw: str) -> str:
    d = (raw or "").strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = re.sub(r"^www\.", "", d)
    return d.split("/")[0].rstrip(".")


def read_jsonl(path: Path) -> list:
    rows = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"WARNING: {path}:{i} is not valid JSON, skipped ({e})", file=sys.stderr)
    return rows


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"WARNING: could not read {path} ({e})", file=sys.stderr)
        return None


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def scalars_only(obj: dict) -> dict:
    """Keep only scalar values — defensive trim for unknown vendor schemas."""
    return {k: v for k, v in obj.items()
            if isinstance(v, (str, int, float, bool)) and v not in ("", None)}


# ---------------------------------------------------------------- collect

def merge_record(base: dict, extra: dict) -> dict:
    """Merge extra into base. Existing non-empty values win; filters_matched unions."""
    out = dict(base)
    for k, v in extra.items():
        if k == "filters_matched":
            seen = list(out.get("filters_matched") or [])
            for item in (v or []):
                if item not in seen:
                    seen.append(item)
            out["filters_matched"] = seen
        elif out.get(k) in (None, "", []):
            out[k] = v
    return out


def collect_scrape_pages(scrape_run: Path) -> dict:
    """domain -> list of {type, url, content, status} from a 03 run folder."""
    scans = scrape_run / "scans"
    if not scans.is_dir():
        print(f"WARNING: no scans/ folder in {scrape_run}, skipping page content", file=sys.stderr)
        return {}
    out = {}
    for path in sorted(scans.glob("*.json")):
        scan = load_json(path)
        if not scan:
            continue
        domain = norm_domain(scan.get("domain") or path.stem)
        pages_raw = scan.get("pages", {})
        pages = []
        items = pages_raw.items() if isinstance(pages_raw, dict) else \
            ((p.get("type", f"page{i}"), p) for i, p in enumerate(pages_raw))
        for ptype, page in items:
            if not isinstance(page, dict):
                continue
            pages.append({
                "type": ptype,
                "url": page.get("url", ""),
                "content": page.get("content", "") or "",
                "status": page.get("status", "unknown"),
            })
        out[domain] = pages
    return out


def extract_crustdata(data: dict) -> dict:
    """Compact, defensive extraction from a 04 per-domain JSON. Unknown or
    reshaped sections degrade to omission, never to a crash."""
    block = {}
    try:
        matches = data.get("enrich", {}).get("matches", [])
        cd = matches[0].get("company_data", {}) if matches else {}
    except (AttributeError, IndexError, TypeError):
        cd = {}
    if isinstance(cd, dict):
        basic = cd.get("basic_info")
        if isinstance(basic, dict):
            block["company"] = scalars_only(basic)
        funding = cd.get("funding")
        if isinstance(funding, dict):
            rounds = funding.get("funding_rounds")
            if isinstance(rounds, list) and rounds:
                block["funding_rounds"] = [scalars_only(r) for r in rounds[:5]
                                           if isinstance(r, dict)]
        headcount = cd.get("headcount")
        if isinstance(headcount, dict):
            block["headcount"] = scalars_only(headcount)
    hires = data.get("recent_hires")
    if isinstance(hires, list) and hires:
        block["recent_hires"] = [scalars_only(h) for h in hires[:25]
                                 if isinstance(h, dict)]
        if len(hires) > 25:
            block["recent_hires_truncated"] = f"{len(hires)} total, first 25 shown"
    return block


def collect_crustdata(run_dir: Path) -> dict:
    """domain -> compact structured-signal block from a 04 outputs folder."""
    out = {}
    skip = {"tracker.json", "meta.json"}
    for path in sorted(run_dir.glob("*.json")):
        if path.name in skip:
            continue
        data = load_json(path)
        if not isinstance(data, dict) or "domain" not in data:
            continue
        block = extract_crustdata(data)
        if block:
            out[norm_domain(data["domain"])] = block
    return out


def write_bundle(path: Path, domain: str, record: dict, pages: list, structured: dict) -> bool:
    """Write one evidence bundle. Returns True if the bundle has real evidence."""
    lines = [f"# {domain} — evidence bundle", ""]
    lines += ["## Upstream record", "```json", json.dumps(record, indent=2), "```", ""]

    has_evidence = False
    if structured:
        has_evidence = True
        lines += ["## Structured signals (crustdata)", "```json",
                  json.dumps(structured, indent=2), "```", ""]

    gaps = []
    for page in pages:
        content = page["content"].strip()
        if page["status"] not in ("success", "partial", "unknown") or len(content) < 100:
            gaps.append(f"{page['type']} ({page['url'] or 'no url'}): {page['status']}")
            continue
        has_evidence = True
        capped = content[:PAGE_CONTENT_CAP]
        note = "" if len(content) <= PAGE_CONTENT_CAP else \
            f"\n\n[truncated at {PAGE_CONTENT_CAP} chars of {len(content)}]"
        lines += [f"## Page: {page['type']} — {page['url']}", "", capped + note, ""]

    lines += ["## Coverage notes"]
    if gaps:
        lines += [f"- missing/thin page: {g}" for g in gaps]
    if not structured:
        lines += ["- no structured signals for this domain"]
    if not gaps and structured:
        lines += ["- full coverage"]
    path.write_text("\n".join(lines))
    return has_evidence


def cmd_collect(args):
    out_dir = Path(args.out)
    inputs_dir = out_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)

    records: dict[str, dict] = {}
    for rec_path in args.records or []:
        path = Path(rec_path)
        if not path.is_file():
            sys.exit(f"ERROR: records file not found: {path}")
        for row in read_jsonl(path):
            domain = norm_domain(row.get("domain", ""))
            if not domain:
                continue
            records[domain] = merge_record(records.get(domain, {}), row)

    pages_by_domain = collect_scrape_pages(Path(args.scrape_run)) if args.scrape_run else {}
    structured_by_domain = collect_crustdata(Path(args.crustdata_run)) if args.crustdata_run else {}

    all_domains = set(records) | set(pages_by_domain) | set(structured_by_domain)
    if args.domains:
        wanted = {norm_domain(d) for d in args.domains.split(",")}
        all_domains &= wanted
    if not all_domains:
        sys.exit("ERROR: no domains found in the given inputs")

    tracker_path = out_dir / "tracker.json"
    tracker = load_json(tracker_path) if tracker_path.exists() else None
    tracker = tracker or {"run_id": out_dir.name, "created": now_iso(), "domains": {}}

    records_in = []
    thin = 0
    for domain in sorted(all_domains):
        record = records.get(domain) or {"company": domain, "domain": domain,
                                         "person": None, "filters_matched": []}
        record.setdefault("domain", domain)
        records_in.append(record)
        has_evidence = write_bundle(inputs_dir / f"{domain}.md", domain, record,
                                    pages_by_domain.get(domain, []),
                                    structured_by_domain.get(domain, {}))
        existing = tracker["domains"].get(domain, {})
        if existing.get("status") != "done":       # re-collect never resets done work
            tracker["domains"][domain] = {"status": "pending", "thin": not has_evidence}
        if not has_evidence:
            thin += 1

    (out_dir / "records_in.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records_in) + "\n")
    tracker_path.write_text(json.dumps(tracker, indent=2))
    meta = {
        "run_id": out_dir.name, "created": tracker["created"], "updated": now_iso(),
        "sources": {"records": args.records or [], "scrape_run": args.scrape_run,
                    "crustdata_run": args.crustdata_run},
        "domains": len(all_domains), "thin_bundles": thin,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    done = sum(1 for d in tracker["domains"].values() if d.get("status") == "done")
    print(f"Collected {len(all_domains)} domains -> {inputs_dir}")
    print(f"  pending: {len(all_domains) - done} | already done: {done} | thin bundles: {thin}")
    if thin:
        print("  thin = no page content and no structured signals; run 03-firecrawl-research"
              " first (or fetch pages manually for small batches)")


# ------------------------------------------------------------------- emit

def validate_signals(payload) -> tuple[list, dict, list]:
    """Returns (signals, fallback, errors). Contract in SKILL.md 'Output 2'."""
    errors = []
    if isinstance(payload, list):
        signals, fallback = payload, None
    elif isinstance(payload, dict):
        signals = payload.get("signals", [])
        fallback = payload.get("fallback_approach")
    else:
        return [], {}, ["payload must be a JSON object with 'signals' or a JSON array"]

    if not isinstance(signals, list):
        return [], {}, ["'signals' must be an array"]
    if len(signals) > MAX_SIGNALS:
        errors.append(f"{len(signals)} signals given; max is {MAX_SIGNALS} — keep the top {MAX_SIGNALS}")

    for i, sig in enumerate(signals):
        tag = f"signals[{i}]"
        if not isinstance(sig, dict):
            errors.append(f"{tag}: must be an object")
            continue
        for field in ("signal_type", "signal_sentence", "source_url"):
            if not isinstance(sig.get(field), str) or not sig.get(field).strip():
                errors.append(f"{tag}.{field}: required non-empty string")
        src = sig.get("source_url", "")
        if isinstance(src, str) and src.strip() and not SOURCE_RE.match(src.strip()):
            errors.append(f"{tag}.source_url: must be an http(s) URL or vendor:section:domain ref, got '{src}'")
        score = sig.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 10:
            errors.append(f"{tag}.score: integer 1-10 required, got {score!r}")
        if sig.get("approach") not in APPROACHES:
            errors.append(f"{tag}.approach: must be one of {sorted(APPROACHES)}, got {sig.get('approach')!r}")

    if not isinstance(fallback, dict):
        errors.append("fallback_approach: required object {approach, angle}")
        fallback = {}
    else:
        if fallback.get("approach") not in APPROACHES:
            errors.append(f"fallback_approach.approach: must be one of {sorted(APPROACHES)}")
        if not isinstance(fallback.get("angle"), str) or not fallback.get("angle").strip():
            errors.append("fallback_approach.angle: required non-empty string")

    signals = sorted(signals, key=lambda s: s.get("score", 0) if isinstance(s, dict) else 0,
                     reverse=True)
    return signals, fallback, errors


def cmd_emit(args):
    run_dir = Path(args.run)
    tracker_path = run_dir / "tracker.json"
    if not tracker_path.exists():
        sys.exit(f"ERROR: no tracker.json in {run_dir} — run collect first")
    tracker = load_json(tracker_path)
    domain = norm_domain(args.domain)
    if domain not in tracker.get("domains", {}):
        sys.exit(f"ERROR: {domain} is not in this run (see tracker.json)")

    raw = sys.stdin.read() if args.signals_json == "-" else Path(args.signals_json).read_text()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: signals JSON does not parse: {e}")

    signals, fallback, errors = validate_signals(payload)
    if errors:
        print("VALIDATION FAILED — nothing written:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(2)

    upstream = {}
    records_in = run_dir / "records_in.jsonl"
    if records_in.exists():
        for row in read_jsonl(records_in):
            if norm_domain(row.get("domain", "")) == domain:
                upstream = row
                break
    record = dict(upstream) or {"company": domain, "domain": domain,
                                "person": None, "filters_matched": []}
    record["signals"] = signals
    record["fallback_approach"] = fallback

    out_path = run_dir / "records.jsonl"
    rows = [r for r in (read_jsonl(out_path) if out_path.exists() else [])
            if norm_domain(r.get("domain", "")) != domain]
    rows.append(record)
    out_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

    tracker["domains"][domain]["status"] = "done"
    tracker["domains"][domain]["signals"] = len(signals)
    tracker["domains"][domain]["top_score"] = signals[0]["score"] if signals else None
    tracker_path.write_text(json.dumps(tracker, indent=2))
    print(f"{domain}: {len(signals)} signal(s) emitted"
          f"{' (top score ' + str(signals[0]['score']) + ')' if signals else ''}"
          f" -> {out_path}")


# -------------------------------------------------------------- deviation

def cmd_deviation(args):
    """Append {skill, what, why, at} to meta.json deviations[]. Works on any
    chain run folder (not just 05's) — the run-time complement to the
    build-time contract eval."""
    run_dir = Path(args.run)
    if not run_dir.is_dir():
        sys.exit(f"ERROR: run folder not found: {run_dir}")
    meta_path = run_dir / "meta.json"
    meta = (load_json(meta_path) if meta_path.exists() else None) or {}
    deviations = meta.get("deviations")
    if not isinstance(deviations, list):
        deviations = []
    deviations.append({
        "skill": args.skill,
        "what": args.what,
        "why": args.why,
        "at": now_iso(),
    })
    meta["deviations"] = deviations
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(f"Deviation logged in {meta_path} ({len(deviations)} total)")


# ----------------------------------------------------------------- status

def cmd_status(args):
    run_dir = Path(args.run)
    tracker = load_json(run_dir / "tracker.json")
    if not tracker:
        sys.exit(f"ERROR: no readable tracker.json in {run_dir}")
    domains = tracker.get("domains", {})
    done = [d for d, v in domains.items() if v.get("status") == "done"]
    pending = [d for d, v in domains.items() if v.get("status") != "done"]
    print(f"Run {tracker.get('run_id', run_dir.name)}: {len(done)} done, {len(pending)} pending")
    for d in pending[:20]:
        thin = " [thin]" if domains[d].get("thin") else ""
        print(f"  pending: {d}{thin}")
    if len(pending) > 20:
        print(f"  ... and {len(pending) - 20} more")


# ------------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("collect", help="assemble per-domain evidence bundles")
    p.add_argument("--records", action="append",
                   help="records.jsonl from an upstream skill (repeatable; "
                        "01/02/04 run folders all emit one)")
    p.add_argument("--scrape-run", help="03-firecrawl-research run folder (has scans/)")
    p.add_argument("--crustdata-run", help="04-crustdata-signals run folder (per-domain JSONs)")
    p.add_argument("--domains", help="optional comma-separated allowlist")
    p.add_argument("--out", required=True, help="run folder to create/update")
    p.set_defaults(func=cmd_collect)

    p = sub.add_parser("emit", help="validate + append judged signals for one domain")
    p.add_argument("--run", required=True)
    p.add_argument("--domain", required=True)
    p.add_argument("--signals-json", required=True,
                   help="path to the judged-signals JSON, or '-' for stdin")
    p.set_defaults(func=cmd_emit)

    p = sub.add_parser("status", help="show done/pending for a run")
    p.add_argument("--run", required=True)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("deviation",
                       help="append a contract-deviation note to a run's meta.json")
    p.add_argument("--run", required=True, help="any chain run folder")
    p.add_argument("--skill", required=True, help="skill that deviated, e.g. 03-firecrawl-research")
    p.add_argument("--what", required=True, help="what was done instead of the contract")
    p.add_argument("--why", required=True, help="why the contract couldn't be followed")
    p.set_defaults(func=cmd_deviation)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
