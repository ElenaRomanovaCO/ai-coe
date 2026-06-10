"""WORKER-08 — bias_analyzer (deterministic, rule-based).

Takes a use case + data types + affected populations + decision type and emits bias
risks across the four categories the task names: **data representation, sample bias,
label bias, automation bias**. Each risk carries a severity and a concrete mitigation.
Deterministic and fully testable — no LLM, no S3 (pure compute on the inputs),
consistent with ``vault/decisions/worker-pattern.md``.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from .base import Worker

WORKER_ID = "WORKER-08"

# Populations that warrant heightened representation scrutiny (protected / vulnerable).
_PROTECTED = {
    "minority",
    "minorities",
    "race",
    "racial",
    "ethnic",
    "ethnicity",
    "black",
    "hispanic",
    "indigenous",
    "immigrant",
    "women",
    "woman",
    "female",
    "gender",
    "lgbtq",
    "disabled",
    "disability",
    "elderly",
    "senior",
    "aged",
    "low-income",
    "poor",
    "veteran",
    "religion",
    "religious",
    "rural",
    "non-native",
    "limited-english",
    "children",
    "minors",
    "patients",
}

# Data types whose historical nature can encode past inequities (sample bias).
_HISTORICAL_DATA = {"behavioral", "historical", "transaction", "financial", "location", "credit"}


class Risk(BaseModel):
    id: str = ""
    category: str
    description: str
    severity: str = "medium"  # critical | high | medium | low
    mitigation: str = ""


def _tokens(values: list[str]) -> set[str]:
    out: set[str] = set()
    for v in values:
        out.update(t for t in re.split(r"[^a-z0-9]+", str(v).lower()) if t)
    return out


class BiasAnalyzerWorker(Worker):
    agent_id = WORKER_ID

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.run_tool("analyze_bias", lambda _u: self._analyze(args))

    def _analyze(self, args: dict[str, Any]) -> dict[str, Any]:
        data_types = [
            str(d).strip().lower() for d in (args.get("data_types") or []) if str(d).strip()
        ]
        populations = [
            str(p).strip() for p in (args.get("affected_populations") or []) if str(p).strip()
        ]
        decision_type = str(args.get("decision_type") or "assisted").strip().lower()
        pop_tokens = _tokens(populations)
        has_protected = bool(pop_tokens & _PROTECTED)
        pop_phrase = ", ".join(populations) if populations else "affected individuals"

        risks: list[Risk] = []

        # 1. Data representation — always assessed; protected groups raise severity.
        risks.append(
            Risk(
                category="data_representation",
                description=(
                    f"Training data may under-represent {pop_phrase}, degrading model "
                    "performance for those groups."
                ),
                severity="high" if has_protected else "medium",
                mitigation=(
                    "Audit representation across subgroups and reweight or augment "
                    "under-represented populations before training."
                ),
            )
        )

        # 2. Sample bias — when the inputs lean on historical/behavioral data.
        if set(data_types) & _HISTORICAL_DATA:
            risks.append(
                Risk(
                    category="sample_bias",
                    description=(
                        "Historical/behavioral data can encode past inequities, so the model "
                        "may reproduce them as if they were ground truth."
                    ),
                    severity="high" if has_protected else "medium",
                    mitigation=(
                        "Test for disparate impact against a held-out, balanced sample and "
                        "correct skew before deployment."
                    ),
                )
            )

        # 3. Label bias — when the system makes or assists consequential decisions.
        if decision_type in ("automated", "assisted"):
            risks.append(
                Risk(
                    category="label_bias",
                    description=(
                        "If training labels came from past human decisions, the model can "
                        "inherit the biases embedded in those judgments."
                    ),
                    severity="medium",
                    mitigation=(
                        "Examine label provenance; prefer objective outcome labels over "
                        "subjective historical decisions where possible."
                    ),
                )
            )

        # 4. Automation bias — severity scales with how much the human is removed.
        auto_sev, auto_desc = {
            "automated": (
                "high",
                "A fully automated decision removes the human check, so erroneous or biased "
                "outputs act directly on people.",
            ),
            "assisted": (
                "medium",
                "Operators may over-trust the model's suggestion and rubber-stamp it without "
                "independent judgment.",
            ),
            "recommendation-only": (
                "low",
                "Even advisory outputs can anchor a reviewer's decision toward the model.",
            ),
        }.get(decision_type, ("medium", "Users may over-rely on the model's output."))
        risks.append(
            Risk(
                category="automation_bias",
                description=auto_desc,
                severity=auto_sev,
                mitigation=(
                    "Require human review for adverse or high-impact outcomes, surface model "
                    "confidence, and log overrides to monitor for rubber-stamping."
                ),
            )
        )

        for i, r in enumerate(risks, start=1):
            r.id = f"bias-{i:02d}"
        return {"status": "ok", "bias_risks": [r.model_dump() for r in risks]}
