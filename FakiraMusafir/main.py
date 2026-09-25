# -*- coding: utf-8 -*-
"""
Fakira Musafir - main orchestrator.

Usage:
    python main.py --mode long                 # build only the long video
    python main.py --mode shorts-only           # build only the 3 shorts/reels
    python main.py --mode long+shorts           # build long, then the 3 shorts
    python main.py --mode long --upload         # also upload to YouTube
    python main.py --mode long+shorts --upload  # upload long + shorts (IG stays manual)

Before running: paste today's Claude Pro output into
/scripts/manual_input.txt using the format from /prompts/*.txt.
"""
import argparse

import config
from script_parser import get_block
from voiceover import generate_voiceover
from downloader import download_broll
from builder import build_long_video, pick_music
from thumbnail import generate_thumbnail


def run_long(upload: bool = False) -> dict:
    block = get_block("LONG")
    voice_path = generate_voiceover(block)
    download_broll(block, target_count=config.LONG_CLIP_COUNT[1])
    music_path = pick_music()
    video_path = build_long_video(block, voice_path, music_path=music_path)
    thumb_path = generate_thumbnail(block)

    video_url = ""
    if upload:
        from uploader import upload_long_video
        video_id = upload_long_video(block, video_path, thumb_path)
        video_url = f"https://youtu.be/{video_id}"

    return {"video": video_path, "thumbnail": thumb_path, "url": video_url}


def run_shorts(upload: bool = False, long_video_url: str = "") -> dict:
    from shorts_builder import build_all_shorts
    results = build_all_shorts(long_video_url=long_video_url)

    if upload:
        from uploader_shorts import upload_all_shorts
        upload_all_shorts()

    return results


def main():
    parser = argparse.ArgumentParser(description="Fakira Musafir automation pipeline")
    parser.add_argument("--mode", choices=["long", "shorts-only", "long+shorts"], default="long")
    parser.add_argument("--upload", action="store_true", help="Also upload finished video(s) to YouTube")
    args = parser.parse_args()

    if args.mode == "long":
        run_long(upload=args.upload)
    elif args.mode == "shorts-only":
        run_shorts(upload=args.upload)
    elif args.mode == "long+shorts":
        long_result = run_long(upload=args.upload)
        run_shorts(upload=args.upload, long_video_url=long_result.get("url", ""))

    print("\n[main] Done. Check /final/long, /final/shorts, /final/reels and /thumbnails.")


if __name__ == "__main__":
    main()
