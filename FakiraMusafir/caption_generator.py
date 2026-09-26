# -*- coding: utf-8 -*-
"""
Generates YouTube Shorts + Instagram Reels metadata (titles, descriptions,
hashtags, first-comment) for the 3 shorts and saves everything into
/final/shorts/metadata.json.
"""
import argparse
import json
from pathlib import Path

import config
from script_parser import parse_manual_input, get_block, ScriptBlock

SHORT_TYPES = ["SHORT1", "SHORT2", "SHORT3"]

YT_HASHTAGS = ["#shorts", "#travel", "#fakiramusafir"]
IG_HASHTAGS = ["#travelreels", "#indiantraveler", "#budgettravel", "#fakiramusafir",
               "#travelindia", "#reelsindia", "#traveltips"]

FIRST_COMMENT_QUESTIONS = [
    "Tumhara agla trip kaha ka plan hai? Comment karo 👇",
    "Yeh dekh ke kaunsa desh sabse pehle jaana hai? Batao!",
    "Solo ja rahe ho ya squad ke sath? Neeche batao 🌍",
]


def _yt_title(block: ScriptBlock) -> str:
    title = block.title.strip()
    if "#shorts" not in title.lower():
        title = f"{title} #Shorts"
    return title[:100]


def _yt_description(block: ScriptBlock, long_video_url: str = "") -> str:
    lines = [block.description.strip() or "Fakira Musafir ke saath ek aur mast trip ka scene.",
             ""]
    if long_video_url:
        lines.append(f"Full video: {long_video_url}")
    lines.append(" ".join(YT_HASHTAGS))
    return "\n".join(lines)


def _ig_caption(block: ScriptBlock) -> str:
    body = block.description.strip() or block.title
    hashtags = " ".join(IG_HASHTAGS)
    return f"{body}\n\nComment karo agla desh kaha jau? 🌏\n\n{hashtags}"


def build_metadata(long_video_url: str = "", manual_input_path=None) -> dict:
    blocks = parse_manual_input(manual_input_path)
    meta = {}

    for i, type_name in enumerate(SHORT_TYPES):
        if type_name not in blocks:
            continue
        block = blocks[type_name]
        meta[type_name] = {
            "youtube_shorts": {
                "title": _yt_title(block),
                "description": _yt_description(block, long_video_url),
                "tags": (block.tags + ["travel shorts", "fakira musafir", "visa free"])[:15],
                "hashtags": YT_HASHTAGS,
                "category_id": config.YOUTUBE_CATEGORY_TRAVEL,
            },
            "instagram_reels": {
                "caption": _ig_caption(block),
                "hashtags": IG_HASHTAGS,
                "first_comment": FIRST_COMMENT_QUESTIONS[i % len(FIRST_COMMENT_QUESTIONS)],
            },
            "thumbnail_text": block.thumbnail_text,
        }

    out_path = config.FINAL_SHORTS_DIR / "metadata.json"
    out_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[caption_generator] saved {out_path}")
    return meta


def main():
    parser = argparse.ArgumentParser(description="Generate Shorts/Reels metadata.json")
    parser.add_argument("--long-video-url", default="")
    args = parser.parse_args()
    build_metadata(args.long_video_url)


if __name__ == "__main__":
    main()
