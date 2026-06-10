"""WORKER-09 — regulation_mapper (deterministic, rule-based).

Maps a use case to its regulatory posture: the EU AI Act risk tier (the core output),
plus sector implications for HIPAA (healthcare / PHI) and FFIEC (financial). Each
framework entry carries a ``reg_id`` ONLY when a backing file exists in ``vault/regs/``
(reg-eu-ai-act, reg-hipaa-ai, reg-ffiec-ai all exist and are confirmed), so the UI
never renders a dangling citation; frameworks without a vault file would be returned
as plain named implications instead. Deterministic, no LLM, no S3.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from .base import Worker

WORKER_ID = "WORKER-09"

# Reg ids that have a backing markdown file in vault/regs/ (verified). Only these get
# attached as citations; any other framework is named in text without a reg_id.
_REG_EU_AI_ACT = "reg-eu-ai-act"
_REG_HIPAA = "reg-hipaa-ai"
_REG_FFIEC = "reg-ffiec-ai"

# High-stakes domains that push the EU AI Act tier toward "high".
_HIGH_STAKES = {
    "lending",
    "loan",
    "credit",
    "underwriting",
    "mortgage",
    "hiring",
    "recruit",
    "employment",
    "hr",
    "medical",
    "clinical",
    "diagnos",
    "health",
    "biometric",
    "face",
    "facial",
    "law",
    "police",
    "criminal",
    "justice",
    "education",
    "exam",
    "admission",
    "insurance",
    "benefit",
    "welfare",
    "housing",
}
# Practices the Act treats as unacceptable.
_UNACCEPTABLE = {"social-scoring", "social scoring", "mass surveillance", "predictive policing"}


def _hay(*values: str) -> str:
    return " ".join(v for v in values if v).lower()


class FrameworkMapping(BaseModel):
    framework: str
    tier: str  # EU AI Act: minimal|limited|high|unacceptable; sector: applicable|n/a
    reg_id: str | None = None
    note: str = ""


class RegulationMapperWorker(Worker):
    agent_id = WORKER_ID

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.run_tool("map_regulations", lambda _u: self._map(args))

    def _eu_ai_act_tier(self, text: str, decision_type: str) -> tuple[str, str]:
        if any(k in text for k in _UNACCEPTABLE):
            return "unacceptable", (
                "Use case touches a practice the EU AI Act may prohibit outright; "
                "confirm it is not a banned use before proceeding."
            )
        high_stakes = any(re.search(re.escape(k), text) for k in _HIGH_STAKES)
        if high_stakes and decision_type in ("automated", "assisted"):
            return "high", (
                "Decisioning in a sensitive domain → likely a high-risk system: plan "
                "documentation, logging, human oversight, and conformity assessment."
            )
        if high_stakes:
            return "limited", (
                "Sensitive domain but advisory only → transparency duties apply; disclose "
                "AI involvement and keep a human decision-maker."
            )
        return "minimal", (
            "No sensitive-domain decisioning detected → minimal-risk; maintain basic "
            "transparency and documentation."
        )

    def _map(self, args: dict[str, Any]) -> dict[str, Any]:
        use_case = str(args.get("use_case") or "")
        decision_type = str(args.get("decision_type") or "assisted").strip().lower()
        industry = str(args.get("industry") or "").strip().lower()
        data_types = [str(d).strip().lower() for d in (args.get("data_types") or [])]
        text = _hay(use_case, industry, " ".join(data_types))

        frameworks: list[FrameworkMapping] = []

        tier, note = self._eu_ai_act_tier(text, decision_type)
        frameworks.append(
            FrameworkMapping(framework="EU AI Act", tier=tier, reg_id=_REG_EU_AI_ACT, note=note)
        )

        # HIPAA — healthcare or PHI in scope.
        if industry == "healthcare" or "phi" in data_types or "health" in text:
            frameworks.append(
                FrameworkMapping(
                    framework="HIPAA",
                    tier="applicable",
                    reg_id=_REG_HIPAA,
                    note="PHI in scope: require a BAA, minimum-necessary use, and audit logging.",
                )
            )

        # FFIEC — financial institutions / credit decisioning.
        if industry in ("financial-services", "fintech", "banking") or any(
            k in text for k in ("lending", "credit", "underwriting", "bank", "loan")
        ):
            frameworks.append(
                FrameworkMapping(
                    framework="FFIEC",
                    tier="applicable",
                    reg_id=_REG_FFIEC,
                    note=(
                        "Financial decisioning: apply model risk management and "
                        "third-party diligence."
                    ),
                )
            )

        # framework -> tier (the spec's regulatory_tier dict) + the richer list.
        regulatory_tier = {f.framework: f.tier for f in frameworks}
        return {
            "status": "ok",
            "regulatory_tier": regulatory_tier,
            "frameworks": [f.model_dump() for f in frameworks],
        }
