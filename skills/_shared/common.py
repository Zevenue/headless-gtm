"""Shared CLI plumbing for the discovery skill scripts.

Argument parsing, the >$10 cost gate, env-key loading, output-dir resolution,
slugs, and run metadata. Stdlib only - scripts import `requests` lazily so the
estimate-only path needs no network deps.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys

# Runs whose estimate exceeds this require explicit confirmation (--yes or y/N).
COST_GATE_USD = 10.0


def base_arg_parser(tool_name: str) -> argparse.ArgumentParser:
    """The flag set every discovery script shares (see the skill's SKILL.md)."""
    parser = argparse.ArgumentParser(
        description=f"{tool_name} discovery - normalized ProspectRecord output"
    )
    parser.add_argument("--search-term", required=True,
                        help="the vertical, e.g. 'yoga studios'")
    parser.add_argument("--geo", required=True,
                        help="the area, e.g. 'California' or 'Toronto, ON'")
    parser.add_argument("--max-results", type=int, default=200,
                        help="max places to crawl (default 200)")
    parser.add_argument("--min-rating", type=float, default=4.0,
                        help="minimum star rating (default 4.0)")
    parser.add_argument("--include-emails", action="store_true",
                        help="request contact enrichment (adds cost)")
    parser.add_argument("--out", default=None,
                        help="output directory (default: <skill>/runs/)")
    parser.add_argument("--estimate-only", action="store_true",
                        help="print the cost estimate and exit - no API call")
    parser.add_argument("--yes", action="store_true",
                        help=f"skip the >${COST_GATE_USD:.0f} confirmation prompt")
    return parser


def cost_gate(estimate_usd: float, estimate_only: bool = False,
              assume_yes: bool = False, breakdown: str = "") -> None:
    """Print the estimate; exit on --estimate-only; confirm if over the gate.

    Never bypass the gate silently - that is the whole point of it.
    """
    print(f"Estimated cost: ${estimate_usd:.2f}", file=sys.stderr)
    if breakdown:
        print(breakdown, file=sys.stderr)
    if estimate_only:
        print("(estimate-only: exiting before any API call)", file=sys.stderr)
        sys.exit(0)
    if estimate_usd <= COST_GATE_USD or assume_yes:
        return
    if not sys.stdin.isatty():
        sys.exit(
            f"ABORT: estimate ${estimate_usd:.2f} exceeds the ${COST_GATE_USD:.0f} gate "
            "and no TTY is available to confirm. Re-run with --yes to approve, "
            "or lower --max-results."
        )
    answer = input(
        f"Estimate ${estimate_usd:.2f} exceeds the ${COST_GATE_USD:.0f} gate. Proceed? [y/N] "
    ).strip().lower()
    if answer not in ("y", "yes"):
        sys.exit("Aborted by user.")


def get_key_or_die(var_name: str, hint: str = "") -> str:
    """Read an env var or exit with the canonical error the docs reference."""
    value = os.environ.get(var_name, "").strip()
    if not value:
        msg = f"ERROR: environment variable {var_name} is not set"
        if hint:
            msg += f"\n{hint}"
        sys.exit(msg)
    return value


def resolve_out_dir(out_arg: str | None, script_file: str) -> str:
    """--out if given, else <skill-dir>/runs/ (created if missing).

    Resolved relative to the script's own directory, never the CWD, so runs
    land inside the skill folder no matter where the command was launched.
    """
    if out_arg:
        out_dir = os.path.abspath(out_arg)
    else:
        out_dir = os.path.join(
            os.path.dirname(os.path.abspath(script_file)), "runs"
        )
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def slugify(*parts: str) -> str:
    """Date-prefixed slug per the runs/ convention: 2026-07-07-apify-salons-toronto."""
    cleaned = []
    for part in parts:
        token = re.sub(r"[^a-z0-9]+", "-", str(part).lower()).strip("-")
        if token:
            cleaned.append(token)
    date = _dt.date.today().isoformat()
    return "-".join([date] + cleaned)


def write_meta(out_dir: str, slug: str, meta: dict) -> str:
    """Write <slug>_meta.json (run metadata: query, counts, spend estimate)."""
    meta = dict(meta)
    meta.setdefault("generated_at", _dt.datetime.now().isoformat(timespec="seconds"))
    path = os.path.join(out_dir, f"{slug}_meta.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path
