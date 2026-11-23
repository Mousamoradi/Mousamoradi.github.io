#!/usr/bin/env python3
"""Refresh Google Scholar citation metrics and paper list using SerpAPI.

Updates aggregate metrics and regenerates the papers JSON on the publications page.
"""
import os
import re
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

AUTHOR_ID = "CYKwjg4AAAAJ"
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def infer_kind(venue: str) -> str:
    v = (venue or "").lower()
    if any(x in v for x in ["medrxiv", "biorxiv", "arxiv", "research square", "preprint"]):
        return "preprint"
    if any(x in v for x in ["thesis", "dissertation"]):
        return "thesis"
    if any(x in v for x in ["book", "chapter"]):
        return "book"
    if any(x in v for x in ["conference", "proc", "proceedings", "workshop", "symposium"]):
        return "conference"
    return "journal"

def make_id(year, title):
    slug = re.sub(r'[^a-z0-9]+', '-', (title or "").lower()).strip('-')[:60]
    return f"{year}-{slug}"

def fetch_data():
    if not SERPAPI_KEY:
        print("SERPAPI_KEY not set", file=sys.stderr)
        return None

    url = "https://serpapi.com/search"
    params = {
        "engine": "google_scholar_author",
        "author_id": AUTHOR_ID,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "num": 100,  # get more papers
    }

    try:
        print(f"Fetching author {AUTHOR_ID} via SerpAPI...")
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data
    except Exception as e:
        print(f"SerpAPI error: {e}", file=sys.stderr)
        return None

def extract_metrics(data):
    cited_by = data.get("cited_by", {})
    table = cited_by.get("table", [])

    citations = table[0].get("citations", {}).get("all") if len(table) > 0 else None
    h_index = table[1].get("indice_h", table[1].get("h_index", {})).get("all") if len(table) > 1 else None
    i10_index = table[2].get("indice_i10", table[2].get("i10_index", {})).get("all") if len(table) > 2 else None

    articles = data.get("articles", [])
    pubs = len(articles)

    return {
        "citations": citations,
        "h_index": h_index,
        "i10_index": i10_index,
        "pubs": pubs,
    }

def build_papers(data):
    articles = data.get("articles", [])
    papers = []
    for art in articles:
        year = art.get("year") or 0
        title = art.get("title") or ""
        authors = art.get("authors") or ""
        venue = art.get("publication") or ""
        href = art.get("link") or ""
        cites = art.get("cited_by", {}).get("value")

        paper = {
            "id": make_id(year, title),
            "year": year,
            "title": title,
            "authors": authors,
            "venue": venue,
            "kind": infer_kind(venue),
            "href": href,
        }
        if cites is not None:
            paper["citations"] = cites
        papers.append(paper)

    # Sort newest first
    papers.sort(key=lambda p: (p.get("year") or 0, p.get("title") or ""), reverse=True)
    return papers

def update_metrics(path: Path, metrics: dict, date_str: str) -> bool:
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

def update_papers(path: Path, papers: list) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    # Replace the JSON inside <script id="papers" type="application/json">...</script>
    json_str = json.dumps(papers, ensure_ascii=False, separators=(',', ':'))
    pattern = r'(<script id="papers" type="application/json">).*?(</script>)'
    text = re.sub(pattern, rf'\g<1>{json_str}\g<2>', text, count=1, flags=re.DOTALL)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False

def main():
    print("=" * 50)
    print(f"Updating Scholar data for {AUTHOR_ID} via SerpAPI")
    print("=" * 50)

    data = fetch_data()
    if not data:
        print("Failed to fetch data. Leaving files unchanged.")
        return

    metrics = extract_metrics(data)
    if not all(v is not None for v in metrics.values()):
        print(f"Incomplete metrics: {metrics}")
        return

    papers = build_papers(data)
    print(f"Fetched {len(papers)} papers")

    now = datetime.utcnow()
    date_str = f"{now.strftime('%B')} {now.day}, {now.year}"

    changed = False
    for p in [Path("index.html"), Path("publications/index.html")]:
        if p.exists() and update_metrics(p, metrics, date_str):
            print(f"Updated metrics in {p}")
            changed = True

    pubs_path = Path("publications/index.html")
    if pubs_path.exists() and update_papers(pubs_path, papers):
        print(f"Updated paper list in {pubs_path}")
        changed = True

    if not changed:
        print("Already up to date; no file changes.")

if __name__ == "__main__":
    main()
