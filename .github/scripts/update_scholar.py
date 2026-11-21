#!/usr/bin/env python3
"""Attempt to refresh Google Scholar citation metrics on the static site.

Google Scholar frequently blocks automated requests from GitHub Actions (datacenter IPs).
This script tries direct access first, then free proxies (via scholarly.ProxyGenerator),
and fails gracefully (exit 0, no changes) when blocked.
"""
import os
import re
import sys
import time
import random
from datetime import datetime
from pathlib import Path

try:
    from scholarly import scholarly, ProxyGenerator
except ImportError:
    print("scholarly not installed", file=sys.stderr)
    sys.exit(0)

AUTHOR_ID = "CYKwjg4AAAAJ"
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

def fetch_metrics(use_proxy=False):
    try:
        if use_proxy and IS_GITHUB_ACTIONS:
            print("Attempting free proxy setup for GitHub Actions...")
            try:
                pg = ProxyGenerator()
                success = pg.FreeProxies()
                if success:
                    scholarly.use_proxy(pg)
                    print("Free proxy configured.")
                else:
                    print("Free proxy setup failed; continuing direct.")
            except Exception as pe:
                print(f"Proxy error: {pe}. Continuing direct.")

        print(f"Fetching author {AUTHOR_ID}...")
        author = scholarly.search_author_id(AUTHOR_ID)
        author = scholarly.fill(author, sections=["basics", "indices", "counts"])
        metrics = {
            "citations": author.get("citedby"),
            "h_index": author.get("hindex"),
            "i10_index": author.get("i10index"),
            "pubs": author.get("publications_count") or len(author.get("publications", [])),
        }
        print(f"Fetched: {metrics}")
        return metrics
    except Exception as e:
        print(f"Fetch failed: {e}", file=sys.stderr)
        return None

def update_file(path: Path, metrics: dict, date_str: str) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    replacements = [
        (r'(<strong>)\d+(</strong><span>Citations</span>)', rf'\g<1>{metrics["citations"]}\g<2>'),
        (r'(<strong>)\d+(</strong><span>h-index</span>)', rf'\g<1>{metrics["h_index"]}\g<2>'),
        (r'(<strong>)\d+(</strong><span>i10-index</span>)', rf'\g<1>{metrics["i10_index"]}\g<2>'),
        (r'(<strong>)\d+(</strong><span>Publications</span>)', rf'\g<1>{metrics["pubs"]}\g<2>'),
        (r'Last updated from Google Scholar · [^.<]+', f'Last updated from Google Scholar · {date_str}'),
        (r'Citation counts are a Google Scholar snapshot from [^.<]+', f'Citation counts are a Google Scholar snapshot from {date_str}'),
        (r'\d+ publications by Mousa Moradi', f'{metrics["pubs"]} publications by Mousa Moradi'),
        (r'\d+ records, newest first', f'{metrics["pubs"]} records, newest first'),
    ]

    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text, count=1)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False

def main():
    print("=" * 50)
    print(f"Updating Scholar metrics for {AUTHOR_ID}")
    print(f"Running in GitHub Actions: {IS_GITHUB_ACTIONS}")
    print("=" * 50)

    # Small random delay
    time.sleep(random.uniform(1, 3))

    # Try direct first
    metrics = fetch_metrics(use_proxy=False)

    # If failed and in Actions, try with proxy
    if not metrics and IS_GITHUB_ACTIONS:
        print("Direct failed; retrying with free proxy...")
        metrics = fetch_metrics(use_proxy=True)

    if not metrics or not all(v is not None for v in metrics.values()):
        print("No usable metrics (likely blocked). Leaving files unchanged.")
        return

    now = datetime.utcnow()
    date_str = f"{now.strftime('%B')} {now.day}, {now.year}"

    changed = False
    for p in [Path("index.html"), Path("publications/index.html")]:
        if p.exists() and update_file(p, metrics, date_str):
            print(f"Updated {p}")
            changed = True

    if not changed:
        print("Metrics already current; no file changes.")

if __name__ == "__main__":
    main()
