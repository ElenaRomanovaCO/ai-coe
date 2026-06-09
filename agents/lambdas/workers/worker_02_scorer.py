"""WORKER-02 — scorer (deterministic stage 0-5).

Per the hard guardrail, the stage is computed by rule, never by an LLM: each
dimension's score is the rounded mean of its answers' :func:`score_answer` signals,
and the overall stage is the rounded mean across dimensions. The rationale here is
a deterministic template; the conversational summary is the module agent's job.
"""

from __future__ import annotations

from typing import Any

from .base import Worker
from .dimensions import DIMENSIONS, score_answer

WORKER_ID = "WORKER-02"
_LABEL = {d: d.replace("_", " ") for d in DIMENSIONS}


def _round_mean(values: list[int]) -> int:
    if not values:
        return 0
    return round(sum(values) / len(values))


class ScorerWorker(Worker):
    agent_id = WORKER_ID

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        history = args.get("history") or []
        return self.run_tool("score", lambda _u: self._score(history))

    def _score(self, history: list[dict]) -> dict[str, Any]:
        per_dim: dict[str, list[int]] = {d: [] for d in DIMENSIONS}
        for ex in history:
            dim = ex.get("dimension")
            if dim in per_dim:
                per_dim[dim].append(score_answer(ex.get("answer", "")))

        dimension_scores = {d: _round_mean(per_dim[d]) for d in DIMENSIONS}
        stage = _round_mean(list(dimension_scores.values()))

        strongest = max(dimension_scores, key=lambda d: dimension_scores[d])
        weakest = min(dimension_scores, key=lambda d: dimension_scores[d])
        rationale = (
            f"Placed at stage {stage} of 5 based on {len(history)} responses across six "
            f"dimensions. Strongest area: {_LABEL[strongest]} ({dimension_scores[strongest]}/5). "
            f"Weakest area: {_LABEL[weakest]} ({dimension_scores[weakest]}/5). Focus next on the "
            f"lower-scoring dimensions to advance to stage {min(5, stage + 1)}."
        )
        return {
            "status": "ok",
            "stage": stage,
            "dimension_scores": dimension_scores,
            "rationale": rationale,
        }
