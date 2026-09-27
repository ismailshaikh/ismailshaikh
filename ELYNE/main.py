# -*- coding: utf-8 -*-
"""
ELYNE System - main orchestrator. Same pattern as FakiraMusafir/main.py
and NoBakwaas/main.py: one command runs the whole pipeline.

Usage:
    python main.py                  # research + push fresh report to Notion
    python main.py --top 15
    python main.py --no-notion      # just print/save locally, skip Notion push

On-demand only - no scheduler, no n8n. Run it yourself, or ask Claude
"ELYNE trending topics do" and it runs this same pipeline live.
"""
import argparse

import config
from trend_finder import find_elyne_trends, save_json
from notion_writer import push_report


def run(top_n: int = 15, push_to_notion: bool = True) -> dict:
    data = find_elyne_trends(top_n=top_n)
    save_json(data)

    if not push_to_notion:
        print("[main] --no-notion set, skipping Notion push")
        return data

    if not config.NOTION_API_KEY or not config.NOTION_PAGE_ID:
        print("[main] NOTION_API_KEY / NOTION_PAGE_ID not set - skipping Notion push.")
        print("[main] See README.md for one-time Notion integration setup.")
        return data

    try:
        block_count = push_report(config.NOTION_PAGE_ID, config.NOTION_API_KEY, data)
        print(f"[main] pushed {block_count} blocks to Notion page {config.NOTION_PAGE_ID}")
    except Exception as e:
        print(f"[main] Notion push failed: {e}")

    return data


def main():
    parser = argparse.ArgumentParser(description="ELYNE System trend + content-idea pipeline")
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--no-notion", action="store_true", help="Skip pushing results to Notion")
    args = parser.parse_args()

    run(top_n=args.top, push_to_notion=not args.no_notion)
    print("\n[main] Done. Check elyne_trends.json and your Notion page.")


if __name__ == "__main__":
    main()
