"""Heading-aware markdown chunking for embedding.

Splits a markdown document into chunks that respect heading boundaries, stay
under a token budget, and carry overlap so a fact split across a boundary is
still retrievable. Token counts are estimated at ~4 characters/token (good
enough for Titan Embed v2 budgeting; we never need exact counts here).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass
class Chunk:
    index: int
    text: str
    heading_path: list[str]


@dataclass
class _Section:
    heading_path: list[str]
    lines: list[str]

    def body(self) -> str:
        return "\n".join(self.lines).strip()


def _split_sections(md: str) -> list[_Section]:
    """Split into sections at heading lines; each section keeps its heading path."""
    sections: list[_Section] = []
    stack: list[tuple[int, str]] = []  # (level, title)
    current = _Section(heading_path=[], lines=[])

    for line in md.splitlines():
        m = _HEADING.match(line)
        if m:
            if current.body():
                sections.append(current)
            level = len(m.group(1))
            title = m.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            current = _Section(heading_path=[t for _, t in stack], lines=[line])
        else:
            current.lines.append(line)

    if current.body():
        sections.append(current)
    return sections


def _split_long(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    """Split a too-large section into word-packed pieces with trailing overlap."""
    words = text.split()
    pieces: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for w in words:
        if cur and cur_len + len(w) + 1 > max_chars:
            pieces.append(" ".join(cur))
            tail: list[str] = []
            tail_len = 0
            for ww in reversed(cur):
                if tail_len + len(ww) + 1 > overlap_chars:
                    break
                tail.insert(0, ww)
                tail_len += len(ww) + 1
            cur = tail
            cur_len = tail_len
        cur.append(w)
        cur_len += len(w) + 1
    if cur:
        pieces.append(" ".join(cur))
    return pieces


def chunk_markdown(
    md: str,
    *,
    max_tokens: int = 1000,
    overlap_tokens: int = 100,
    chars_per_token: int = 4,
) -> list[Chunk]:
    """Chunk a markdown document. Returns chunks in document order."""
    max_chars = max_tokens * chars_per_token
    overlap_chars = overlap_tokens * chars_per_token

    raw: list[tuple[str, list[str]]] = []
    buf = ""
    buf_path: list[str] = []

    for section in _split_sections(md):
        body = section.body()
        if len(body) > max_chars:
            if buf:
                raw.append((buf, buf_path))
                buf = ""
            for piece in _split_long(body, max_chars, overlap_chars):
                raw.append((piece, section.heading_path))
            continue
        if buf and len(buf) + 2 + len(body) > max_chars:
            raw.append((buf, buf_path))
            buf = ""
        if not buf:
            buf, buf_path = body, section.heading_path
        else:
            buf = f"{buf}\n\n{body}"

    if buf:
        raw.append((buf, buf_path))

    return [Chunk(index=i, text=t, heading_path=p) for i, (t, p) in enumerate(raw)]
