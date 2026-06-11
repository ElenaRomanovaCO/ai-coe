"""WORKER-10 — item_classifier (deterministic, no LLM, no AWS).

Scores one feed item against a user profile and confirms its classification, so the
feed can be ranked by relevance to *this* user. The seeded feed items in
``vault/feed/`` already carry a ``category``, ``industries``, and ``radar_status`` in
frontmatter (real ingestion that derives these from raw articles is post-demo per
``post-demo-plan.md`` Section 3.1), so the worker's job here is the *relevance* signal:
how well an item matches the user's industries and tech focus, weighted by where it
sits on the radar. A deterministic pass is simpler and more predictable than an LLM and
matches the other Layer-3 workers (``vault/decisions/worker-pattern.md``).

Input:
  - ``item`` — ``{frontmatter: {...}, body: "..."}`` (body optional; only frontmatter
    is used for scoring). For convenience the frontmatter fields may also be passed at
    the top level.
  - ``user_profile`` — ``{industries: [...], ai_stage: int|None, tech_focus: [...]}``
    (all optional; an empty profile yields a neutral baseline score).

Output: ``{status, category, industries: [...], relevance_score: float (0-1),
matched: {industries: [...], tags: [...]}}``.

Recency is intentionally NOT part of the score: a single item has no batch context to
normalize against, so AGENT-23 applies the date tie-break across the whole feed.
"""

from __future__ import annotations

from typing import Any

from .base import Worker

WORKER_ID = "WORKER-10"

# Radar position is a relevance signal: things the CoE has decided to adopt matter more
# than things parked on hold. Items with no radar status (pure news) get a small bump.
_RADAR_WEIGHT: dict[str, float] = {
    "adopt": 0.10,
    "trial": 0.07,
    "assess": 0.04,
    "hold": 0.0,
}
_NO_RADAR_WEIGHT = 0.05

_BASE_SCORE = 0.30
_DIRECT_INDUSTRY_BONUS = 0.40
_CROSS_INDUSTRY_BONUS = 0.15
_TAG_BONUS_EACH = 0.05
_TAG_BONUS_MAX = 0.20


def _norm(value: str) -> str:
    return str(value or "").strip().lower()


def _norm_list(values: Any) -> list[str]:
    return [_norm(v) for v in (values or []) if str(v).strip()]


class ItemClassifierWorker(Worker):
    agent_id = WORKER_ID

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.run_tool("classify_item", lambda _u: self._classify(args))

    def _classify(self, args: dict[str, Any]) -> dict[str, Any]:
        item = args.get("item") or {}
        fm = item.get("frontmatter") if isinstance(item, dict) else None
        # Accept frontmatter at the top level too (lenient on payload shape).
        fm = fm or args.get("frontmatter") or args

        category = _norm(fm.get("category"))
        item_industries = _norm_list(fm.get("industries"))
        item_tags = _norm_list(fm.get("tags"))
        radar = _norm(fm.get("radar_status")) or None

        profile = args.get("user_profile") or {}
        profile_industries = _norm_list(profile.get("industries"))
        profile_tags = _norm_list(profile.get("tech_focus"))

        score = _BASE_SCORE

        matched_industries = sorted(set(item_industries) & set(profile_industries))
        if matched_industries:
            score += _DIRECT_INDUSTRY_BONUS
        elif "cross-industry" in item_industries:
            # Broadly-relevant items still surface even without a direct match.
            score += _CROSS_INDUSTRY_BONUS

        matched_tags = sorted(set(item_tags) & set(profile_tags))
        if matched_tags:
            score += min(_TAG_BONUS_MAX, _TAG_BONUS_EACH * len(matched_tags))

        score += _RADAR_WEIGHT[radar] if radar in _RADAR_WEIGHT else _NO_RADAR_WEIGHT

        score = round(max(0.0, min(1.0, score)), 4)

        return {
            "status": "ok",
            "category": category,
            "industries": item_industries,
            "relevance_score": score,
            "matched": {"industries": matched_industries, "tags": matched_tags},
        }
