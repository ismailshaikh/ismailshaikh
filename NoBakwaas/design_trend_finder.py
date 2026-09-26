# -*- coding: utf-8 -*-
"""
NoBakwaas design trend finder - FREE sources only, on-demand.

Pulls signal for new t-shirt/hoodie design ideas aimed at Indian Gen Z
streetwear buyers, across the 5 categories Ismail asked for:
  - Trending memes            -> Reddit (India meme subreddits)
  - Trending fashion           -> Google Trends India, rising queries around
                                  streetwear/tshirt/hoodie seed keywords
  - Trending dialogues         -> no reliable free API (see manual_check_sources)
  - Trending anime             -> MyAnimeList current season, via the free Jikan API
  - General design ideas       -> same Google Trends rising-query lookups above

This is meant to be run ON DEMAND (no scheduler) - either by Ismail
directly, or by asking Claude "design trends do" in chat, which runs
the same free lookups live and refreshes the Notion page.

NOT automated here (no reliable free API, checked manually instead):
  - Redbubble / Teepublic "Trending" tag pages - no public API, and
    scraping their JS-rendered trending page is unreliable. Browse
    redbubble.com/shop/trending and teepublic.com by hand instead.
  - X/Twitter "Trends for India" - X's API is paid now. Check the
    app's Trends tab by hand.
  - Instagram Reels trending audio - no public API. Browse Explore by hand.

Usage:
    python design_trend_finder.py                    # print + save design_trends.json
    python design_trend_finder.py --top 10
"""
import argparse
import datetime as dt
import json
import re
from pathlib import Path

import requests

OUTPUT_FILE = Path(__file__).resolve().parent / "design_trends.json"

REDDIT_MEME_SUBREDDITS = ["IndianDankMemes", "india", "bakchodi"]
GOOGLE_TRENDS_KEYWORDS = [
    "streetwear",
    "oversized tshirt",
    "hoodie",
    "anime tshirt",
    "meme tshirt",
]
GOOGLE_TRENDS_DELAY_SECONDS = 8  # unofficial API rate-limits (HTTP 429) if hit faster than this
JIKAN_SEASON_URL = "https://api.jikan.moe/v4/seasons/now"


# ---------------------------------------------------------------------------
# Source 1: Trending memes - Reddit (free, no key)
# ---------------------------------------------------------------------------
def fetch_trending_memes(subreddits=None, limit_per_sub=10):
    subreddits = subreddits or REDDIT_MEME_SUBREDDITS
    headers = {"User-Agent": "NoBakwaasDesignTrendFinder/1.0"}
    results = []

    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/top.json"
        try:
            resp = requests.get(url, params={"t": "week", "limit": limit_per_sub},
                                 headers=headers, timeout=10)
            resp.raise_for_status()
            posts = resp.json()["data"]["children"]
        except Exception as e:
            print(f"[design_trend_finder] Reddit failed for r/{sub}: {e}")
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
# Source 2: Trending anime - MyAnimeList current season via Jikan (free, no key)
# ---------------------------------------------------------------------------
def fetch_trending_anime(top_n=10):
    try:
        resp = requests.get(JIKAN_SEASON_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()["data"]
    except Exception as e:
        print(f"[design_trend_finder] Jikan/MAL failed: {e}")
        return []

    ranked = sorted(data, key=lambda a: a.get("members", 0), reverse=True)
    return [
        {
            "title": a.get("title"),
            "members": a.get("members", 0),
            "genres": [g["name"] for g in a.get("genres", [])],
            "url": a.get("url"),
        }
        for a in ranked[:top_n]
    ]


# ---------------------------------------------------------------------------
# Source 3/4/5: Trending fashion / dialogues / general ideas - Google Trends
# ---------------------------------------------------------------------------
def fetch_google_trends_rising(keywords=None, geo="IN"):
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("[design_trend_finder] pytrends not installed, skipping Google Trends source")
        return []

    import time

    keywords = keywords or GOOGLE_TRENDS_KEYWORDS
    try:
        pytrends = TrendReq(hl="en-IN", tz=330)
    except Exception as e:
        print(f"[design_trend_finder] pytrends init failed: {e}")
        return []

    results = []
    for i, kw in enumerate(keywords):
        if i > 0:
            time.sleep(GOOGLE_TRENDS_DELAY_SECONDS)  # avoid HTTP 429 rate limiting
        try:
            pytrends.build_payload([kw], geo=geo, timeframe="today 3-m")
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
            print(f"[design_trend_finder] Google Trends failed for '{kw}' (rate-limited? wait longer between runs): {e}")
            continue
    return results


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------
def find_design_trends(top_n: int = 10) -> dict:
    print("[design_trend_finder] fetching trending memes (Reddit)...")
    memes = fetch_trending_memes()[:top_n]
    print("[design_trend_finder] fetching trending anime (MyAnimeList)...")
    anime = fetch_trending_anime(top_n)
    print("[design_trend_finder] fetching Google Trends rising queries (fashion/dialogues/general)...")
    trends = fetch_google_trends_rising()[:top_n * 2]

    return {
        "generated_at_utc": dt.datetime.utcnow().isoformat(),
        "trending_memes": memes,
        "trending_anime": anime,
        "google_trends_rising": trends,
        "manual_check_sources": {
            "redbubble_trending": "https://www.redbubble.com/shop/trending",
            "teepublic_trending": "https://www.teepublic.com/",
            "twitter_trends_india": "X/Twitter app -> Trends for India tab",
            "instagram_reels_audio": "Instagram app -> Explore/Reels tab",
            "competitor_bestsellers": [
                "bewakoof.com", "thesouledstore.com", "redwolf.in", "bonkerscorner.com",
            ],
        },
    }


def save_json(data: dict, path=None):
    path = Path(path) if path else OUTPUT_FILE
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[design_trend_finder] saved {path}")


def main():
    parser = argparse.ArgumentParser(description="Find NoBakwaas design trend ideas from free sources")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    data = find_design_trends(top_n=args.top)
    save_json(data)

    print("\n=== TRENDING MEMES ===")
    for m in data["trending_memes"]:
        print(f"  [{m['upvotes']}] {m['title']}")

    print("\n=== TRENDING ANIME ===")
    for a in data["trending_anime"]:
        print(f"  [{a['members']} members] {a['title']} ({', '.join(a['genres'])})")

    print("\n=== GOOGLE TRENDS RISING (fashion/general) ===")
    for t in data["google_trends_rising"]:
        print(f"  [{t['growth']}] {t['query']} (from: {t['seed_keyword']})")


if __name__ == "__main__":
    main()
