# -*- coding: utf-8 -*-
"""
Pushes a trend_finder.py report into a Notion page via Notion's REST
API directly (just `requests`, no extra SDK) - same pattern as
NoBakwaas/notion_writer.py.

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
    timestamp = dt.datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")
    blocks = [_divider(), _heading(f"ELYNE Trend Refresh - {timestamp}")]

    marketing = data.get("marketing_rising_queries") or []
    if marketing:
        blocks.append(_heading("Marketing/Small-Business Rising Queries"))
        for t in marketing[:20]:
            blocks.append(_bullet(f"[{t['growth']}] {t['query']}  (from: {t['seed_keyword']})"))

    pain_points = data.get("business_pain_points") or []
    if pain_points:
        blocks.append(_heading("Business Pain Points (Reddit r/smallbusiness, r/marketing)"))
        for p in pain_points[:15]:
            blocks.append(_bullet(f"[{p['upvotes']} upvotes] {p['title']}"))
    else:
        blocks.append(_heading("Business Pain Points"))
        blocks.append(_bullet("No live data this run (source blocked/unavailable) - check manually"))

    manual = data.get("manual_check_sources") or {}
    if manual:
        blocks.append(_heading("Manual-check sources (no free API)"))
        for label, value in manual.items():
            blocks.append(_bullet(f"{label}: {value}"))

    return blocks


def append_blocks(page_id: str, api_key: str, blocks: list):
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
