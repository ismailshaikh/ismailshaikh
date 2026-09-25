# Fakira Musafir - YouTube Automation System

Hindi/Hinglish faceless travel channel automation. **Phase 1 = 100% FREE**
tools, no monthly cost. Phase 2 upgrade path already wired in (see
`PHASE2_UPGRADE.md`).

Daily output target: **1 long video (8-12 min) + 3 Shorts + 3 Reels**.

---

## Folder Structure

```
FakiraMusafir/
  scripts/manual_input.txt         <- Claude Pro se copy-paste karke script daalo yaha
  prompts/
    claude_pro_script_prompt.txt   <- long video script ke liye Claude Pro prompt
    shorts_prompt.txt              <- standalone short ke liye prompt
    shorts_factory_prompt.txt      <- long video se 3 shorts nikalne ka prompt
  voices/                          <- generated mp3 voiceovers
  footage/                         <- downloaded Pexels/Pixabay clips
  final/
    long/                          <- finished 16:9 long video
    shorts/                        <- finished 9:16 Shorts + metadata.json
    reels/                         <- copy of shorts + cover images + upload_ready.txt
  thumbnails/                      <- generated thumbnails + reel covers
  assets/music/                    <- put free background music mp3s here
  .credentials/                    <- YouTube OAuth client_secret.json + token.json (gitignored)
  config.py, script_parser.py      <- shared config & manual_input.txt parser
  voiceover.py, downloader.py, builder.py, thumbnail.py
  uploader.py, setup_youtube_auth.py
  shorts_builder.py, caption_generator.py, uploader_shorts.py
  main.py                          <- orchestrator
  topics.csv                       <- 100 long-video topic ideas
  topics_shorts.csv                <- 100 shorts-only topic ideas
  viral_hooks.txt                  <- 50 reusable viral hooks
```

---

## One-time setup

```bash
cd FakiraMusafir
pip install -r requirements.txt
cp .env.example .env
```

1. **Pexels API key** (free): https://www.pexels.com/api/ -> paste in `.env`
2. **Pixabay API key** (free): https://pixabay.com/api/docs/ -> paste in `.env`
3. **YouTube OAuth**: Google Cloud Console me project banao, YouTube Data
   API v3 enable karo, OAuth Desktop client banao, `client_secret.json`
   ko `.credentials/` me daalo, phir:
   ```bash
   python setup_youtube_auth.py
   ```
   Browser khulega, login karo, done.
4. `assets/music/` me 2-3 free background music mp3 daal do (YouTube
   Audio Library / Pixabay Music se le sakte ho, dono free hain).
5. faster-whisper pehli baar chalega toh Hindi "small" model download
   karega (~500MB) - ek baar hi hota hai.
6. FFmpeg system me installed hona chahiye (`ffmpeg -version` check karo).

---

## Daily workflow - LONG VIDEO

1. `topics.csv` se aaj ka topic uthao.
2. `prompts/claude_pro_script_prompt.txt` open karo, `{TOPIC}` ko apne
   topic se replace karo, poora prompt Claude Pro me paste karo.
3. Claude Pro ka jo output aaye, use **as-is** copy karke
   `scripts/manual_input.txt` me paste karo (`===TYPE: LONG===` block ke
   andar - format file me already sample bhara hai, waisa hi rakhna).
4. Run:
   ```bash
   python main.py --mode long
   ```
   Yeh voiceover banayega, footage download karega, video edit karega
   (captions + music + Ken Burns), thumbnail banayega.
5. Video check karo `final/long/long_16x9.mp4` me. Agar sahi lage:
   ```bash
   python main.py --mode long --upload
   ```
   Yeh YouTube pe 6 PM IST ke liye schedule kar dega.

## Daily workflow - SHORTS + REELS

1. Long video ka topic + 1-2 line summary lo.
2. `prompts/shorts_factory_prompt.txt` open karo, `{TOPIC}` aur
   `{SUMMARY}` fill karo, Claude Pro me paste karo.
3. Output ko `scripts/manual_input.txt` me `SHORT1`/`SHORT2`/`SHORT3`
   blocks ke andar paste karo (long block ke baad, same file me).
4. Run:
   ```bash
   python main.py --mode shorts-only
   ```
   Ya agar long bhi same din bana rahe ho:
   ```bash
   python main.py --mode long+shorts
   ```
5. Output:
   - `final/shorts/short1_9x16.mp4`, `short2_9x16.mp4`, `short3_9x16.mp4`
   - `final/shorts/metadata.json` (titles, descriptions, hashtags)
   - `final/reels/` - same videos + cover images + `upload_ready.txt`
     (Instagram caption copy-paste ready)
6. Upload Shorts to YouTube:
   ```bash
   python main.py --mode shorts-only --upload
   ```
   (schedules at 11 AM / 3 PM / 8 PM IST)
7. Upload Reels to Instagram **manually** (Phase 1 - free): open
   `final/reels/upload_ready.txt`, copy the caption, upload the video +
   cover from the Instagram app. Phase 2 me yeh bhi automate ho jayega
   (`PHASE2_UPGRADE.md` dekho).

---

## `manual_input.txt` format (important)

Har script block iss shape me hona chahiye - Claude Pro ke prompts
already isi format me output dete hai:

```
===TYPE: LONG===
TITLE:
1. Title option 1
2. Title option 2
3. Title option 3

DESCRIPTION:
Hindi description...

TAGS:
tag1, tag2, tag3

THUMBNAIL_TEXT:
2-3 words

THUMBNAIL_PROMPT:
English image prompt

SCRIPT:
Script text with [B-ROLL: keyword] and [ON-SCREEN TEXT: word] tags
===END===
```

Multiple blocks (`LONG`, `SHORT1`, `SHORT2`, `SHORT3`) same file me,
ek ke baad ek, rakh sakte ho.

---

## Upload schedule (IST)

| Content        | Time(s)                  |
|-----------------|---------------------------|
| Long video      | 6:00 PM                   |
| YouTube Shorts  | 11:00 AM, 3:00 PM, 8:00 PM |
| Instagram Reels | 12:00 PM, 7:00 PM, 9:00 PM |

---

## Individual scripts (run standalone for debugging)

```bash
python voiceover.py --type LONG
python downloader.py --type LONG
python thumbnail.py --type LONG
python uploader.py --type LONG --video final/long/long_16x9.mp4 --thumbnail thumbnails/long.png

python shorts_builder.py --long-video-url https://youtu.be/xxxx
python caption_generator.py --long-video-url https://youtu.be/xxxx
python uploader_shorts.py
```

---

## Phase 1 vs Phase 2

Everything above is **Phase 1 - completely free**. When the channel
starts earning, read `PHASE2_UPGRADE.md` for the exact swaps
(ElevenLabs voice, Leonardo AI thumbnails, Whisper API captions,
Storyblocks footage, Instagram Graph API auto-publish) - code stubs
for all of them are already written and commented in each file.

## Notes

- All Hindi text is UTF-8 everywhere (`scripts/manual_input.txt`,
  generated descriptions, `topics.csv`, `viral_hooks.txt`) - no
  encoding issues on Windows/Linux/Mac.
- Sample test data for topic **"Thailand Trip Under 30000"** is already
  filled into `scripts/manual_input.txt` (LONG + SHORT1/2/3) so you can
  run the whole pipeline once end-to-end before plugging in your own
  Claude Pro output.
