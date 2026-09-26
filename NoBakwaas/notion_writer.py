# -*- coding: utf-8 -*-
"""
Pushes a design_trend_finder.py report into a Notion page, using
Notion's own REST API directly (just `requests`, no extra SDK -
same lightweight style as the rest of this repo).

Setup (one-time, see README.md):
  1. notion.so/my-integrations -> New integration -> copy the token
  2. Open the target Notion page -> "..." menu -> Connections -> add
     that integration
  3. Copy the page ID from its URL
  4. Set NOTION_API_KEY and NOTION_PAGE_ID (env vars or .env)
"""
import datetime as dt

import requests

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"


def _heading(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def _bullet(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def build_report_blocks(data: dict) -> list:
    """Turns a design_trend_finder.py result dict into Notion blocks."""
    timestamp = dt.datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")
    blocks = [_divider(), _heading(f"Trend Refresh - {timestamp}")]

    memes = data.get("trending_memes") or []
    if memes:
        blocks.append(_heading("Trending Memes"))
        for m in memes[:10]:
            blocks.append(_bullet(f"[{m['upvotes']} upvotes] {m['title']}"))
    else:
        blocks.append(_heading("Trending Memes"))
        blocks.append(_bullet("No live data this run (source blocked/unavailable) - check manually"))

    anime = data.get("trending_anime") or []
    if anime:
        blocks.append(_heading("Trending Anime"))
        for a in anime[:10]:
            genres = ", ".join(a.get("genres", []))
            blocks.append(_bullet(f"[{a['members']:,} members] {a['title']} ({genres})"))

    trends = data.get("google_trends_rising") or []
    if trends:
        blocks.append(_heading("Trending Fashion / Design Keywords (Google Trends India)"))
        for t in trends[:15]:
            blocks.append(_bullet(f"[{t['growth']}] {t['query']}  (from: {t['seed_keyword']})"))

    manual = data.get("manual_check_sources") or {}
    if manual:
        blocks.append(_heading("Manual-check sources (no free API)"))
        blocks.append(_bullet(f"Redbubble trending: {manual.get('redbubble_trending', '')}"))
        blocks.append(_bullet(f"Teepublic: {manual.get('teepublic_trending', '')}"))
        blocks.append(_bullet(f"Twitter/X: {manual.get('twitter_trends_india', '')}"))
        blocks.append(_bullet(f"Instagram Reels audio: {manual.get('instagram_reels_audio', '')}"))
        competitors = manual.get("competitor_bestsellers", [])
        if competitors:
            blocks.append(_bullet(f"Competitor bestsellers to check: {', '.join(competitors)}"))

    return blocks


def append_blocks(page_id: str, api_key: str, blocks: list):
    """Appends blocks to a Notion page. Chunks into groups of 100
    (Notion's per-request limit on children blocks)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    for i in range(0, len(blocks), 100):
        chunk = blocks[i:i + 100]
        resp = requests.patch(
            f"{BASE_URL}/blocks/{page_id}/children",
            headers=headers, json={"children": chunk}, timeout=30,
        )
        if not resp.ok:
            raise RuntimeError(f"Notion API error {resp.status_code}: {resp.text[:500]}")


def push_report(page_id: str, api_key: str, data: dict):
    blocks = build_report_blocks(data)
    append_blocks(page_id, api_key, blocks)
    return len(blocks)
