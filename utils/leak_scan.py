#!/usr/bin/env python3
"""
Leak scanner for the public gtm-skills repo.

This repo is PUBLIC. Nothing here may contain client/prospect names, staff names,
pricing, margins, retainers, internal file paths, or real call data. This script
is the machine gate that enforces that on every pull request (see
.github/workflows/leak-scan.yml) and can be run locally before you push.

It gates what a change ADDS, not what is already public — so it scans added lines
(against a base ref) by default, not the whole repo's history.

Two detection layers:
  1. Generic structural patterns (committed, safe to be public): money-in-pricing
     context, Fathom share links, internal path/file references, raw emails.
  2. A denylist of literal strings (client names, staff names, specific figures)
     loaded from a file that is NEVER committed. Locally that file is
     .leakscan-denylist.txt (gitignored). In CI it is written from the
     LEAKSCAN_DENYLIST repository secret. The sensitive strings live only there.

Usage:
    python utils/leak_scan.py                  # scan lines added vs origin/main
    python utils/leak_scan.py --staged         # scan staged added lines (pre-commit)
    python utils/leak_scan.py --diff <base>    # scan lines added vs <base> (CI)
    python utils/leak_scan.py --all            # audit every tracked file, wholesale
    python utils/leak_scan.py path/a path/b    # scan specific files, wholesale

Suppress a known-safe line with a trailing comment:  # leakscan:ignore
Exit code 0 = clean, 1 = findings.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files the scanner must never scan (they legitimately contain the patterns/terms).
SKIP = {
    "utils/leak_scan.py",
    ".leakscan-denylist.txt",
    ".leakscan-denylist.example.txt",
}
SKIP_DIRS = (".git/",)
SKIP_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".zip", ".pyc")

# Emails allowed to appear (public contact, common example domains).
EMAIL_ALLOW_DOMAINS = {
    "zevenue.com", "example.com", "example.org", "acme.com",
    "prospect.com", "company.com", "stripe.com", "notion.so",
}

MONEY_RE = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?\s?[kKmM]?\b")
# Money is only a leak when it sits next to pricing/deal language. Bare "per month"
# is intentionally excluded — these are outbound skills full of generic "$50/month
# subscriber" examples, and a gate that cries wolf gets ignored. Real monthly
# retainers are caught by the denylist (specific figures) + CODEOWNERS review.
PRICING_CONTEXT = re.compile(
    r"per\s*lead|/\s*lead|per-lead|retainer|base\s*fee|margin|\bmrr\b|\barr\b|"
    r"committed|cost\s*per|deal\s*size|upfront|\bgmv\b|per\s*request|/\s*request",
    re.IGNORECASE,
)
FATHOM_RE = re.compile(r"fathom\.video/share/", re.IGNORECASE)
INTERNAL_PATH_RE = re.compile(
    r"\b(?:internal/|context/clients/|context/prospects/|context/team/|past-clients/)",
)
INTERNAL_FILE_RE = re.compile(
    r"\b(?:financials|strategy|staff|compensation)\.md\b", re.IGNORECASE
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def load_denylist():
    """Literal strings that must never appear. Loaded from a gitignored file."""
    path = Path(os.environ.get("LEAKSCAN_DENYLIST_FILE", ROOT / ".leakscan-denylist.txt"))
    if not path.exists():
        return []
    terms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    # Word-boundary, case-insensitive — a short name won't match inside a longer word.
    return [re.compile(r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])", re.IGNORECASE)
            for t in terms]


def _git(args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def should_skip(rel):
    return rel in SKIP or rel.startswith(SKIP_DIRS) or rel.endswith(SKIP_SUFFIXES)


def units_wholesale(paths):
    """Yield (path, lineno, line) for every line of each file."""
    for rel in paths:
        if should_skip(rel):
            continue
        p = ROOT / rel
        if not p.exists():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            yield rel, n, line


def units_from_diff(diff_args):
    """Yield (path, lineno, line) for ADDED lines in a `git diff` output."""
    res = _git(["diff", "--unified=0", "--no-color", *diff_args])
    if res.returncode != 0:
        sys.stderr.write(f"note: `git diff {' '.join(diff_args)}` failed; "
                         f"falling back to --all.\n{res.stderr}")
        yield from units_wholesale([l for l in _git(["ls-files"]).stdout.splitlines() if l])
        return
    rel, lineno = None, 0
    for line in res.stdout.splitlines():
        if line.startswith("+++ b/"):
            rel = line[6:]
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            lineno = int(m.group(1)) if m else 0
        elif line.startswith("+") and not line.startswith("+++"):
            if rel and not should_skip(rel):
                yield rel, lineno, line[1:]
            lineno += 1


def select_units():
    args = sys.argv[1:]
    if "--all" in args:
        return units_wholesale([l for l in _git(["ls-files"]).stdout.splitlines() if l])
    if "--staged" in args:
        return units_from_diff(["--cached"])
    if "--diff" in args:
        i = args.index("--diff")
        base = args[i + 1] if i + 1 < len(args) else "origin/main"
        return units_from_diff([base])
    paths = [a for a in args if not a.startswith("--")]
    if paths:
        return units_wholesale(paths)
    # Default: lines added vs the upstream main branch.
    for base in ("origin/main", "main"):
        if _git(["rev-parse", "--verify", "--quiet", base]).returncode == 0:
            return units_from_diff([base])
    sys.stderr.write("note: no origin/main or main ref found; auditing all tracked files.\n")
    return units_wholesale([l for l in _git(["ls-files"]).stdout.splitlines() if l])


def find_in_line(line, denylist):
    kinds = []
    if MONEY_RE.search(line) and PRICING_CONTEXT.search(line):
        kinds.append("pricing")
    if FATHOM_RE.search(line):
        kinds.append("fathom-link")
    if INTERNAL_PATH_RE.search(line):
        kinds.append("internal-path")
    if INTERNAL_FILE_RE.search(line):
        kinds.append("internal-file")
    for m in EMAIL_RE.finditer(line):
        if m.group(1).lower() not in EMAIL_ALLOW_DOMAINS:
            kinds.append("email")
            break
    for rx in denylist:
        if rx.search(line):
            kinds.append("denylist")
            break
    return kinds


def main():
    denylist = load_denylist()
    if not denylist and os.environ.get("CI"):
        sys.stderr.write("WARNING: no denylist loaded (LEAKSCAN_DENYLIST secret unset). "
                         "Structural patterns still active.\n")

    total = 0
    for rel, n, line in select_units():
        if "leakscan:ignore" in line:
            continue
        for kind in find_in_line(line, denylist):
            total += 1
            snippet = (line.strip()[:120] + "…") if len(line.strip()) > 120 else line.strip()
            print(f"  {rel}:{n}  [{kind}]  {snippet}")

    print()
    if total:
        print(f"✗ leak-scan: {total} potential leak(s) found. "
              f"Sanitize, or add '# leakscan:ignore' to a confirmed-safe line.")
        return 1
    print("✓ leak-scan: clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
