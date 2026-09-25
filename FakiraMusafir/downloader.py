# -*- coding: utf-8 -*-
"""
Auto-downloads B-ROLL footage for [B-ROLL: keyword] tags in a script.

PHASE 1 (FREE): Pexels API + Pixabay API, both have free tiers.
PHASE 2 (PREMIUM): swap to Storyblocks / Envato Elements - see the
commented function at the bottom and PHASE2_UPGRADE.md.
"""
import argparse
import time
from pathlib import Path

import requests

import config
from script_parser import get_block, ScriptBlock

PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"
PIXABAY_SEARCH_URL = "https://pixabay.com/api/videos/"


def _search_pexels(keyword: str, per_page: int = 3):
    if not config.PEXELS_API_KEY:
        return []
    headers = {"Authorization": config.PEXELS_API_KEY}
    params = {"query": keyword, "per_page": per_page, "orientation": "landscape"}
    try:
        r = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        print(f"[downloader] Pexels search failed for '{keyword}': {e}")
        return []

    urls = []
    for video in data.get("videos", []):
        files = sorted(video.get("video_files", []),
                        key=lambda f: f.get("width", 0), reverse=True)
        hd = next((f for f in files if 720 <= f.get("width", 0) <= 1920), None)
        if hd:
            urls.append(hd["link"])
    return urls


def _search_pixabay(keyword: str, per_page: int = 3):
    if not config.PIXABAY_API_KEY:
        return []
    params = {
        "key": config.PIXABAY_API_KEY,
        "q": keyword,
        "per_page": max(per_page, 3),
    }
    try:
        r = requests.get(PIXABAY_SEARCH_URL, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        print(f"[downloader] Pixabay search failed for '{keyword}': {e}")
        return []

    urls = []
    for hit in data.get("hits", []):
        videos = hit.get("videos", {})
        best = videos.get("medium") or videos.get("small") or videos.get("large")
        if best and best.get("url"):
            urls.append(best["url"])
    return urls


def _download(url: str, out_path: Path) -> bool:
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    f.write(chunk)
        return True
    except requests.RequestException as e:
        print(f"[downloader] download failed for {url}: {e}")
        return False


def download_broll(block: ScriptBlock, out_dir=None, target_count: int = None) -> list:
    """Downloads clips for every [B-ROLL: keyword] in the block's script.
    Falls back to config.FALLBACK_BROLL_KEYWORDS if a keyword yields
    nothing on either API (or no API keys are configured)."""
    keywords = block.broll_keywords() or list(config.FALLBACK_BROLL_KEYWORDS)
    out_dir = Path(out_dir) if out_dir else (config.FOOTAGE_DIR / block.type.lower())
    out_dir.mkdir(parents=True, exist_ok=True)

    is_long = block.type.upper() == "LONG"
    default_target = config.LONG_CLIP_COUNT[1] if is_long else config.SHORT_CLIP_COUNT[1]
    target_count = target_count or default_target

    downloaded = []
    fallback_cycle = list(config.FALLBACK_BROLL_KEYWORDS)
    fi = 0

    for i, keyword in enumerate(keywords):
        if len(downloaded) >= target_count:
            break

        urls = _search_pexels(keyword) or _search_pixabay(keyword)
        if not urls:
            print(f"[downloader] no results for '{keyword}', using fallback keyword")
            fb_keyword = fallback_cycle[fi % len(fallback_cycle)]
            fi += 1
            urls = _search_pexels(fb_keyword) or _search_pixabay(fb_keyword)

        if not urls:
            print(f"[downloader] fallback also empty (check API keys / network), skipping slot {i}")
            continue

        url = urls[0]
        ext = ".mp4"
        out_path = out_dir / f"{i:02d}_{_safe_name(keyword)}{ext}"
        if _download(url, out_path):
            downloaded.append(str(out_path))
            print(f"[downloader] saved {out_path.name}")
        time.sleep(0.3)  # be gentle on free-tier rate limits

    # top up with fallback keywords if we're short of target_count
    while len(downloaded) < target_count:
        fb_keyword = fallback_cycle[fi % len(fallback_cycle)]
        fi += 1
        urls = _search_pexels(fb_keyword) or _search_pixabay(fb_keyword)
        if not urls:
            print("[downloader] no more fallback results available, stopping")
            break
        url = urls[0]
        out_path = out_dir / f"{len(downloaded):02d}_{_safe_name(fb_keyword)}.mp4"
        if _download(url, out_path):
            downloaded.append(str(out_path))
        time.sleep(0.3)

    print(f"[downloader] {block.type}: {len(downloaded)} clips in {out_dir}")
    return downloaded


def _safe_name(keyword: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in keyword.lower())[:30] or "clip"


# ---------------------------------------------------------------------------
# PHASE 2 (commented, ready to switch): Storyblocks / Envato Elements
# ---------------------------------------------------------------------------
# def _search_storyblocks(keyword: str):
#     # Storyblocks API needs HMAC-signed requests with STORYBLOCKS_PUBLIC_KEY
#     # and STORYBLOCKS_PRIVATE_KEY. Docs: https://developer.storyblocks.com/
#     raise NotImplementedError("Wire up Storyblocks signed search here in Phase 2")


def main():
    parser = argparse.ArgumentParser(description="Download B-ROLL clips for a script block")
    parser.add_argument("--type", default="LONG", help="LONG, SHORT1, SHORT2, SHORT3")
    parser.add_argument("--count", type=int, default=None)
    args = parser.parse_args()

    block = get_block(args.type)
    download_broll(block, target_count=args.count)


if __name__ == "__main__":
    main()
