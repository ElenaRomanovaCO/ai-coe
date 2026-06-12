"""WORKER-20 — vetting_scorer (deterministic, no LLM, no AWS).

Scores one vendor's security/compliance posture against a fixed control catalog and
returns a risk tier plus a per-control pass/gap/unknown breakdown. The signals come from
a ``vetting`` block in the vendor's frontmatter (see ``vault/vendors/*.md``); the agent
(AGENT-30) reads the vendor and passes the frontmatter in, so this stays pure and
trivially testable — same Layer-3 worker pattern as the others
(``vault/decisions/worker-pattern.md``).

Context matters: for PHI/healthcare engagements a missing HIPAA BAA is load-bearing
(⇒ high), and any vendor that trains on customer data is high regardless of context.

Input:
  - ``frontmatter`` — the vendor's parsed frontmatter (reads ``frontmatter['vetting']``);
    a bare ``vetting`` dict at the top level is also accepted.
  - ``context_industry`` — e.g. ``healthcare`` (makes the BAA control load-bearing).
  - ``data_sensitivity`` — ``public | internal | pii | phi``.

Output: ``{status, risk_tier, controls: [{control, result, detail}], gaps: [...]}``.
"""

from __future__ import annotations

from typing import Any

from .base import Worker

WORKER_ID = "WORKER-20"

# (key, human label, kind). kind drives how the raw value maps to pass/gap/unknown.
#   bool      — True=pass, False=gap, missing=unknown
#   neg_bool  — True=gap (a risk), False=pass, missing=unknown  (e.g. trains-on-data)
#   value     — non-empty/known string=pass, else unknown
#   retention — int days <= 365 = pass, > 365 = gap, missing=unknown
_CONTROLS: list[tuple[str, str, str]] = [
    ("data_residency", "Data residency control", "value"),
    ("sub_processors_disclosed", "Sub-processor disclosure", "bool"),
    ("encryption_at_rest", "Encryption at rest", "bool"),
    ("encryption_in_transit", "Encryption in transit", "bool"),
    ("soc2_type2", "SOC 2 Type II", "bool"),
    ("iso27001", "ISO 27001", "bool"),
    ("hipaa_baa", "HIPAA BAA available", "bool"),
    ("trains_on_customer_data", "Does not train on customer data", "neg_bool"),
    ("data_retention_days", "Bounded data retention", "retention"),
    ("sso", "SSO / access controls", "bool"),
]


def _score_control(kind: str, value: Any) -> tuple[str, str]:
    """Return (result, detail) for one control given its raw value."""
    if kind == "neg_bool":
        if value is True:
            return "gap", "Vendor trains on customer data"
        if value is False:
            return "pass", "Does not train on customer data"
        return "unknown", "Not stated"
    if kind == "bool":
        if value is True:
            return "pass", "Yes"
        if value is False:
            return "gap", "No"
        return "unknown", "Not stated"
    if kind == "value":
        s = str(value).strip().lower()
        if s and s not in ("unknown", "none", "no"):
            return "pass", str(value)
        return "unknown", "Not stated"
    if kind == "retention":
        try:
            days = int(value)
        except (TypeError, ValueError):
            return "unknown", "Not stated"
        if days <= 365:
            return "pass", f"{days} days"
        return "gap", f"{days} days (long)"
    return "unknown", "Not stated"


class VettingScorerWorker(Worker):
    agent_id = WORKER_ID

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.run_tool("score_vetting", lambda _u: self._score(args))

    def _score(self, args: dict[str, Any]) -> dict[str, Any]:
        fm = args.get("frontmatter") or {}
        vetting = fm.get("vetting") if isinstance(fm, dict) else None
        if not isinstance(vetting, dict):
            vetting = args.get("vetting") if isinstance(args.get("vetting"), dict) else {}

        context_industry = str(args.get("context_industry", "")).strip().lower()
        data_sensitivity = str(args.get("data_sensitivity", "")).strip().lower()
        phi_context = data_sensitivity == "phi" or context_industry == "healthcare"

        controls: list[dict[str, str]] = []
        gaps: list[str] = []
        for key, label, kind in _CONTROLS:
            result, detail = _score_control(kind, vetting.get(key))
            controls.append({"control": label, "result": result, "detail": detail})
            if result == "gap":
                gaps.append(label)

        risk_tier = self._risk_tier(vetting, controls, phi_context)
        return {"status": "ok", "risk_tier": risk_tier, "controls": controls, "gaps": gaps}

    @staticmethod
    def _risk_tier(vetting: dict, controls: list[dict], phi_context: bool) -> str:
        trains = vetting.get("trains_on_customer_data") is True
        baa = vetting.get("hipaa_baa") is True
        # Hard-high triggers, regardless of how clean the rest looks.
        if trains:
            return "high"
        if phi_context and not baa:
            return "high"

        gaps = sum(1 for c in controls if c["result"] == "gap")
        unknowns = sum(1 for c in controls if c["result"] == "unknown")
        if gaps >= 3 or unknowns >= 5:
            return "high"
        if gaps >= 1 or unknowns >= 2:
            return "medium"
        return "low"
