#!/usr/bin/env python3
"""Attempt to refresh Google Scholar citation metrics on the static site.

Google Scholar frequently blocks automated requests. This script fails gracefully
(exit 0 with no changes) when it cannot fetch fresh data.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from scholarly import scholarly
except ImportError:
    print("scholarly not installed", file=sys.stderr)
    sys.exit(0)

AUTHOR_ID = "CYKwjg4AAAAJ"

def fetch_metrics():
    try:
        author = scholarly.search_author_id(AUTHOR_ID)
        author = scholarly.fill(author, sections=["basics", "indices", "counts"])
        return {
            "citations": author.get("citedby"),
            "h_index": author.get("hindex"),
            "i10_index": author.get("i10index"),
            "pubs": author.get("publications_count") or len(author.get("publications", [])),
        }
    except Exception as e:
        print(f"Could not fetch Scholar metrics: {e}", file=sys.stderr)
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
    metrics = fetch_metrics()
    if not metrics or not all(v is not None for v in metrics.values()):
        print("No usable metrics; leaving files unchanged.")
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
