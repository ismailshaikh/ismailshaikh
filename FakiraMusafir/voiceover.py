# -*- coding: utf-8 -*-
"""
Hindi voiceover generation.

PHASE 1 (FREE): Microsoft edge-tts, no API key needed.
PHASE 2 (PREMIUM): swap to ElevenLabs Hindi voice - see the commented
function at the bottom and PHASE2_UPGRADE.md.
"""
import argparse
import asyncio

import edge_tts

import config
from script_parser import get_block, ScriptBlock

LONG_TYPES = {"LONG"}


def voice_and_rate_for(type_name: str, voice_override: str = None) -> tuple:
    if voice_override:
        voice = voice_override
    elif type_name.upper() in LONG_TYPES:
        voice = config.VOICE_LONG_MALE
    else:
        voice = config.VOICE_SHORT_FEMALE
    rate = config.TTS_RATE_LONG if type_name.upper() in LONG_TYPES else config.TTS_RATE_SHORT
    return voice, rate


async def _synthesize(text: str, voice: str, rate: str, out_path):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(str(out_path))


def generate_voiceover(block: ScriptBlock, voice: str = None, rate: str = None, out_dir=None) -> str:
    """Reads the cleaned script text (b-roll/on-screen tags stripped) and
    writes an mp3 to /voices/<type>.mp3. Returns the output path."""
    text = block.clean_for_tts()
    if not text:
        raise ValueError(f"No spoken text found for block {block.type} - check manual_input.txt")

    resolved_voice, resolved_rate = voice_and_rate_for(block.type, voice)
    rate = rate or resolved_rate
    out_dir = out_dir or config.VOICES_DIR
    out_path = out_dir / f"{block.type.lower()}.mp3"

    asyncio.run(_synthesize(text, resolved_voice, rate, out_path))
    print(f"[voiceover] {block.type}: {resolved_voice} rate={rate} -> {out_path}")
    return str(out_path)


# ---------------------------------------------------------------------------
# PHASE 2 (commented, ready to switch): ElevenLabs Hindi voiceover
# ---------------------------------------------------------------------------
# import requests
#
# def generate_voiceover_elevenlabs(block: ScriptBlock, out_dir=None) -> str:
#     text = block.clean_for_tts()
#     out_dir = out_dir or config.VOICES_DIR
#     out_path = out_dir / f"{block.type.lower()}.mp3"
#     url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_HINDI_VOICE_ID}"
#     headers = {"xi-api-key": config.ELEVENLABS_API_KEY, "Content-Type": "application/json"}
#     payload = {
#         "text": text,
#         "model_id": "eleven_multilingual_v2",
#         "voice_settings": {"stability": 0.45, "similarity_boost": 0.8},
#     }
#     resp = requests.post(url, headers=headers, json=payload, timeout=120)
#     resp.raise_for_status()
#     out_path.write_bytes(resp.content)
#     return str(out_path)


def main():
    parser = argparse.ArgumentParser(description="Generate Hindi voiceover from manual_input.txt")
    parser.add_argument("--type", default="LONG", help="LONG, SHORT1, SHORT2, SHORT3")
    parser.add_argument("--voice", default=None, help="Override voice, e.g. hi-IN-SwaraNeural")
    parser.add_argument("--rate", default=None, help="Override speaking rate, e.g. -5%%")
    args = parser.parse_args()

    block = get_block(args.type)
    generate_voiceover(block, voice=args.voice, rate=args.rate)


if __name__ == "__main__":
    main()
