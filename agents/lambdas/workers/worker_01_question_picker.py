"""WORKER-01 — question_picker (deterministic, adaptive coverage).

Phase 1: ask each dimension's primary question once (6 questions, fixed order).
Phase 2: once all dimensions are covered, ask follow-ups until the target length is
reached. The target is adaptive but deterministic: ``6 + (# of weak primary
answers)`` clamped to [8, 12] — uncertain/low-maturity answers earn more probing.
Follow-ups go to the weak dimensions first. ``is_final`` when the target is met.
"""

from __future__ import annotations

from typing import Any

from .base import Worker
from .dimensions import DIMENSIONS, QUESTION_BANK, is_weak_answer

WORKER_ID = "WORKER-01"
MIN_QUESTIONS = 8
MAX_QUESTIONS = 12


def _by_dimension(history: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {d: [] for d in DIMENSIONS}
    for ex in history:
        dim = ex.get("dimension")
        if dim in out:
            out[dim].append(ex)
    return out


def _target_length(by_dim: dict[str, list[dict]]) -> int:
    weak = 0
    for dim in DIMENSIONS:
        exchanges = by_dim[dim]
        if exchanges and is_weak_answer(exchanges[0].get("answer", "")):
            weak += 1
    return max(MIN_QUESTIONS, min(MAX_QUESTIONS, len(DIMENSIONS) + weak))


class QuestionPickerWorker(Worker):
    agent_id = WORKER_ID

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        history = args.get("history") or []
        return self.run_tool("pick_question", lambda _u: self._pick(history))

    def _pick(self, history: list[dict]) -> dict[str, Any]:
        by_dim = _by_dimension(history)

        # Phase 1: cover every dimension with its primary question.
        for dim in DIMENSIONS:
            if not by_dim[dim]:
                return {
                    "status": "ok",
                    "question_text": QUESTION_BANK[dim]["primary"],
                    "dimension": dim,
                    "is_final": False,
                }

        # Phase 2: adaptive follow-ups until the (deterministic) target is met.
        target = _target_length(by_dim)
        if len(history) >= target:
            return {"status": "ok", "question_text": "", "dimension": "", "is_final": True}

        # Dimensions still on just their primary, weak ones first (fixed order).
        not_followed = [d for d in DIMENSIONS if len(by_dim[d]) < 2]
        weak_first = sorted(
            not_followed,
            key=lambda d: (not is_weak_answer(by_dim[d][0].get("answer", "")), DIMENSIONS.index(d)),
        )
        dim = weak_first[0] if weak_first else DIMENSIONS[len(history) % len(DIMENSIONS)]
        return {
            "status": "ok",
            "question_text": QUESTION_BANK[dim]["followup"],
            "dimension": dim,
            "is_final": False,
        }
