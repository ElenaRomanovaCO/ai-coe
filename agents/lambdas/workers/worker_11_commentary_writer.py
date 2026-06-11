"""WORKER-11 — commentary_writer (Sonnet 4.6; the first LLM-backed worker).

Writes the "what this means for *you*" note that turns a generic feed item into a
personalized signal: given a feed item and a user profile (industries + AI stage focus
+ tech focus), it produces 2-4 short paragraphs tailored to that reader, grounded in
the item's own body. Every other module makes its one prose call from the agent layer
(``vault/decisions/agent-05-orchestration.md``); this worker owns its call instead
because the spec scopes commentary generation to WORKER-11 and the workers Lambda role
already grants ``bedrock:InvokeModel``. AGENT-23 invokes it lazily on ``get`` — the
note is generated at view time, never persisted (real ingestion is post-demo per
``post-demo-plan.md`` Section 3.1).

If Bedrock is unavailable or errors, it degrades to a deterministic note built from the
item's own "What this means" section (or its lede), so the detail page always renders.

Input:
  - ``item`` — ``{frontmatter: {...}, body: "..."}`` (frontmatter may also be top-level).
  - ``user_profile`` — ``{industries: [...], ai_stage: int|None, tech_focus: [...]}``.

Output: ``{status, commentary: str, industry: str, ai_stage: int|None, tailored: bool}``.
``tailored`` is False when the deterministic fallback was used.
"""

from __future__ import annotations

import re
from typing import Any

from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .base import Worker

WORKER_ID = "WORKER-11"

SYSTEM = """You write a short, personalized "what this means for you" note about one AI \
intelligence-feed item, for a specific reader. You are given the item's title and body \
and the reader's profile (their industry focus and where their engagements sit on the \
0-5 AI maturity curve). Write 2-4 short paragraphs, plain-language, that a delivery lead \
in that industry and stage can act on: why this item matters to them specifically, the \
concrete implication for their work, and a sensible next step. Ground everything in the \
item content provided; do not invent facts, product names, or numbers. Be direct — no \
preamble, no headings, no bullet lists."""

# A ``## What this means`` (or similar) section in the item body — the fallback source.
_MEANS_HEADING = re.compile(
    r"^##\s+(.*what this means.*|implications.*)$", re.IGNORECASE | re.MULTILINE
)
_ANY_H2 = re.compile(r"^##\s+", re.MULTILINE)


def _norm_list(values: Any) -> list[str]:
    return [str(v).strip() for v in (values or []) if str(v).strip()]


def _strip_frontmatter(body: str) -> str:
    if body.startswith("---"):
        end = body.find("\n---", 3)
        if end != -1:
            return body[end + 4 :].lstrip("\n")
    return body


def _means_section(body: str) -> str:
    """Extract the item's own 'What this means' section, if present."""
    m = _MEANS_HEADING.search(body)
    if not m:
        return ""
    start = m.end()
    nxt = _ANY_H2.search(body, start)
    section = body[start : nxt.start() if nxt else len(body)]
    return " ".join(section.split()).strip()


def _lede(body: str) -> str:
    """First non-heading paragraph of the body."""
    for para in re.split(r"\n\s*\n", _strip_frontmatter(body)):
        para = para.strip()
        if para and not para.startswith("#"):
            return " ".join(para.split())
    return ""


def _industry_label(profile_industries: list[str]) -> str:
    direct = [i for i in profile_industries if i.lower() != "cross-industry"]
    if direct:
        return direct[0].replace("-", " ")
    if profile_industries:
        return "cross-industry"
    return "your"


def _stage_phrase(ai_stage: Any) -> str:
    try:
        return f"stage {int(ai_stage)}"
    except (TypeError, ValueError):
        return "your current"


class CommentaryWriterWorker(Worker):
    agent_id = WORKER_ID
    model_id = lib_models.SONNET_4_6

    def __init__(self, *, bedrock_client: BedrockClient | None = None, bedrock: Any = None,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.bedrock_client = bedrock_client or BedrockClient(client=bedrock)

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.run_tool("write_commentary", lambda _u: self._write(args))

    def _write(self, args: dict[str, Any]) -> dict[str, Any]:
        item = args.get("item") or {}
        fm = item.get("frontmatter") if isinstance(item, dict) else None
        fm = fm or args.get("frontmatter") or {}
        item_body = item.get("body") if isinstance(item, dict) else ""
        body = str(item_body or "") or str(args.get("body") or "")
        title = str(fm.get("title") or "this update")

        profile = args.get("user_profile") or {}
        industries = _norm_list(profile.get("industries"))
        ai_stage = profile.get("ai_stage")
        tech_focus = _norm_list(profile.get("tech_focus"))
        industry_label = _industry_label(industries)

        commentary = self._generate(title, body, industry_label, ai_stage, tech_focus)
        tailored = bool(commentary)
        if not commentary:
            commentary = self._fallback(body, industry_label, ai_stage)

        return {
            "status": "ok",
            "commentary": commentary,
            "industry": industry_label,
            "ai_stage": ai_stage,
            "tailored": tailored,
        }

    def _generate(
        self, title: str, body: str, industry: str, ai_stage: Any, tech_focus: list[str]
    ) -> str:
        focus = ", ".join(tech_focus) if tech_focus else "(none specified)"
        user_text = (
            f"Reader profile:\n"
            f"- Industry focus: {industry}\n"
            f"- AI maturity stage: {_stage_phrase(ai_stage)}\n"
            f"- Tech focus: {focus}\n\n"
            f"Feed item title: {title}\n\n"
            f"Feed item body:\n{_strip_frontmatter(body).strip() or '(no body)'}\n\n"
            f"Write the personalized note."
        )
        try:
            with instrumented(
                agent_id=self.agent_id,
                tool_name="bedrock:converse",
                model_id=self.model_id,
                metrics_client=self.metrics_client,
            ) as usage:
                resp = self.bedrock_client.converse(
                    model_id=self.model_id,
                    messages=[{"role": "user", "content": [{"text": user_text}]}],
                    system=SYSTEM,
                    max_tokens=600,
                    usage=usage,
                )
            return _extract_text(resp.get("output", {}).get("message", {}))
        except Exception:  # noqa: BLE001 — fall back to a deterministic note
            return ""

    def _fallback(self, body: str, industry: str, ai_stage: Any) -> str:
        source = _means_section(body) or _lede(body)
        lead = (
            f"For {industry} teams at {_stage_phrase(ai_stage)} maturity, here's the gist."
            if industry != "your"
            else "Here's the gist for your work."
        )
        return f"{lead} {source}".strip() if source else lead


def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()
