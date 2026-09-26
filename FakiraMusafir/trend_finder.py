# -*- coding: utf-8 -*-
"""
Trending topic finder for Fakira Musafir - Phase 1, FREE sources only.

Combines signal from every source that actually has a free, scriptable
way in:
  - YouTube Data API v3 search (real videos, real view velocity)
  - Google Trends rising queries (via pytrends, no key needed)
  - YouTube search autosuggest (unofficial free endpoint)
  - Reddit hot posts from travel subreddits (public JSON, no key needed)

Then it normalizes, cross-checks and DEDUPES everything into one ranked
list so the same idea from 3 sources doesn't show up 3 times, and skips
anything already sitting in topics.csv / topics_shorts.csv.

NOT included here because they have no free scriptable API - these stay
manual (see README "Trending Topics Finder" section):
  - YouTube Studio "Research" tab (Studio UI only)
  - TubeBuddy free tier (browser extension only)
  - Social Blade (no free API)
  - Quora (no public API)
  - vidIQ deep search (MCP-tool only, ask Claude directly when you want it -
    it isn't reachable from a plain Python script)

Usage:
    python trend_finder.py                          # print + save trending_topics.csv
    python trend_finder.py --append-to-topics        # also append fresh ones into topics.csv
    python trend_finder.py --top 15
"""
import argparse
import csv
import datetime as dt
import re
from collections import defaultdict
from pathlib import Path

import requests

import config

STOPWORDS = {
    "the", "a", "an", "is", "are", "in", "on", "of", "to", "for", "with",
    "and", "or", "how", "what", "why", "your", "you", "me", "i", "this",
    "that", "ka", "ki", "ke", "ko", "se", "me", "mein", "hai", "ho", "kya",
    "kaise", "kaha", "kahan", "aur", "ek", "sabse", "video", "shorts",
}


# ---------------------------------------------------------------------------
# normalization + dedup
# ---------------------------------------------------------------------------
def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokens(text: str) -> set:
    return {t for t in normalize(text).split() if t and t not in STOPWORDS}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_existing_topics() -> list:
    """Loads topic strings already sitting in topics.csv / topics_shorts.csv
    so we never re-suggest something you already have."""
    existing = []
    for path in (config.ROOT / "topics.csv", config.ROOT / "topics_shorts.csv"):
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                topic = row.get("topic")
                if topic:
                    existing.append(topic)
    return existing


class CandidatePool:
    """Collects candidates from every source, merges near-duplicates, and
    boosts the score of anything confirmed by more than one source."""

    def __init__(self, existing_topics):
        self.items = []  # list of dicts: topic, score, sources(set), tokens
        self.existing_tokens = [tokens(t) for t in existing_topics]

    def add(self, topic: str, score: float, source: str):
        topic = topic.strip()
        if not topic or len(topic) < 4:
            return
        tk = tokens(topic)
        if not tk:
            return

        # skip if it's basically already one of our curated topics
        for ex_tk in self.existing_tokens:
            if jaccard(tk, ex_tk) >= config.TREND_DEDUP_THRESHOLD:
                return

        # merge into an existing candidate if similar enough
        for item in self.items:
            if jaccard(tk, item["tokens"]) >= config.TREND_DEDUP_THRESHOLD:
                item["score"] = max(item["score"], score) + 8  # cross-source boost
                item["sources"].add(source)
                if len(topic) > len(item["topic"]):
                    item["topic"] = topic  # keep the more descriptive phrasing
                return

        self.items.append({"topic": topic, "score": score, "sources": {source}, "tokens": tk})

    def ranked(self, top_n: int) -> list:
        ranked = sorted(self.items, key=lambda i: i["score"], reverse=True)
        return ranked[:top_n]


