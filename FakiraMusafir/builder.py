# -*- coding: utf-8 -*-
"""
Video assembly: MoviePy + FFmpeg (FREE) with faster-whisper (FREE) for
Hindi auto-captions. Builds both the 16:9 long video and the 9:16
vertical (Shorts/Reels) video from the same set of building blocks so
shorts_builder.py and main.py can reuse them.
"""
import glob
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config
from script_parser import ScriptBlock

_WHISPER_MODEL = None


def _font(size: int, bold_path_override=None):
    from thumbnail import FONT_CANDIDATES
    for path in ([bold_path_override] if bold_path_override else []) + FONT_CANDIDATES:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Captions (faster-whisper, FREE)
# ---------------------------------------------------------------------------
def _get_whisper_model():
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        from faster_whisper import WhisperModel
        print(f"[builder] loading faster-whisper '{config.WHISPER_MODEL_SIZE}' model...")
        _WHISPER_MODEL = WhisperModel(config.WHISPER_MODEL_SIZE, compute_type="int8")
    return _WHISPER_MODEL


def transcribe_words(audio_path: str) -> list:
    """Returns [(word, start_sec, end_sec), ...] for Hindi audio."""
    model = _get_whisper_model()
    segments, _info = model.transcribe(
        audio_path, language=config.WHISPER_LANGUAGE, word_timestamps=True
    )
    words = []
    for seg in segments:
        for w in (seg.words or []):
            text = w.word.strip()
            if text:
                words.append((text, w.start, w.end))
    return words


def _chunk_words(words, chunk_size=4):
    for i in range(0, len(words), chunk_size):
        yield words[i:i + chunk_size]


# ---------------------------------------------------------------------------
# Caption rendering -> PIL image -> moviepy ImageClip (no ImageMagick needed)
# ---------------------------------------------------------------------------
def _render_caption_png(text: str, size=(1600, 220), font_size=64, fill="white",
                         stroke="black", stroke_w=6, highlight_word=None,
                         highlight_color="#FFD400"):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _font(font_size)

    words = text.split()
    spans = []
    total_w = 0
    space_w = draw.textlength(" ", font=font)
    for w in words:
        w_width = draw.textlength(w, font=font)
        spans.append((w, w_width))
        total_w += w_width + space_w
    total_w -= space_w

    x = (size[0] - total_w) / 2
    y = size[1] / 2
    for w, w_width in spans:
        color = highlight_color if (highlight_word and w.strip(",.!?") == highlight_word.strip(",.!?")) else fill
        draw.text((x, y), w, font=font, fill=color, stroke_width=stroke_w,
                   stroke_fill=stroke, anchor="lm")
        x += w_width + space_w
    return np.array(img)


def caption_clips_long(words, video_size):
    """Bottom-center caption bar, white text + black stroke, ~4 words at a
    time, CarryMinati-style burn-in captions for the long video."""
    from moviepy.editor import ImageClip
    clips = []
    for chunk in _chunk_words(words, chunk_size=5):
        if not chunk:
            continue
        text = " ".join(w for w, _, _ in chunk)
        start, end = chunk[0][1], chunk[-1][2]
        duration = max(end - start, 0.3)
        arr = _render_caption_png(text, size=(video_size[0] - 100, 200), font_size=58)
        clip = (ImageClip(arr)
                .set_start(start)
                .set_duration(duration)
                .set_position(("center", video_size[1] - 260)))
        clips.append(clip)
    return clips


def caption_clips_vertical(words, video_size):
    """Word-by-word pop-style captions for Shorts/Reels: shows a small
    rolling window of words, current word highlighted yellow + bounced."""
    from moviepy.editor import ImageClip
    clips = []
    window = 3
    for i, (word, start, end) in enumerate(words):
        lo = max(0, i - 1)
        hi = min(len(words), lo + window)
        chunk = words[lo:hi]
        text = " ".join(w for w, _, _ in chunk)
        duration = max(end - start, 0.12)
        arr = _render_caption_png(text, size=(video_size[0] - 80, 260), font_size=78,
                                   highlight_word=word)
        clip = (ImageClip(arr)
                .set_start(start)
                .set_duration(duration)
                .set_position(("center", int(video_size[1] * 0.62))))
        # quick pop/bounce-in over the first 0.12s
        clip = clip.resize(lambda t, d=duration: 1.15 - 0.15 * min(t / 0.12, 1.0))
        clips.append(clip)
    return clips


def onscreen_text_clip(text: str, video_size, start=0.0, duration=2.0):
    from moviepy.editor import ImageClip
    arr = _render_caption_png(text.upper(), size=(video_size[0] - 60, 200), font_size=72,
                               fill="#FFD400", stroke="black", stroke_w=8)
    return (ImageClip(arr)
            .set_start(start)
            .set_duration(duration)
            .set_position(("center", int(video_size[1] * 0.12))))


# ---------------------------------------------------------------------------
# Ken Burns zoom
# ---------------------------------------------------------------------------
def ken_burns(clip, zoom_per_sec=0.04):
    return clip.resize(lambda t: 1 + zoom_per_sec * t)


