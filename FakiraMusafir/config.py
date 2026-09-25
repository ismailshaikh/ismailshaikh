# -*- coding: utf-8 -*-
"""
Fakira Musafir - shared config & paths.
PHASE 1: everything here is FREE tooling. See PHASE2_UPGRADE.md for
the premium swaps this file is already structured to accept.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent

# ---- folders ----
SCRIPTS_DIR = ROOT / "scripts"
PROMPTS_DIR = ROOT / "prompts"
VOICES_DIR = ROOT / "voices"
FOOTAGE_DIR = ROOT / "footage"
FINAL_LONG_DIR = ROOT / "final" / "long"
FINAL_SHORTS_DIR = ROOT / "final" / "shorts"
FINAL_REELS_DIR = ROOT / "final" / "reels"
THUMBNAILS_DIR = ROOT / "thumbnails"
MUSIC_DIR = ROOT / "assets" / "music"
CREDENTIALS_DIR = ROOT / ".credentials"

MANUAL_INPUT_FILE = SCRIPTS_DIR / "manual_input.txt"

for d in (SCRIPTS_DIR, PROMPTS_DIR, VOICES_DIR, FOOTAGE_DIR, FINAL_LONG_DIR,
          FINAL_SHORTS_DIR, FINAL_REELS_DIR, THUMBNAILS_DIR, MUSIC_DIR,
          CREDENTIALS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ---- API keys (PHASE 1 free tier) ----
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")

# ---- PHASE 2 keys (unused until you upgrade, see PHASE2_UPGRADE.md) ----
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_HINDI_VOICE_ID = os.getenv("ELEVENLABS_HINDI_VOICE_ID", "")
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # for Whisper API upgrade
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID", "")

# ---- YouTube ----
YOUTUBE_CLIENT_SECRETS_FILE = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", str(CREDENTIALS_DIR / "client_secret.json"))
YOUTUBE_TOKEN_FILE = os.getenv("YOUTUBE_TOKEN_FILE", str(CREDENTIALS_DIR / "token.json"))
YOUTUBE_CATEGORY_TRAVEL = "19"
YOUTUBE_DEFAULT_LANGUAGE = "hi"

# Simple API key (no OAuth) for read-only Data API v3 calls (search/videos.list).
# Google Cloud Console -> APIs & Services -> Credentials -> Create API Key ->
# restrict it to "YouTube Data API v3". Free, separate from the OAuth client
# used by setup_youtube_auth.py/uploader.py.
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# ---- trend_finder.py (all FREE sources) ----
TREND_SEED_KEYWORDS = [
    "budget travel india",
    "visa free countries for indians",
    "cheap countries to visit from india",
    "thailand trip budget",
    "bali trip budget",
    "vietnam backpacking india",
    "dubai budget trip",
    "nepal trip budget",
    "sri lanka trip budget",
    "travel scam india",
    "hidden places india",
    "solo travel india",
]
REDDIT_SUBREDDITS = ["IndiaTravel", "india", "travel", "backpacking", "solotravel"]
TREND_OUTPUT_FILE = ROOT / "trending_topics.csv"
TREND_DEDUP_THRESHOLD = 0.55  # token-overlap ratio above which two topics are treated as duplicates

# ---- voices (edge-tts, FREE, no API key) ----
VOICE_LONG_MALE = "hi-IN-MadhurNeural"
VOICE_SHORT_FEMALE = "hi-IN-SwaraNeural"
TTS_RATE_LONG = "-5%"
TTS_RATE_SHORT = "-2%"

# ---- video specs ----
LONG_RESOLUTION = (1920, 1080)
VERTICAL_RESOLUTION = (1080, 1920)
LONG_FPS = 30
VERTICAL_FPS = 30
CLIP_SECONDS = 5
LONG_CLIP_COUNT = (25, 30)
SHORT_CLIP_COUNT = (6, 8)
SHORT_MAX_SECONDS = 40

# ---- captions ----
WHISPER_MODEL_SIZE = "small"
WHISPER_LANGUAGE = "hi"

# ---- scheduling (IST) ----
LONG_UPLOAD_TIME_IST = "18:00"
SHORTS_UPLOAD_TIMES_IST = ["11:00", "15:00", "20:00"]
REELS_UPLOAD_TIMES_IST = ["12:00", "19:00", "21:00"]

FALLBACK_BROLL_KEYWORDS = [
    "india travel", "backpacker", "airport", "passport", "mountains",
    "beach sunset", "street food", "train journey", "city skyline",
    "temple", "market street", "hiking trail", "waterfall", "night market",
    "budget hostel", "motorbike ride", "rice fields", "tropical island",
    "tuk tuk", "local bazaar",
]