# ---------------------------------------------------------------------------
# Source 1: YouTube Data API v3 search (real videos, view velocity)
# ---------------------------------------------------------------------------
def fetch_youtube_candidates(pool: CandidatePool, seed_keywords=None):
    if not config.YOUTUBE_API_KEY:
        print("[trend_finder] YOUTUBE_API_KEY not set, skipping YouTube source")
        return

    from googleapiclient.discovery import build
    youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)
    seed_keywords = seed_keywords or config.TREND_SEED_KEYWORDS
    published_after = (dt.datetime.utcnow() - dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    for seed in seed_keywords:
        try:
            resp = youtube.search().list(
                q=seed, part="snippet", type="video", order="viewCount",
                publishedAfter=published_after, regionCode="IN", relevanceLanguage="hi",
                maxResults=8,
            ).execute()
        except Exception as e:
            print(f"[trend_finder] YouTube search failed for '{seed}': {e}")
            continue

        video_ids = [item["id"]["videoId"] for item in resp.get("items", [])]
        if not video_ids:
            continue

        try:
            stats_resp = youtube.videos().list(part="statistics", id=",".join(video_ids)).execute()
        except Exception as e:
            print(f"[trend_finder] YouTube stats failed: {e}")
            stats_resp = {"items": []}
        stats_by_id = {v["id"]: v["statistics"] for v in stats_resp.get("items", [])}

        for item in resp.get("items", []):
            vid = item["id"]["videoId"]
            title = item["snippet"]["title"]
            views = int(stats_by_id.get(vid, {}).get("viewCount", 0))
            # simple recency-normalized score: views in the last 7 days, capped
            score = min(views / 500, 100)
            pool.add(title, score, "youtube")


# ---------------------------------------------------------------------------
# Source 2: Google Trends rising queries (pytrends, free, no key)
# ---------------------------------------------------------------------------
def fetch_google_trends_candidates(pool: CandidatePool, seed_keywords=None):
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("[trend_finder] pytrends not installed, skipping Google Trends source")
        return

    seed_keywords = seed_keywords or config.TREND_SEED_KEYWORDS
    try:
        pytrends = TrendReq(hl="en-IN", tz=330)
    except Exception as e:
        print(f"[trend_finder] pytrends init failed: {e}")
        return

    for seed in seed_keywords:
        try:
            pytrends.build_payload([seed], geo="IN", timeframe="now 7-d")
            related = pytrends.related_queries().get(seed, {})
            rising = related.get("rising")
            if rising is None or rising.empty:
                continue
            for _, row in rising.iterrows():
                query = str(row.get("query", ""))
                growth = str(row.get("value", "100"))
                growth_num = 100
                if "+" in growth or "%" in growth:
                    digits = re.sub(r"[^\d]", "", growth) or "100"
                    growth_num = min(int(digits), 500)
                pool.add(query, min(growth_num / 5, 100), "google_trends")
        except Exception as e:
            print(f"[trend_finder] Google Trends failed for '{seed}': {e}")
            continue


# ---------------------------------------------------------------------------
# Source 3: YouTube search autosuggest (unofficial, free, no key)
# ---------------------------------------------------------------------------
def fetch_autosuggest_candidates(pool: CandidatePool, seed_keywords=None):
    seed_keywords = seed_keywords or config.TREND_SEED_KEYWORDS
    url = "http://suggestqueries.google.com/complete/search"

    for seed in seed_keywords:
        try:
            resp = requests.get(url, params={"client": "firefox", "ds": "yt", "q": seed}, timeout=10)
            resp.raise_for_status()
            suggestions = resp.json()[1]
        except Exception as e:
            print(f"[trend_finder] autosuggest failed for '{seed}': {e}")
            continue

        for suggestion in suggestions:
            # baseline score: someone is actively typing this into YouTube search
            pool.add(suggestion, 35, "youtube_autosuggest")


# ---------------------------------------------------------------------------
# Source 4: Reddit hot posts from travel subreddits (public JSON, no key)
# ---------------------------------------------------------------------------
def fetch_reddit_candidates(pool: CandidatePool, subreddits=None):
    subreddits = subreddits or config.REDDIT_SUBREDDITS
    headers = {"User-Agent": "FakiraMusafirTrendFinder/1.0"}

    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/top.json"
        try:
            resp = requests.get(url, params={"t": "week", "limit": 25}, headers=headers, timeout=10)
            resp.raise_for_status()
            posts = resp.json()["data"]["children"]
        except Exception as e:
            print(f"[trend_finder] Reddit failed for r/{sub}: {e}")
            continue

        for post in posts:
            data = post["data"]
            title = data.get("title", "")
            upvotes = data.get("ups", 0)
            score = min(upvotes / 20, 100)
            pool.add(title, score, f"reddit_r/{sub}")


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------
def find_trending_topics(top_n: int = 20) -> list:
    existing = load_existing_topics()
    pool = CandidatePool(existing)

    print("[trend_finder] fetching from YouTube Data API...")
    fetch_youtube_candidates(pool)
    print("[trend_finder] fetching from Google Trends...")
    fetch_google_trends_candidates(pool)
    print("[trend_finder] fetching from YouTube autosuggest...")
    fetch_autosuggest_candidates(pool)
    print("[trend_finder] fetching from Reddit...")
    fetch_reddit_candidates(pool)

    ranked = pool.ranked(top_n)
    print(f"[trend_finder] {len(pool.items)} unique candidates found, showing top {len(ranked)}")
    return ranked


def save_trending_csv(ranked: list, path=None):
    path = Path(path) if path else config.TREND_OUTPUT_FILE
    now = dt.datetime.utcnow().isoformat()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "topic", "score", "sources", "detected_at_utc"])
        for i, item in enumerate(ranked, 1):
            writer.writerow([i, item["topic"], round(item["score"], 1),
                              "|".join(sorted(item["sources"])), now])
    print(f"[trend_finder] saved {path}")


def append_to_topics_csv(ranked: list, path=None):
    path = Path(path) if path else (config.ROOT / "topics.csv")
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    next_id = max((int(r["id"]) for r in rows), default=0) + 1

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for item in ranked:
            writer.writerow([next_id, item["topic"], "trending_auto"])
            next_id += 1
    print(f"[trend_finder] appended {len(ranked)} new topics to {path}")


def main():
    parser = argparse.ArgumentParser(description="Find trending Hindi travel topics from free sources")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--append-to-topics", action="store_true",
                         help="Also append fresh (non-duplicate) topics to topics.csv")
    args = parser.parse_args()

    ranked = find_trending_topics(top_n=args.top)
    save_trending_csv(ranked)

    print("\n=== TOP TRENDING TOPICS (Fakira Musafir niche) ===")
    for i, item in enumerate(ranked, 1):
        print(f"{i:2d}. [{item['score']:.0f}] {item['topic']}  ({', '.join(sorted(item['sources']))})")

    if args.append_to_topics:
        append_to_topics_csv(ranked)


if __name__ == "__main__":
    main()
