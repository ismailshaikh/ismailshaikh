# -*- coding: utf-8 -*-
"""
Uploads the 3 built Shorts to YouTube (FREE, Data API v3) at IST
11 AM / 3 PM / 8 PM. Instagram Reels: Option A (FREE, manual) writes
a ready-to-paste caption file; Option B (Graph API, needs Meta app
review) is commented out below for Phase 2.
"""
import argparse
import datetime as dt
import json
from pathlib import Path

from googleapiclient.http import MediaFileUpload

import config
from script_parser import parse_manual_input, ScriptBlock
from setup_youtube_auth import get_authenticated_service

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
SHORT_TYPES = ["SHORT1", "SHORT2", "SHORT3"]


def _publish_at_for_slot(slot_index: int) -> str:
    time_str = config.SHORTS_UPLOAD_TIMES_IST[slot_index % len(config.SHORTS_UPLOAD_TIMES_IST)]
    hour, minute = map(int, time_str.split(":"))
    now_ist = dt.datetime.now(IST)
    target = now_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now_ist:
        target += dt.timedelta(days=1)
    return target.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def upload_short(block: ScriptBlock, video_path: str, meta: dict, slot_index: int,
                  schedule: bool = True) -> str:
    youtube = get_authenticated_service()
    yt_meta = meta.get("youtube_shorts", {})

    title = yt_meta.get("title") or block.title
    if "#shorts" not in title.lower():
        title += " #Shorts"

    body = {
        "snippet": {
            "title": title[:100],
            "description": yt_meta.get("description", block.description),
            "tags": yt_meta.get("tags", block.tags)[:15],
            "categoryId": config.YOUTUBE_CATEGORY_TRAVEL,
            "defaultLanguage": config.YOUTUBE_DEFAULT_LANGUAGE,
        },
        "status": {"selfDeclaredMadeForKids": False},
    }
    if schedule:
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = _publish_at_for_slot(slot_index)
    else:
        body["status"]["privacyStatus"] = "public"

    media = MediaFileUpload(video_path, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[uploader_shorts] {block.type} upload {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"[uploader_shorts] {block.type} uploaded: https://youtube.com/shorts/{video_id}")
    return video_id


def upload_all_shorts(manual_input_path=None, schedule: bool = True):
    blocks = parse_manual_input(manual_input_path)
    meta_path = config.FINAL_SHORTS_DIR / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    for i, type_name in enumerate(SHORT_TYPES):
        block = blocks.get(type_name)
        video_path = config.FINAL_SHORTS_DIR / f"{type_name.lower()}_9x16.mp4"
        if not block or not video_path.exists():
            print(f"[uploader_shorts] skipping {type_name}, missing script or built video")
            continue
        upload_short(block, str(video_path), meta.get(type_name, {}), i, schedule=schedule)

    print("[uploader_shorts] Instagram Reels: see /final/reels/upload_ready.txt "
          "for copy-paste-ready captions (Option A, free manual upload).")


# ---------------------------------------------------------------------------
# PHASE 2 (commented, needs Meta App Review + IG Business account linked
# to a Facebook Page): Instagram Graph API auto-publish
# ---------------------------------------------------------------------------
# import requests
#
# GRAPH_BASE = "https://graph.facebook.com/v19.0"
#
# def publish_reel_instagram(video_url: str, caption: str) -> str:
#     """video_url must be a publicly reachable URL (e.g. hosted on your own
#     server/S3) - the Graph API pulls the video from there, it can't take a
#     local file upload directly."""
#     ig_user_id = config.INSTAGRAM_BUSINESS_ID
#     token = config.INSTAGRAM_ACCESS_TOKEN
#
#     create = requests.post(f"{GRAPH_BASE}/{ig_user_id}/media", data={
#         "media_type": "REELS",
#         "video_url": video_url,
#         "caption": caption,
#         "access_token": token,
#     }, timeout=60).json()
#     creation_id = create["id"]
#
#     # poll {GRAPH_BASE}/{creation_id}?fields=status_code until FINISHED
#
#     publish = requests.post(f"{GRAPH_BASE}/{ig_user_id}/media_publish", data={
#         "creation_id": creation_id,
#         "access_token": token,
#     }, timeout=60).json()
#     return publish["id"]


def main():
    parser = argparse.ArgumentParser(description="Upload the 3 built Shorts to YouTube")
    parser.add_argument("--publish-now", action="store_true")
    args = parser.parse_args()
    upload_all_shorts(schedule=not args.publish_now)


if __name__ == "__main__":
    main()
