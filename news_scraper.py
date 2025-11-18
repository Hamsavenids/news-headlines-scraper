# news_scraper.py
"""
Robust news headlines scraper for TechCrunch + Economic Times (multiple feed fallbacks).
Writes CSV & XLSX, prints top-2 formatted summary.
Installs: pip install feedparser pandas openpyxl requests python-dateutil
Run: python news_scraper.py        (per_source mode: 4 per source)
     python news_scraper.py global (global_top mode: 4 total)
"""

import sys
import os
from datetime import datetime
import feedparser
import requests
import pandas as pd
from dateutil import parser as dateutil_parser

# --- CONFIG ---
FEEDS = {
    "TechCrunch": ["https://techcrunch.com/feed/"],
    # Economic Times: try several plausible RSS endpoints as fallbacks
    "Economic Times - Top Stories": [
        "https://b2b.economictimes.indiatimes.com/rss/topstories",
        "https://economictimes.indiatimes.com/feeds/newsdefault.cms",   # fallback attempt
        "https://economictimes.indiatimes.com/rssfeedsdefault.cms",   # another common pattern
        "https://economictimes.indiatimes.com/defaultinterstitial.cms" # user-provided (not an RSS, kept for debug)
    ],
}
HEADLINES_PER_SOURCE = 4
CSV_OUT = "news_headlines.csv"
XLSX_OUT = "news_headlines.xlsx"
MODE = "per_source" if not (len(sys.argv) > 1 and sys.argv[1].lower() in ("global","global_top")) else "global_top"
MAX_PER_SOURCE_FOR_GLOBAL = 12
TOTAL_GLOBAL_TOP = 4

# Use a browser-like User-Agent to avoid being served an HTML interstitial
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

# ---------------- functions ----------------
def fetch_feed_text(url, timeout=15):
    """Fetch raw text with requests using browser UA. Returns tuple(status_code, text, content_type)"""
    try:
        r = requests.get(url, headers=REQUEST_HEADERS, timeout=timeout)
        return (r.status_code, r.text, r.headers.get("Content-Type", ""))
    except Exception as e:
        return (None, None, f"error: {e}")

def parse_with_feedparser_from_text(text):
    """Parse feedparser on a text body (string). Returns feedparser result."""
    return feedparser.parse(text)

def try_feed_urls(url_list, max_items=4, debug_name=""):
    """
    Try each URL in url_list until we find entries. Returns list of entries (dicts).
    Also prints debug info for each attempt.
    """
    rows = []
    for url in url_list:
        print(f"\nTrying URL for {debug_name}: {url}")
        status, text, ctype = fetch_feed_text(url)
        print(f" HTTP status: {status}, Content-Type: {ctype[:80]}")
        if not text:
            print(" No response body; moving to next fallback.")
            continue

        parsed = parse_with_feedparser_from_text(text)
        print(f" feedparser.bozo: {getattr(parsed, 'bozo', False)}; entries found: {len(parsed.entries)}")
        if getattr(parsed, "bozo", False):
            print(f" bozo_exception: {getattr(parsed, 'bozo_exception', '')}")
            # If feedparser parsed any entries despite bozo, we can still use them.
        if len(parsed.entries) == 0:
            # show a short snippet to help debug why it's not an RSS
            snippet = text.strip()[:800].replace("\n", " ")
            print(" Snippet of response (first 800 chars):")
            print(snippet)
            continue

        # we have entries -> take up to max_items
        entries = parsed.entries[:max_items]
        for e in entries:
            title = getattr(e, "title", "").strip()
            link = getattr(e, "link", "").strip()
            published = getattr(e, "published", "") or getattr(e, "updated", "")
            published_dt = None
            if getattr(e, "published_parsed", None):
                try:
                    published_dt = datetime(*e.published_parsed[:6])
                except Exception:
                    published_dt = None
            else:
                # try parse textual date
                try:
                    if published:
                        published_dt = dateutil_parser.parse(published)
                except Exception:
                    published_dt = None
            rows.append({
                "source": debug_name,
                "title": title,
                "link": link,
                "published": published,
                "published_dt": published_dt
            })
        # stop after the first successful URL for this source
        break
    return rows

def dedupe(rows):
    seen = set()
    out = []
    for r in rows:
        key = (r.get("link") or r.get("title") or "").strip()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out

def save(rows):
    df = pd.DataFrame(rows)
    if "published_dt" in df.columns:
        df["published_dt_iso"] = df["published_dt"].apply(lambda x: x.isoformat() if x is not None else "")
        df = df.drop(columns=["published_dt"])
    df["scraped_at"] = datetime.now().isoformat()
    # desired order
    cols = [c for c in ["source","title","link","published","published_dt_iso","scraped_at"] if c in df.columns]
    df = df[cols]
    df.to_csv(CSV_OUT, index=False)
    df.to_excel(XLSX_OUT, index=False)
    return df

# -------------- main flow --------------
def main():
    print("Mode:", MODE)
    all_rows = []
    if MODE == "per_source":
        for source_name, urls in FEEDS.items():
            rows = try_feed_urls(urls, max_items=HEADLINES_PER_SOURCE, debug_name=source_name)
            print(f" -> fetched {len(rows)} item(s) for {source_name}")
            all_rows.extend(rows)
    else:
        # global mode: fetch more per source then pick top TOTAL_GLOBAL_TOP by datetime
        for source_name, urls in FEEDS.items():
            rows = try_feed_urls(urls, max_items=MAX_PER_SOURCE_FOR_GLOBAL, debug_name=source_name)
            print(f" -> fetched {len(rows)} item(s) for {source_name}")
            all_rows.extend(rows)
        # sort & limit
        all_rows = [r for r in all_rows if r.get("published_dt") is not None]
        all_rows.sort(key=lambda r: r["published_dt"], reverse=True)
        all_rows = all_rows[:TOTAL_GLOBAL_TOP]

    all_rows = dedupe(all_rows)
    if not all_rows:
        print("No headlines fetched from any source. See debug output above.")
        return

    df = save(all_rows)
    print(f"\nSaved {len(df)} rows to {CSV_OUT} and {XLSX_OUT}")

    # print top 2
    print("\n=== Top 2 Headlines (formatted summary) ===")
    for i, row in enumerate(df.head(2).itertuples(index=False), start=1):
        title = getattr(row, "title")
        src = getattr(row, "source")
        link = getattr(row, "link")
        pub = getattr(row, "published", "") or getattr(row, "published_dt_iso", "")
        print(f"\n[{i}] {title}\nSource : {src}\nLink   : {link}\nDate   : {pub}")

if __name__ == "__main__":
    main()
