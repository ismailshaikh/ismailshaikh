# -*- coding: utf-8 -*-
"""
Uploads the long video to YouTube via the Data API v3 (FREE).
Reads title/description/tags straight from the parsed script block.
"""
import argparse
import datetime as dt
from pathlib import Path

from googleapiclient.http import MediaFileUpload

import config
from script_parser import get_block, ScriptBlock
from setup_youtube_auth import get_authenticated_service

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def next_publish_at(time_str: str = None) -> str:
    """Returns an RFC3339 UTC timestamp for the next occurrence of
    time_str (HH:MM, IST). Defaults to config.LONG_UPLOAD_TIME_IST."""
    time_str = time_str or config.LONG_UPLOAD_TIME_IST
    hour, minute = map(int, time_str.split(":"))
    now_ist = dt.datetime.now(IST)
    target = now_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now_ist:
        target += dt.timedelta(days=1)
    return target.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def upload_long_video(block: ScriptBlock, video_path: str, thumbnail_path: str = None,
                       publish_at: str = None, schedule: bool = True) -> str:
    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": block.title[:100],
            "description": block.description or "",
            "tags": block.tags[:30],
            "categoryId": config.YOUTUBE_CATEGORY_TRAVEL,
            "defaultLanguage": config.YOUTUBE_DEFAULT_LANGUAGE,
            "defaultAudioLanguage": config.YOUTUBE_DEFAULT_LANGUAGE,
        },
        "status": {
            "selfDeclaredMadeForKids": False,
        },
    }

    if schedule:
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at or next_publish_at()
    else:
        body["status"]["privacyStatus"] = "public"

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[uploader] upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"[uploader] uploaded: https://youtu.be/{video_id}")

    if thumbnail_path and Path(thumbnail_path).exists():
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_path)).execute()
        print("[uploader] thumbnail set")

    return video_id


def main():
    parser = argparse.ArgumentParser(description="Upload the long Fakira Musafir video to YouTube")
    parser.add_argument("--type", default="LONG")
    parser.add_argument("--video", required=True)
    parser.add_argument("--thumbnail", default=None)
    parser.add_argument("--publish-now", action="store_true", help="Skip scheduling, publish immediately")
    args = parser.parse_args()

    block = get_block(args.type)
    upload_long_video(block, args.video, args.thumbnail, schedule=not args.publish_now)


if __name__ == "__main__":
    main()
