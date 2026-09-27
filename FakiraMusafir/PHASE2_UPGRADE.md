# PHASE 2 Upgrade Guide - Fakira Musafir

Jab revenue aane lage aur tum premium tools afford kar sako, yeh file
batati hai kaha kya replace karna hai. Har jagah code already commented
hai, tumhe bas uncomment karke API key daalni hai.

## 1. Voice: edge-tts -> ElevenLabs

**File:** `voiceover.py`
**Why upgrade:** ElevenLabs ki Hindi voice zyada natural, emotional aur
human-jaisi lagti hai - edge-tts thoda robotic sunta hai lambe videos me.

Steps:
1. ElevenLabs account banao, Hindi-capable voice clone/pick karo (voice_id copy karo).
2. `.env` me `ELEVENLABS_API_KEY` aur `ELEVENLABS_HINDI_VOICE_ID` daalo.
3. `voiceover.py` me `generate_voiceover_elevenlabs()` function ka comment hatao.
4. `main.py` / `shorts_builder.py` me `generate_voiceover` ki jagah
   `generate_voiceover_elevenlabs` call karo.

Cost: ~$5-99/month depending on characters used.

## 2. Thumbnail background: PIL -> Leonardo AI / Midjourney

**File:** `thumbnail.py`
**Why upgrade:** AI-generated cinematic backgrounds CTR zyada badhate
hai compared to a cropped stock video frame.

Steps:
1. Leonardo AI API key lo, `.env` me `LEONARDO_API_KEY` daalo.
2. `thumbnail.py` me `generate_background_leonardo()` ka comment hatao,
   poll-and-download logic complete karo (function ke andar TODO hai).
3. `generate_thumbnail()` me `_pick_background()` call ki jagah
   `generate_background_leonardo(block)` use karo.
4. Text overlay (PIL) waisa hi rahega - sirf background source badalta hai.

Cost: ~$10-30/month depending on generations.

## 3. Captions: faster-whisper -> Whisper API (OpenAI)

**File:** `builder.py`
**Why upgrade:** Whisper API cloud-based hai, kabhi kabhi Hindi/Hinglish
mixed speech pe thoda better accuracy deta hai aur local CPU/GPU load nahi
karta - useful jab tum daily 4 videos render kar rahe ho.

Steps:
1. `.env` me `OPENAI_API_KEY` daalo.
2. `builder.py` me `transcribe_words()` function replace karo - openai
   python SDK se `client.audio.transcriptions.create(model="whisper-1",
   file=..., response_format="verbose_json", timestamp_granularities=["word"])`
   call karo, response se `words` list bana lo same `(word, start, end)`
   tuple format me jisse baaki caption code untouched chale.
3. Rest of the caption rendering pipeline (PIL-based, no ImageMagick)
   waisa hi rahega.

Cost: $0.006/minute of audio.

## 4. Footage: Pexels/Pixabay -> Storyblocks / Envato Elements

**File:** `downloader.py`
**Why upgrade:** Premium stock libraries me zyada relevant, high quality,
niche-specific travel B-roll milta hai jo free tier me nahi milta.

Steps:
1. Storyblocks/Envato subscription lo, API/download credentials lo.
2. `downloader.py` me `_search_storyblocks()` stub complete karo (HMAC
   signed request - unke developer docs follow karo).
3. `download_broll()` me `_search_pexels(keyword) or _search_pixabay(keyword)`
   ki jagah `_search_storyblocks(keyword)` ko pehli priority do, Pexels/Pixabay
   ko fallback rakh sakte ho.

Cost: ~$15-30/month (Envato Elements) or pay-per-clip (Storyblocks).

## 5. Instagram Reels: Manual -> Graph API auto-publish

**File:** `uploader_shorts.py`
**Why upgrade:** Abhi Instagram upload manual hai (`upload_ready.txt` se
copy-paste). Meta App Review approval milne ke baad, ye fully automate
ho sakta hai.

Steps:
1. Facebook Developer app banao, Instagram Graph API permissions ke liye
   App Review submit karo (`instagram_content_publish` scope).
2. Instagram Business account ko Facebook Page se link karo, Page Access
   Token generate karo.
3. `.env` me `INSTAGRAM_ACCESS_TOKEN` aur `INSTAGRAM_BUSINESS_ID` daalo.
4. Video ko kahi publicly hosted karna padega (S3 / your own server) kyunki
   Graph API local file upload nahi leta - sirf public video_url.
5. `uploader_shorts.py` me `publish_reel_instagram()` ka comment hatao aur
   `upload_all_shorts()` ke end me call add karo.

Cost: Free (Meta doesn't charge), but needs App Review approval time + hosting cost for public video URLs.

---

## Suggested upgrade order (based on ROI)
1. ElevenLabs voice (biggest retention/watch-time impact)
2. Leonardo AI thumbnails (biggest CTR impact)
3. Instagram Graph API (saves your manual time daily)
4. Whisper API captions (marginal accuracy gain)
5. Storyblocks/Envato footage (only once you're scaling to multiple channels)
