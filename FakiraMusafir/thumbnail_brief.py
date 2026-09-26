# -*- coding: utf-8 -*-
"""
Thumbnail BRIEF generator - for when you're designing in Canva Pro
yourself instead of using the auto-PIL thumbnail.py.

Writes a plain-text brief with everything needed to build the
thumbnail/cover in Canva: exact canvas size, headline text, background
image idea, color/style notes, and where to export the finished PNG so
the rest of the pipeline (uploader.py / uploader_shorts.py) picks it up
automatically.

Long video -> 16:9 YouTube thumbnail (1280x720)
Shorts/Reels -> 9:16 cover (1080x1920)

thumbnail.py (PIL auto-generation) still exists and works standalone if
you ever want an instant fallback on a busy day - see --auto-thumbnail
in main.py / shorts_builder.py.
"""
import argparse
import random
from pathlib import Path

import config
from script_parser import get_block, ScriptBlock

ACCENT_COLORS = ["Yellow (#FFD400)", "Red (#FF3B30)", "Cyan (#00E0C6)", "Orange (#FF7A00)"]


def _style_block(accent: str) -> str:
    return (
        "STYLE NOTES:\n"
        f"- Headline: bold sans-serif (Canva: Anton / Poppins ExtraBold / Bebas Neue), ALL CAPS, 2-4 words max\n"
        f"- Text color: White or {accent}, with black outline/shadow for readability\n"
        "- Brand tag \"FAKIRA MUSAFIR\" small, top-left corner, every thumbnail (consistency = recognition)\n"
        "- High contrast background, subject/face in upper two-thirds, text in lower third\n"
        "- Keep it readable at phone size - zoom out to 30% in Canva and check before exporting\n"
    )


def write_long_brief(block: ScriptBlock, out_path=None) -> str:
    """16:9 - YouTube long-video thumbnail, 1280x720."""
    accent = random.choice(ACCENT_COLORS)
    lines = [
        "FAKIRA MUSAFIR - THUMBNAIL BRIEF",
        "=" * 40,
        f"Video type: LONG   |   Canvas: 1280 x 720 px (16:9)",
        "",
        "HEADLINE TEXT (put this big, on the thumbnail):",
        f"  {block.thumbnail_text or block.title.upper()}",
        "",
        "VIDEO TITLE (context only - don't put the full title on the thumbnail):",
        f"  {block.title}",
        "",
        "BACKGROUND IMAGE IDEA (search Canva stock photos, or Canva Magic Media prompt):",
        f"  {block.thumbnail_prompt or 'Indian traveler in the destination from the script'}",
        "",
        _style_block(accent),
        "EXPORT AS (exact path, so uploader.py finds it automatically):",
        f"  {config.THUMBNAILS_DIR / 'long.png'}",
    ]

    out_path = Path(out_path) if out_path else config.THUMBNAILS_DIR / "long_brief.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[thumbnail_brief] saved {out_path}")
    return str(out_path)


def write_vertical_brief(block: ScriptBlock, out_path=None) -> str:
    """9:16 - Shorts/Reels cover, 1080x1920."""
    accent = random.choice(ACCENT_COLORS)
    onscreen = block.onscreen_texts()

    lines = [
        "FAKIRA MUSAFIR - THUMBNAIL/COVER BRIEF",
        "=" * 40,
        f"Video type: {block.type}   |   Canvas: 1080 x 1920 px (9:16)",
        "",
        "HEADLINE TEXT (put this big, center of frame):",
        f"  {block.thumbnail_text or block.title.upper()}",
        "",
        "VIDEO TITLE (context only):",
        f"  {block.title}",
        "",
        "BACKGROUND IMAGE IDEA (search Canva stock photos, or Canva Magic Media prompt):",
        f"  {block.thumbnail_prompt or 'Indian traveler in the destination from the script'}",
        "",
    ]

    if onscreen:
        lines.append("BONUS PUNCHLINE IDEAS (from the script's on-screen text, pick one if it hits harder):")
        for t in onscreen:
            lines.append(f"  - {t}")
        lines.append("")

    lines.extend([
        _style_block(accent),
        "SAFE ZONES (YouTube Shorts / Instagram UI overlaps these - keep text clear of them):",
        "- Top 200px: avoid (profile/follow button overlap on some apps)",
        "- Bottom 250px: avoid (caption/like/comment buttons overlap)",
        "- Keep headline text in the middle 60% of the frame",
        "",
        "EXPORT AS (exact path):",
        f"  {config.THUMBNAILS_DIR / (block.type.lower() + '_cover.png')}",
    ])

    out_path = Path(out_path) if out_path else config.THUMBNAILS_DIR / f"{block.type.lower()}_brief.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[thumbnail_brief] saved {out_path}")
    return str(out_path)


def main():
    parser = argparse.ArgumentParser(description="Generate a Canva thumbnail/cover brief")
    parser.add_argument("--type", default="LONG")
    parser.add_argument("--cover", action="store_true", help="Write the 9:16 vertical brief instead of 16:9")
    args = parser.parse_args()

    block = get_block(args.type)
    if args.cover or args.type.upper() != "LONG":
        write_vertical_brief(block)
    else:
        write_long_brief(block)


if __name__ == "__main__":
    main()
