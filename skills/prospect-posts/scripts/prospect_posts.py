"""
Prospect Posts Scraper via Apify
Fetches recent LinkedIn posts from one or more profiles and writes structured JSON
for theme/signal research. Read-only and multi-profile: it does not download
images and does not write back to any profile.

Uses the apimaestro/linkedin-profile-posts actor (ID LQQIXN9Othf8f7R5n), which takes
one profile per run. For multiple profiles, we start runs in parallel and merge.

Usage:
    python3 scripts/prospect_posts.py \\
        --profile-url https://www.linkedin.com/in/foo/ \\
        --profile-url https://www.linkedin.com/in/bar/ \\
        --count 20 \\
        --output-path scans/2026-04-16-ai-first-gtm.json

Requires:
    - APIFY_API_TOKEN in the environment or a .env file
    - pip install requests python-dotenv
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# --- shared helpers + .env loading ------------------------------------------
_SHARED = Path(__file__).resolve().parents[2] / "headless-gtm-shared"
if _SHARED.is_dir():
    sys.path.insert(0, str(_SHARED))
try:
    from common import load_env, runs_base
except ImportError:
    sys.exit(
        f"ERROR: cannot find headless-gtm-shared/common.py (looked in {_SHARED}).\n"
        "Copy skills/headless-gtm-shared/ next to this skill - the chain reads its record "
        "contract and shared helpers from there."
    )
load_env(__file__)

ACTOR_ID = "apimaestro~linkedin-profile-posts"
APIFY_BASE = "https://api.apify.com/v2"
POLL_INTERVAL_SECS = 5
RUN_TIMEOUT_SECS = 900  # 15 min per profile

API_TOKEN = os.getenv("APIFY_API_TOKEN") or os.getenv("APIFY_API_KEY")


def username_from_input(raw: str) -> str:
    """Accept either a bare username or a LinkedIn URL; return the username segment."""
    s = (raw or "").strip()
    m = re.search(r"linkedin\.com/in/([^/?#]+)", s, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    return s.strip("/").split("/")[-1]


def start_actor_run(username: str, total_posts: int) -> str:
    url = f"{APIFY_BASE}/acts/{ACTOR_ID}/runs"
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    payload = {"username": username, "total_posts": total_posts}
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]["id"]


def get_run_status(run_id: str) -> dict:
    url = f"{APIFY_BASE}/actor-runs/{run_id}"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()["data"]


def fetch_dataset(dataset_id: str) -> list:
    url = f"{APIFY_BASE}/datasets/{dataset_id}/items"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    resp = requests.get(url, headers=headers, params={"format": "json"}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def flatten_posts(raw_items: list) -> list:
    """Dataset items may be individual posts or wrappers of {data: {posts: [...]}}.

    Normalize to a flat list of post dicts.
    """
    out = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        data = item.get("data")
        if isinstance(data, dict) and isinstance(data.get("posts"), list):
            out.extend(data["posts"])
            continue
        if isinstance(item.get("posts"), list):
            out.extend(item["posts"])
            continue
        out.append(item)
    return out


def parse_post_date(post: dict) -> str:
    posted_at = post.get("posted_at") or post.get("postedAt")
    if isinstance(posted_at, dict):
        date_str = posted_at.get("date", "")
        if date_str:
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d",
            ):
                try:
                    return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    continue
        ts = posted_at.get("timestamp")
        if ts:
            try:
                return datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d")
            except (ValueError, TypeError, OSError):
                pass
    elif isinstance(posted_at, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"):
            try:
                return datetime.strptime(posted_at, fmt).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                continue
    return ""


def extract_text(post: dict) -> str:
    text = post.get("text") or post.get("content") or ""
    if isinstance(text, str):
        text = text.strip()
    else:
        text = ""

    reshared = post.get("reshared_post") or {}
    if isinstance(reshared, dict):
        reshared_text = reshared.get("text") or ""
        if isinstance(reshared_text, str) and reshared_text.strip():
            author = reshared.get("author") or {}
            name = " ".join(
                filter(None, [author.get("first_name"), author.get("last_name")])
            ).strip() or author.get("username", "original author")
            prefix = text + "\n\n" if text else ""
            text = f"{prefix}[Reshared from {name}]\n{reshared_text.strip()}"

    return text


def extract_engagement(post: dict) -> dict:
    stats = post.get("stats") or {}
    if not isinstance(stats, dict):
        return {}
    out = {}
    mapping = {
        "likes": ("total_reactions", "like"),
        "comments": ("comments",),
        "reposts": ("reposts",),
    }
    for key, fields in mapping.items():
        for f in fields:
            val = stats.get(f)
            if isinstance(val, (int, float)):
                out[key] = int(val)
                break
    return out


def extract_author(post: dict) -> tuple[str, str, str]:
    author = post.get("author") or {}
    if not isinstance(author, dict):
        return "", "", ""
    name = " ".join(filter(None, [author.get("first_name"), author.get("last_name")])).strip()
    headline = author.get("headline") or ""
    profile_url = author.get("profile_url") or ""
    return profile_url, name, headline


def shape_post(post: dict) -> dict | None:
    text = extract_text(post)
    if not text:
        return None
    return {
        "date": parse_post_date(post),
        "url": post.get("url") or "",
        "type": post.get("post_type") or post.get("type") or "regular",
        "text": text,
        "engagement": extract_engagement(post),
    }


def wait_for_runs(runs: list[dict]) -> None:
    """Poll all runs until each finishes. Mutates each run dict with `status` and `dataset_id`."""
    start = time.time()
    pending = {r["run_id"]: r for r in runs if r.get("status") not in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT")}
    while pending and (time.time() - start) < RUN_TIMEOUT_SECS:
        time.sleep(POLL_INTERVAL_SECS)
        for run_id in list(pending.keys()):
            data = get_run_status(run_id)
            status = data.get("status")
            r = pending[run_id]
            r["status"] = status
            if status == "SUCCEEDED":
                r["dataset_id"] = data.get("defaultDatasetId")
                del pending[run_id]
            elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                del pending[run_id]
        statuses = [f"{r['username']}={r['status']}" for r in runs]
        print(f"  [{int(time.time()-start)}s] {', '.join(statuses)}")
    for r in runs:
        if r.get("status") not in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            r["status"] = "TIMED-OUT"


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape recent LinkedIn posts from one or more profiles")
    parser.add_argument(
        "--profile-url",
        action="append",
        required=True,
        help="LinkedIn profile URL or username (repeat for multiple profiles)",
    )
    parser.add_argument("--count", type=int, default=20, help="Posts per profile (default 20)")
    parser.add_argument("--output-path", required=True, help="Where to write the JSON result")
    parser.add_argument("--raw-output", help="Optional path to also save raw Apify response")
    args = parser.parse_args()

    if not API_TOKEN:
        print("Error: APIFY_API_TOKEN not found in .env", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    runs = []
    for raw in args.profile_url:
        username = username_from_input(raw)
        run_id = start_actor_run(username, args.count)
        print(f"Started run for {username}: {run_id}")
        runs.append({"input": raw, "username": username, "run_id": run_id, "status": "READY"})

    print("\nWaiting for all runs...")
    wait_for_runs(runs)

    all_raw = []
    profiles = []
    for r in runs:
        entry = {
            "input": r["input"],
            "username": r["username"],
            "run_id": r["run_id"],
            "status": r["status"],
            "profile_url": "",
            "name": "",
            "headline": "",
            "posts": [],
        }
        if r.get("status") != "SUCCEEDED":
            print(f"  {r['username']}: run {r['status']}")
            profiles.append(entry)
            continue

        raw_items = fetch_dataset(r["dataset_id"])
        all_raw.extend(raw_items)
        posts_raw = flatten_posts(raw_items)
        for p in posts_raw:
            if not entry["profile_url"]:
                pu, name, headline = extract_author(p)
                entry["profile_url"] = pu or f"https://www.linkedin.com/in/{r['username']}/"
                entry["name"] = name
                entry["headline"] = headline
            shaped = shape_post(p)
            if shaped:
                entry["posts"].append(shaped)
        entry["posts"].sort(key=lambda x: x.get("date", ""), reverse=True)
        profiles.append(entry)

    if args.raw_output:
        raw_path = Path(args.raw_output)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(json.dumps(all_raw, indent=2, default=str), encoding="utf-8")
        print(f"Raw JSON saved to {args.raw_output}")

    result = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "actor": ACTOR_ID,
        "requested_profiles": args.profile_url,
        "posts_per_profile_requested": args.count,
        "profiles": profiles,
    }
    output_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    print("\nSummary:")
    for p in profiles:
        label = p["name"] or p["username"]
        print(f"  {label} [{p['status']}]: {len(p['posts'])} posts")
    print(f"\nWrote: {output_path}")


if __name__ == "__main__":
    main()