# ---------------------------------------------------------------------------
# Long video (16:9)
# ---------------------------------------------------------------------------
def build_long_video(block: ScriptBlock, voice_path: str, footage_dir=None,
                      music_path=None, out_path=None) -> str:
    from moviepy.editor import (VideoFileClip, AudioFileClip, CompositeVideoClip,
                                 CompositeAudioClip, concatenate_videoclips, vfx)

    footage_dir = Path(footage_dir) if footage_dir else (config.FOOTAGE_DIR / block.type.lower())
    clip_paths = sorted(glob.glob(str(footage_dir / "*.mp4")))
    if not clip_paths:
        raise FileNotFoundError(f"No footage found in {footage_dir}. Run downloader.py first.")

    voiceover = AudioFileClip(voice_path)
    target_duration = voiceover.duration
    w, h = config.LONG_RESOLUTION

    per_clip = config.CLIP_SECONDS
    needed = max(int(target_duration // per_clip) + 1, 1)
    clip_cycle = (clip_paths * (needed // len(clip_paths) + 1))[:needed]

    segments = []
    for path in clip_cycle:
        c = (VideoFileClip(path)
             .without_audio()
             .subclip(0, min(per_clip, VideoFileClip(path).duration)))
        c = c.resize(height=h).crop(x_center=c.w / 2 if c.w >= w else None, width=min(c.w, w), height=h)
        if c.w < w:
            c = c.resize(width=w)
        c = c.crossfadein(0.4)
        c = ken_burns(c)
        segments.append(c)

    video = concatenate_videoclips(segments, method="compose", padding=-0.4).subclip(0, target_duration)
    video = video.set_audio(None)

    words = transcribe_words(voice_path)
    captions = caption_clips_long(words, (w, h))

    layers = [video] + captions
    final = CompositeVideoClip(layers, size=(w, h)).set_duration(target_duration)

    audio_tracks = [voiceover]
    if music_path and Path(music_path).exists():
        music = AudioFileClip(music_path).fx(vfx.loop, duration=target_duration).volumex(0.10)
        audio_tracks.append(music)
    final = final.set_audio(CompositeAudioClip(audio_tracks))

    out_path = Path(out_path) if out_path else config.FINAL_LONG_DIR / f"{block.type.lower()}_16x9.mp4"
    final.write_videofile(str(out_path), fps=config.LONG_FPS, codec="libx264",
                           audio_codec="aac", threads=4, preset="medium")
    print(f"[builder] long video -> {out_path}")
    return str(out_path)


# ---------------------------------------------------------------------------
# Vertical video (9:16) - Shorts / Reels
# ---------------------------------------------------------------------------
def build_vertical_video(block: ScriptBlock, voice_path: str, footage_dir=None,
                          music_path=None, out_path=None) -> str:
    from moviepy.editor import (VideoFileClip, AudioFileClip, CompositeVideoClip,
                                 CompositeAudioClip, concatenate_videoclips, vfx)

    footage_dir = Path(footage_dir) if footage_dir else (config.FOOTAGE_DIR / block.type.lower())
    clip_paths = sorted(glob.glob(str(footage_dir / "*.mp4")))
    if not clip_paths:
        raise FileNotFoundError(f"No footage found in {footage_dir}. Run downloader.py first.")

    voiceover = AudioFileClip(voice_path)
    target_duration = min(voiceover.duration, config.SHORT_MAX_SECONDS)
    w, h = config.VERTICAL_RESOLUTION

    per_clip = config.CLIP_SECONDS
    needed = max(int(target_duration // per_clip) + 1, 1)
    clip_cycle = (clip_paths * (needed // len(clip_paths) + 1))[:needed]

    segments = []
    for path in clip_cycle:
        src = VideoFileClip(path).without_audio()
        c = src.subclip(0, min(per_clip, src.duration))
        # center crop to 9:16
        scale = max(w / c.w, h / c.h)
        c = c.resize(scale)
        c = c.crop(x_center=c.w / 2, y_center=c.h / 2, width=w, height=h)
        c = ken_burns(c, zoom_per_sec=0.05)
        c = c.crossfadein(0.3)
        segments.append(c)

    video = concatenate_videoclips(segments, method="compose", padding=-0.3).subclip(0, target_duration)
    video = video.set_audio(None)

    words = transcribe_words(voice_path)
    words = [wd for wd in words if wd[1] <= target_duration]
    captions = caption_clips_vertical(words, (w, h))

    onscreen_clips = []
    for i, text in enumerate(block.onscreen_texts()):
        start = min(i * 3.0, max(target_duration - 2.0, 0))
        onscreen_clips.append(onscreen_text_clip(text, (w, h), start=start, duration=2.0))

    layers = [video] + captions + onscreen_clips
    final = CompositeVideoClip(layers, size=(w, h)).set_duration(target_duration)

    audio_tracks = [voiceover.subclip(0, target_duration)]
    if music_path and Path(music_path).exists():
        music = AudioFileClip(music_path).fx(vfx.loop, duration=target_duration).volumex(0.15)
        audio_tracks.append(music)
    final = final.set_audio(CompositeAudioClip(audio_tracks))

    out_path = Path(out_path) if out_path else config.FINAL_SHORTS_DIR / f"{block.type.lower()}_9x16.mp4"
    final.write_videofile(str(out_path), fps=config.VERTICAL_FPS, codec="libx264",
                           audio_codec="aac", threads=4, preset="medium")
    print(f"[builder] vertical video -> {out_path}")
    return str(out_path)


def pick_music(music_dir=None):
    music_dir = Path(music_dir) if music_dir else config.MUSIC_DIR
    tracks = glob.glob(str(music_dir / "*.mp3")) + glob.glob(str(music_dir / "*.wav"))
    return random.choice(tracks) if tracks else None
