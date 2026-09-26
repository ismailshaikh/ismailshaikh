# -*- coding: utf-8 -*-
"""
Thumbnail + Reel cover generator.

PHASE 1 (FREE): Pillow (PIL) draws bold Hindi/English text over a
background frame grabbed from the downloaded footage.
PHASE 2 (PREMIUM): swap the background source to Leonardo AI /
Midjourney using thumbnail_prompt - see the commented function below
and PHASE2_UPGRADE.md.
"""
import argparse
import glob
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import config
from script_parser import get_block, ScriptBlock

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
]

ACCENT_COLORS = ["#FFD400", "#FF3B30", "#00E0C6", "#FF7A00"]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _pick_background(footage_dir: Path, size) -> Image.Image:
    """Grabs a frame from a downloaded clip if ffmpeg/moviepy is available,
    otherwise falls back to a solid gradient so the pipeline never breaks."""
    clips = sorted(glob.glob(str(footage_dir / "*.mp4")))
    if clips:
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(random.choice(clips))
            t = min(1.0, clip.duration / 2)
            frame = clip.get_frame(t)
            clip.close()
            img = Image.fromarray(frame).convert("RGB").resize(size)
            return img
        except Exception as e:
            print(f"[thumbnail] could not grab frame from footage ({e}), using gradient bg")

    return _gradient_background(size)


def _gradient_background(size) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size, "#0f172a")
    top = (15, 23, 42)
    bottom = (30, 64, 90)
    for y in range(h):
        t = y / h
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        ImageDraw.Draw(img).line([(0, y), (w, y)], fill=(r, g, b))
    return img


def _darken_for_text(img: Image.Image, box) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle(box, fill=(0, 0, 0, 130))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def _draw_bold_text(draw: ImageDraw.ImageDraw, xy, text, font, fill, stroke_fill="black", stroke_width=8):
    draw.text(xy, text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill,
               anchor="mm")


def generate_thumbnail(block: ScriptBlock, out_path=None, size=(1280, 720)) -> str:
    footage_dir = config.FOOTAGE_DIR / block.type.lower()
    bg = _pick_background(footage_dir, size)
    bg = _darken_for_text(bg, (0, int(size[1] * 0.55), size[0], size[1]))

    draw = ImageDraw.Draw(bg)
    text = (block.thumbnail_text or block.title or "FAKIRA MUSAFIR").upper()
    accent = random.choice(ACCENT_COLORS)

    font_size = 130 if len(text) <= 14 else 90
    font = _load_font(font_size)

    lines = _wrap_text(text, font, draw, size[0] - 120)
    total_h = len(lines) * (font_size + 20)
    y = size[1] - total_h - 60
    for line in lines:
        _draw_bold_text(draw, (size[0] // 2, y + font_size // 2), line, font, accent)
        y += font_size + 20

    brand_font = _load_font(40)
    draw.text((30, 30), "FAKIRA MUSAFIR", font=brand_font, fill="white",
               stroke_width=4, stroke_fill="black")

    out_path = Path(out_path) if out_path else config.THUMBNAILS_DIR / f"{block.type.lower()}.png"
    bg.save(out_path, quality=95)
    print(f"[thumbnail] saved {out_path}")
    return str(out_path)


def generate_reel_cover(block: ScriptBlock, out_path=None, size=(1080, 1920)) -> str:
    footage_dir = config.FOOTAGE_DIR / block.type.lower()
    bg = _pick_background(footage_dir, size)
    bg = bg.filter(ImageFilter.GaussianBlur(1))
    bg = _darken_for_text(bg, (0, int(size[1] * 0.35), size[0], int(size[1] * 0.65)))

    draw = ImageDraw.Draw(bg)
    text = (block.thumbnail_text or block.title or "FAKIRA MUSAFIR").upper()
    font = _load_font(110)
    lines = _wrap_text(text, font, draw, size[0] - 100)
    total_h = len(lines) * 140
    y = size[1] // 2 - total_h // 2
    for line in lines:
        _draw_bold_text(draw, (size[0] // 2, y + 70), line, font, "#FFD400")
        y += 140

    out_path = Path(out_path) if out_path else config.THUMBNAILS_DIR / f"{block.type.lower()}_cover.png"
    bg.save(out_path, quality=95)
    print(f"[thumbnail] saved reel cover {out_path}")
    return str(out_path)


def _wrap_text(text, font, draw, max_width):
    words = text.split()
    lines, current = [], ""
    for w in words:
        trial = f"{current} {w}".strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# PHASE 2 (commented, ready to switch): Leonardo AI thumbnail background
# ---------------------------------------------------------------------------
# def generate_background_leonardo(block: ScriptBlock, size=(1280, 720)) -> Image.Image:
#     import requests, io
#     headers = {"Authorization": f"Bearer {config.LEONARDO_API_KEY}"}
#     payload = {
#         "prompt": block.thumbnail_prompt,
#         "width": size[0], "height": size[1],
#         "num_images": 1, "modelId": "aa77f04e-3eec-4034-9c07-d0f619684628",
#     }
#     r = requests.post("https://cloud.leonardo.ai/api/rest/v1/generations",
#                        headers=headers, json=payload, timeout=60)
#     r.raise_for_status()
#     generation_id = r.json()["sdGenerationJob"]["generationId"]
#     # then poll GET /generations/{id} until status == COMPLETE, download the
#     # returned image URL, and Image.open(io.BytesIO(resp.content))
#     raise NotImplementedError("Poll + download logic goes here in Phase 2")


def main():
    parser = argparse.ArgumentParser(description="Generate thumbnail / reel cover")
    parser.add_argument("--type", default="LONG")
    parser.add_argument("--cover", action="store_true", help="Generate a 9:16 reel cover instead")
    args = parser.parse_args()

    block = get_block(args.type)
    if args.cover:
        generate_reel_cover(block)
    else:
        generate_thumbnail(block)


if __name__ == "__main__":
    main()
