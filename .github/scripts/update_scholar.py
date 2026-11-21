#!/usr/bin/env python3
"""Refresh Google Scholar citation metrics using SerpAPI.

Uses the google_scholar_author engine for exact citations, h-index, i10-index,
and publication count. Fails gracefully if the key is missing or the request fails.
"""
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

AUTHOR_ID = "CYKwjg4AAAAJ"
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def fetch_metrics():
    if not SERPAPI_KEY:
        print("SERPAPI_KEY not set", file=sys.stderr)
        return None

    url = "https://serpapi.com/search"
    params = {
        "engine": "google_scholar_author",
        "author_id": AUTHOR_ID,
        "api_key": SERPAPI_KEY,
        "hl": "en",
    }

    try:
        print(f"Fetching author {AUTHOR_ID} via SerpAPI...")
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Extract from author summary
        author = data.get("author", {})
        cited_by = author.get("cited_by", {})
        citations = cited_by.get("table", [{}])[0].get("citations", {}).get("all")
        h_index = cited_by.get("table", [{}])[1].get("h_index", {}).get("all")
        i10_index = cited_by.get("table", [{}])[2].get("i10_index", {}).get("all")

        # Publication count from articles list or total
        articles = data.get("articles", [])
        pubs = len(articles) if articles else data.get("search_information", {}).get("total_results")

        metrics = {
            "citations": citations,
            "h_index": h_index,
            "i10_index": i10_index,
            "pubs": pubs,
        }

        if all(v is not None for v in metrics.values()):
            print(f"Fetched: {metrics}")
            return metrics
        else:
            print(f"Incomplete metrics: {metrics}", file=sys.stderr)
            return None

    except Exception as e:
        print(f"SerpAPI error: {e}", file=sys.stderr)
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
    print(f"Updating Scholar metrics for {AUTHOR_ID} via SerpAPI")
    print("=" * 50)

    metrics = fetch_metrics()
    if not metrics or not all(v is not None for v in metrics.values()):
        print("No usable metrics. Leaving files unchanged.")
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
