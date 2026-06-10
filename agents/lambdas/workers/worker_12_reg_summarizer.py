"""WORKER-12 — reg_summarizer (deterministic, extractive; no LLM, no AWS).

Turns a single regulation's markdown into a structured plain-language summary:
a one-paragraph overview, a list of key requirements, and the sector implications.
The seeded regulations in ``vault/regs/`` are already authored in plain language with
a consistent structure (an intro paragraph, ``##`` clause sections, and a
"What this means for engagements" section), so a deterministic extractive pass is
simpler, faster, and more predictable than an LLM — consistent with the other Layer-3
workers (``vault/decisions/worker-pattern.md``). The agent layer (AGENT-24) makes the
one prose call, and only on the ``apply`` path.

Input (AGENT-24 reads the reg from S3 and passes the content in, so this stays pure):
  - ``frontmatter`` — the parsed reg frontmatter (dict)
  - ``body`` — the reg markdown body (the part after the frontmatter)

Output: ``{status, summary, key_requirements: [...], sector_implications: [...]}``.
"""

from __future__ import annotations

import re
from typing import Any

from .base import Worker

WORKER_ID = "WORKER-12"

# A ``## Heading`` line; captures the heading text.
_H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
# A ``- **Label** — description`` bullet (em dash or hyphen separator).
_BOLD_BULLET = re.compile(r"^\s*[-*]\s+\*\*(.+?)\*\*\s*[—–:-]?\s*(.*)$")
# Headings that describe implications rather than requirements.
_IMPLICATIONS_RE = re.compile(r"what this means|implications for engagements", re.IGNORECASE)
# Headings that are scene-setting rather than discrete requirements.
_OVERVIEW_RE = re.compile(r"^(overview|introduction|summary|scope|background)\b", re.IGNORECASE)

_MAX_REQUIREMENTS = 8
_MAX_IMPLICATIONS = 5


def _first_sentence(text: str, limit: int = 200) -> str:
    text = " ".join(text.split())
    m = re.search(r"(.+?[.!?])(\s|$)", text)
    out = m.group(1) if m else text
    return out if len(out) <= limit else out[: limit - 1].rstrip() + "…"


def _sections(body: str) -> tuple[str, list[tuple[str, str]]]:
    """Split a reg body into (preamble before the first H2, [(heading, text), ...])."""
    matches = list(_H2.finditer(body))
    if not matches:
        return body.strip(), []
    preamble = body[: matches[0].start()]
    sections: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections.append((m.group(1).strip(), body[start:end].strip()))
    return preamble.strip(), sections


def _intro_paragraph(preamble: str) -> str:
    """First non-heading, non-empty paragraph of the preamble (drops the H1)."""
    text = re.sub(r"^#\s+.+?$", "", preamble, count=1, flags=re.MULTILINE).strip()
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if para and not para.startswith("#"):
            return " ".join(para.split())
    return ""


class RegSummarizerWorker(Worker):
    agent_id = WORKER_ID

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.run_tool("summarize_regulation", lambda _u: self._summarize(args))

    def _summarize(self, args: dict[str, Any]) -> dict[str, Any]:
        fm = args.get("frontmatter") or {}
        body = str(args.get("body") or "")
        preamble, sections = _sections(body)

        summary = _intro_paragraph(preamble) or str(fm.get("name") or "").strip()

        key_requirements: list[str] = []
        sector_implications: list[str] = []
        fallback_headings: list[str] = []

        for heading, text in sections:
            if _IMPLICATIONS_RE.search(heading):
                sector_implications.extend(_to_points(text))
                continue
            if _OVERVIEW_RE.search(heading):
                continue
            bullets = _bold_bullets(text)
            if bullets:
                key_requirements.extend(bullets)
            else:
                fallback_headings.append(heading)

        # If a reg used prose sections (no bolded bullets), fall back to the section
        # headings as the key requirement labels so the card is never empty.
        if not key_requirements:
            key_requirements = fallback_headings

        return {
            "status": "ok",
            "summary": summary,
            "key_requirements": key_requirements[:_MAX_REQUIREMENTS],
            "sector_implications": sector_implications[:_MAX_IMPLICATIONS],
        }


def _bold_bullets(text: str) -> list[str]:
    out: list[str] = []
    for block in _bullet_blocks(text):
        m = _BOLD_BULLET.match(block)
        if not m:
            continue
        label = m.group(1).strip()
        desc = _first_sentence(m.group(2).strip())
        out.append(f"{label} — {desc}" if desc else label)
    return out


def _bullet_blocks(text: str) -> list[str]:
    """Group lines into bullet blocks, coalescing wrapped continuation lines."""
    blocks: list[list[str]] = []
    for line in text.splitlines():
        if re.match(r"^\s*[-*]\s+", line):
            blocks.append([line.strip()])
        elif blocks and line.strip():  # continuation of the current bullet
            blocks[-1].append(line.strip())
    return [" ".join(b) for b in blocks]


def _to_points(text: str) -> list[str]:
    """Split an implications section into short points (bulleted or sentence-wise)."""
    lines = [ln.strip(" -*") for ln in text.splitlines() if ln.strip().startswith(("-", "*"))]
    if lines:
        return [" ".join(ln.split()) for ln in lines if ln]
    flat = " ".join(text.split())
    points = [s.strip() for s in re.split(r"(?<=[.!?])\s+", flat) if len(s.strip()) >= 20]
    return points
