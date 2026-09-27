# -*- coding: utf-8 -*-
"""
Shorts & Reels factory: turns the 3 SHORT scripts in manual_input.txt
(generated from /prompts/shorts_factory_prompt.txt) into 3 finished
YouTube Shorts + 3 Instagram Reels.

Pipeline per short: voiceover -> b-roll download -> 9:16 build with
word-pop captions -> copy into /final/reels/ + generate a reel cover.
"""
import argparse
import shutil
from pathlib import Path

import config
from script_parser import parse_manual_input, ScriptBlock
from voiceover import generate_voiceover
from downloader import download_broll
from builder import build_vertical_video, pick_music
from thumbnail_brief import write_vertical_brief
from caption_generator import build_metadata

SHORT_TYPES = ["SHORT1", "SHORT2", "SHORT3"]


def build_one_short(block: ScriptBlock, music_path=None, auto_thumbnail: bool = False) -> dict:
    print(f"\n=== Building {block.type} ===")
    voice_path = generate_voiceover(block)
    download_broll(block, target_count=config.SHORT_CLIP_COUNT[1])
    short_path = build_vertical_video(block, voice_path, music_path=music_path)

    reel_path = config.FINAL_REELS_DIR / f"{block.type.lower()}_9x16.mp4"
    shutil.copyfile(short_path, reel_path)

    brief_path = write_vertical_brief(block)
    cover_export_path = config.THUMBNAILS_DIR / f"{block.type.lower()}_cover.png"
    if auto_thumbnail and not cover_export_path.exists():
        from thumbnail import generate_reel_cover
        generate_reel_cover(block, out_path=cover_export_path)
    cover_path = str(cover_export_path) if cover_export_path.exists() else None

    print(f"[shorts_builder] {block.type}: short={short_path} reel={reel_path} "
          f"cover={cover_path or ('not exported yet, brief: ' + brief_path)}")
    return {"short": short_path, "reel": str(reel_path), "brief": brief_path, "cover": cover_path}


def build_all_shorts(manual_input_path=None, long_video_url: str = "", auto_thumbnail: bool = False) -> dict:
    blocks = parse_manual_input(manual_input_path)
    music_path = pick_music()
    results = {}

    for type_name in SHORT_TYPES:
        block = blocks.get(type_name)
        if not block:
            print(f"[shorts_builder] no {type_name} block in manual_input.txt, skipping")
            continue
        results[type_name] = build_one_short(block, music_path=music_path, auto_thumbnail=auto_thumbnail)

    build_metadata(long_video_url=long_video_url, manual_input_path=manual_input_path)
    _write_reels_upload_ready(results, blocks)
    return results


def _write_reels_upload_ready(results: dict, blocks: dict):
    """Phase 1 free path for Instagram: no Graph API approval needed,
    just a copy-paste-ready caption file next to each reel."""
    import json
    meta_path = config.FINAL_SHORTS_DIR / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    lines = ["FAKIRA MUSAFIR - INSTAGRAM REELS - MANUAL UPLOAD READY", "=" * 55, ""]
    for type_name, paths in results.items():
        ig = meta.get(type_name, {}).get("instagram_reels", {})
        cover_line = paths["cover"] if paths["cover"] else f"not exported yet - design using {paths['brief']}"
        lines.append(f"[{type_name}] video: {paths['reel']}")
        lines.append(f"cover:  {cover_line}")
        lines.append("caption:")
        lines.append(ig.get("caption", ""))
        lines.append(f"first comment: {ig.get('first_comment', '')}")
        lines.append("-" * 55)

    out_path = config.FINAL_REELS_DIR / "upload_ready.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[shorts_builder] {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Build all 3 Shorts + Reels from manual_input.txt")
    parser.add_argument("--long-video-url", default="", help="Link to the long video for Shorts descriptions")
    parser.add_argument("--auto-thumbnail", action="store_true",
                         help="Instant PIL-generated cover as a fallback if you don't have time to design in Canva")
    args = parser.parse_args()
    build_all_shorts(long_video_url=args.long_video_url, auto_thumbnail=args.auto_thumbnail)


if __name__ == "__main__":
    main()
