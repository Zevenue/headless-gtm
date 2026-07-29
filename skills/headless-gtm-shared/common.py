"""Shared CLI plumbing for the chain skill scripts.

Argument parsing, the >$10 cost gate, .env loading, output-dir resolution,
slugs, and run metadata. Stdlib only - `python-dotenv` and `requests` are both
imported lazily, so the estimate-only path needs no third-party deps at all.
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
                        help="output directory (default: ./runs/ under the CWD)")
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


def _parse_env_file(path: str) -> None:
    """Minimal KEY=VALUE parser. Never overwrites an already-set variable."""
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                if line.startswith("export "):
                    line = line[7:]
                key, _, value = line.partition("=")
                os.environ.setdefault(
                    key.strip(), value.strip().strip("'").strip('"')
                )
    except OSError:
        pass


def load_env(*start_dirs: str) -> None:
    """Load the nearest .env into os.environ, searching CWD-up then script-up.

    Call this once at the top of any script that reads an API key, so that
    `cp .env.example .env` is enough - no `export` required. Exported variables
    always win: a value already in the environment is never overwritten, so a
    secrets manager or a real shell export beats a stale .env on disk.

    Pass __file__ as a start dir to also find a .env sitting beside the skill
    when the script is launched from somewhere else.
    """
    starts = [os.getcwd()]
    for s in start_dirs:
        d = os.path.abspath(s)
        starts.append(d if os.path.isdir(d) else os.path.dirname(d))
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        load_dotenv = None
    seen: set[str] = set()
    for start in starts:
        d = start
        while True:
            path = os.path.join(d, ".env")
            if path not in seen and os.path.isfile(path):
                seen.add(path)
                if load_dotenv:
                    load_dotenv(path, override=False)
                else:
                    _parse_env_file(path)
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent


def get_key_or_die(var_name: str, hint: str = "") -> str:
    """Read an env var or exit with the canonical error the docs reference."""
    value = os.environ.get(var_name, "").strip()
    if not value:
        load_env()
        value = os.environ.get(var_name, "").strip()
    if not value:
        msg = f"ERROR: environment variable {var_name} is not set"
        if hint:
            msg += f"\n{hint}"
        msg += (
            "\nSet it in the environment, or put it in a .env file in this "
            "directory or any parent (see .env.example)."
        )
        sys.exit(msg)
    return value


def runs_base(script_file: str | None = None) -> str:
    """Where run folders go by default: ./runs/ under the current directory.

    Output belongs to the project you are working in, not to the skill. A skill
    installed under ~/.claude/skills or ~/.codex/skills is a read-only package -
    writing client data into it is both a sandbox violation and a filing
    mistake. `script_file` is the fallback for the rare case where the CWD is
    not writable. Creates nothing, so it is safe as a module-level constant.
    """
    cwd = os.getcwd()
    if os.access(cwd, os.W_OK) or not script_file:
        return os.path.join(cwd, "runs")
    return os.path.join(os.path.dirname(os.path.abspath(script_file)), "runs")


def resolve_out_dir(out_arg: str | None, script_file: str | None = None) -> str:
    """--out if given, else `runs_base()`. Creates the directory."""
    out_dir = os.path.abspath(out_arg) if out_arg else runs_base(script_file)
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
