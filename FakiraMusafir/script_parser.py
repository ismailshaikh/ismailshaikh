# -*- coding: utf-8 -*-
"""
Parses /scripts/manual_input.txt (the text you paste from Claude Pro)
into structured ScriptBlock objects used by every other module.

FORMAT (paste exactly this shape - the prompt files ask Claude Pro to
output it):

===TYPE: LONG===
TITLE:
1. Title option one
2. Title option two
3. Title option three

DESCRIPTION:
Hindi description here...

TAGS:
tag1, tag2, tag3

THUMBNAIL_TEXT:
2-3 word Hinglish text

THUMBNAIL_PROMPT:
English image prompt for background art

SCRIPT:
Actual voiceover script with [B-ROLL: keyword] tags sprinkled in
and optional [ON-SCREEN TEXT: word] tags for shorts.
===END===

You can paste multiple blocks (LONG, SHORT1, SHORT2, SHORT3) in the
same file - one after another. Re-running any script just re-reads
whichever TYPE block it needs.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List

from config import MANUAL_INPUT_FILE

BLOCK_RE = re.compile(r"===TYPE:\s*(\w+)\s*===(.*?)===END===", re.DOTALL | re.IGNORECASE)
BROLL_RE = re.compile(r"\[B-ROLL:\s*(.*?)\]", re.IGNORECASE)
ONSCREEN_RE = re.compile(r"\[ON-SCREEN TEXT:\s*(.*?)\]", re.IGNORECASE)
BRACKET_TAG_RE = re.compile(r"\[[^\]]*\]")


@dataclass
class ScriptBlock:
    type: str
    title_options: List[str] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    thumbnail_text: str = ""
    thumbnail_prompt: str = ""
    raw_script: str = ""

    @property
    def title(self) -> str:
        return self.title_options[0] if self.title_options else f"Fakira Musafir - {self.type}"

    def broll_keywords(self) -> List[str]:
        return [kw.strip() for kw in BROLL_RE.findall(self.raw_script) if kw.strip()]

    def onscreen_texts(self) -> List[str]:
        return [t.strip() for t in ONSCREEN_RE.findall(self.raw_script) if t.strip()]

    def clean_for_tts(self) -> str:
        """Strip every [..] tag, leaving only what should be spoken."""
        text = BRACKET_TAG_RE.sub("", self.raw_script)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def _parse_section(body: str, name: str) -> str:
    pattern = re.compile(
        rf"{name}:\s*\n(.*?)(?=\n[A-Z_]+:\s*\n|\Z)", re.DOTALL
    )
    m = pattern.search(body)
    return m.group(1).strip() if m else ""


def parse_manual_input(path=None) -> Dict[str, ScriptBlock]:
    path = path or MANUAL_INPUT_FILE
    text = path.read_text(encoding="utf-8")
    blocks: Dict[str, ScriptBlock] = {}

    for match in BLOCK_RE.finditer(text):
        type_name = match.group(1).strip().upper()
        body = match.group(2)

        title_raw = _parse_section(body, "TITLE")
        titles = [re.sub(r"^\d+[\.\)]\s*", "", ln).strip()
                  for ln in title_raw.splitlines() if ln.strip()]

        tags_raw = _parse_section(body, "TAGS")
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        script = _parse_section(body, "SCRIPT")

        blocks[type_name] = ScriptBlock(
            type=type_name,
            title_options=titles,
            description=_parse_section(body, "DESCRIPTION"),
            tags=tags,
            thumbnail_text=_parse_section(body, "THUMBNAIL_TEXT"),
            thumbnail_prompt=_parse_section(body, "THUMBNAIL_PROMPT"),
            raw_script=script,
        )

    return blocks


def get_block(type_name: str, path=None) -> ScriptBlock:
    blocks = parse_manual_input(path)
    type_name = type_name.upper()
    if type_name not in blocks:
        raise KeyError(
            f"No '{type_name}' block found in {path or MANUAL_INPUT_FILE}. "
            f"Found: {list(blocks.keys())}. Paste the Claude Pro output first."
        )
    return blocks[type_name]


if __name__ == "__main__":
    for t, b in parse_manual_input().items():
        print(f"[{t}] title={b.title!r} broll={len(b.broll_keywords())} "
              f"onscreen={len(b.onscreen_texts())} words={len(b.clean_for_tts().split())}")
