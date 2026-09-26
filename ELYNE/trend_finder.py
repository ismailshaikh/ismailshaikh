# -*- coding: utf-8 -*-
"""
ELYNE System design trend finder - FREE sources, on-demand (no cron).

ELYNE's own organic content plays "trend-jacking": take whatever is
trending in India generally (not a fixed niche, since the audience is
local business owners across every industry) and turn it into a
marketing/business-tip post - "yeh trend, yeh business lesson".

Sources (all free, no API key):
  - Google Trends India - rising queries around marketing/small
    business keywords (for on-topic content ideas)
  - Reddit r/smallbusiness, r/marketing, r/IndianStartups (real pain
    points and questions local business owners actually ask)

NOT included: Google Trends' general daily "Trending Now" list
(pytrends.trending_searches()) - checked, it reliably 404s because
Google changed the underlying endpoint and pytrends hasn't caught up.
Not a transient issue, so it's left out rather than shipping a dead
source. For general trend-jacking material, check Twitter/X Trends
or Instagram Explore by hand (see manual_check_sources below).

Usage:
    python trend_finder.py
    python trend_finder.py --top 15
"""
import argparse
import datetime as dt
import json
import time
from pathlib import Path

import requests

OUTPUT_FILE = Path(__file__).resolve().parent / "elyne_trends.json"

MARKETING_KEYWORDS = [
    "small business marketing",
    "instagram reels",
    "google my business",
    "whatsapp marketing",
    "digital marketing",
]
REDDIT_SUBREDDITS = ["smallbusiness", "marketing", "IndianStartups"]
GOOGLE_TRENDS_DELAY_SECONDS = 8


# ---------------------------------------------------------------------------
# Source 1: Google Trends India - rising queries for marketing keywords
# ---------------------------------------------------------------------------
def fetch_marketing_rising_queries(keywords=None):
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("[trend_finder] pytrends not installed, skipping marketing rising queries")
        return []

    keywords = keywords or MARKETING_KEYWORDS
    try:
        pytrends = TrendReq(hl="en-IN", tz=330)
    except Exception as e:
        print(f"[trend_finder] pytrends init failed: {e}")
        return []

    results = []
    for i, kw in enumerate(keywords):
        if i > 0:
            time.sleep(GOOGLE_TRENDS_DELAY_SECONDS)
        try:
            pytrends.build_payload([kw], geo="IN", timeframe="today 3-m")
            related = pytrends.related_queries().get(kw, {})
            rising = related.get("rising")
            if rising is None or rising.empty:
                continue
            for _, row in rising.iterrows():
                results.append({
                    "query": str(row.get("query", "")),
                    "growth": str(row.get("value", "")),
                    "seed_keyword": kw,
                })
        except Exception as e:
            print(f"[trend_finder] Google Trends failed for '{kw}' (rate-limited? wait longer between runs): {e}")
            continue
    return results


# ---------------------------------------------------------------------------
# Source 2: Reddit - real small-business/marketing pain points (free, no key)
# ---------------------------------------------------------------------------
def fetch_reddit_pain_points(subreddits=None, limit_per_sub=10):
    subreddits = subreddits or REDDIT_SUBREDDITS
    headers = {"User-Agent": "ELYNETrendFinder/1.0"}
    results = []

    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/top.json"
        try:
            resp = requests.get(url, params={"t": "week", "limit": limit_per_sub},
                                 headers=headers, timeout=10)
            resp.raise_for_status()
            posts = resp.json()["data"]["children"]
        except Exception as e:
            print(f"[trend_finder] Reddit failed for r/{sub}: {e}")
            continue

        for post in posts:
            data = post["data"]
            results.append({
                "title": data.get("title", ""),
                "upvotes": data.get("ups", 0),
                "source": f"reddit_r/{sub}",
                "url": f"https://reddit.com{data.get('permalink', '')}",
            })

    results.sort(key=lambda r: r["upvotes"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------
def find_elyne_trends(top_n: int = 15) -> dict:
    print("[trend_finder] fetching marketing/small-business rising queries...")
    marketing_trends = fetch_marketing_rising_queries()[:top_n * 2]
    print("[trend_finder] fetching Reddit small-business/marketing pain points...")
    pain_points = fetch_reddit_pain_points()[:top_n]

    return {
        "generated_at_utc": dt.datetime.utcnow().isoformat(),
        "marketing_rising_queries": marketing_trends,
        "business_pain_points": pain_points,
        "manual_check_sources": {
            "instagram_reels_audio": "Instagram app -> Explore/Reels tab - note repeated trending audio",
            "linkedin_trending": "LinkedIn app -> browse feed for what marketing content is getting engagement",
            "twitter_trends_india": "X/Twitter app -> Trends for India tab",
        },
    }


def save_json(data: dict, path=None):
    path = Path(path) if path else OUTPUT_FILE
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[trend_finder] saved {path}")


def main():
    parser = argparse.ArgumentParser(description="Find trending topics for ELYNE's own organic content")
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()

    data = find_elyne_trends(top_n=args.top)
    save_json(data)

    print("\n=== MARKETING/SMALL-BUSINESS RISING QUERIES ===")
    for t in data["marketing_rising_queries"]:
        print(f"  [{t['growth']}] {t['query']} (from: {t['seed_keyword']})")

    print("\n=== BUSINESS PAIN POINTS (Reddit) ===")
    for p in data["business_pain_points"]:
        print(f"  [{p['upvotes']}] {p['title']}")


if __name__ == "__main__":
    main()
