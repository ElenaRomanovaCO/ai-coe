"""WORKER-05 — checklist_generator (deterministic, rule-table driven).

Turns the regulations WORKER-04 matched, plus the engagement context, into an
actionable pre-delivery risk checklist. Each matched regulation contributes a small
set of templated, regulation-linked items; data types and a governance baseline add
a few cross-cutting items. Deterministic and fully testable — no LLM (the agent layer
makes the one prose call), consistent with ``vault/decisions/worker-pattern.md``.
Items are de-duplicated by statement and returned highest-priority first.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .base import Worker

WORKER_ID = "WORKER-05"

_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class ChecklistItem(BaseModel):
    id: str = ""
    statement: str
    priority: str = "medium"
    regulation_links: list[str] = Field(default_factory=list)
    rationale: str = ""


# Per-regulation checklist items: reg id -> list of (statement, priority, rationale).
# Keyed on the seeded regulation ids (see vault/regs/).
_REG_ITEMS: dict[str, list[tuple[str, str, str]]] = {
    "reg-eu-ai-act": [
        (
            "Classify the use case under the EU AI Act risk tiers (unacceptable / high / "
            "limited / minimal) before design sign-off.",
            "critical",
            "The tier determines the entire obligation set; high-risk systems carry "
            "the heaviest duties.",
        ),
        (
            "For a high-risk system, plan technical documentation, logging, human oversight, "
            "and conformity assessment into the delivery timeline.",
            "high",
            "High-risk obligations must be met before market placement, not retrofitted.",
        ),
        (
            "Provide clear AI-interaction disclosure for any limited-risk, user-facing features.",
            "medium",
            "Limited-risk systems still carry transparency duties under the Act.",
        ),
    ],
    "reg-gdpr-ai": [
        (
            "Run a Data Protection Impact Assessment (DPIA) for automated decisions "
            "over personal data.",
            "high",
            "GDPR requires a DPIA for high-risk processing, including profiling and "
            "automated decisions.",
        ),
        (
            "Establish a lawful basis and honor data-subject rights (access, erasure, objection).",
            "high",
            "Personal-data processing needs a documented lawful basis and a path for "
            "subject requests.",
        ),
    ],
    "reg-hipaa-ai": [
        (
            "Confirm a Business Associate Agreement (BAA) is in place for any service "
            "that processes PHI.",
            "critical",
            "HIPAA requires a BAA before PHI reaches any model or inference endpoint.",
        ),
        (
            "Apply minimum-necessary and de-identify PHI before embedding or retrieval.",
            "high",
            "Only the PHI needed for the task should reach the model; de-identified "
            "data falls outside HIPAA.",
        ),
        (
            "Log access to PHI, including retrieval in the RAG pipeline.",
            "medium",
            "Access auditing is required and must cover AI retrieval paths.",
        ),
    ],
    "reg-fda-ai-ml": [
        (
            "Determine whether the system is Software as a Medical Device (SaMD) and "
            "the applicable FDA pathway.",
            "critical",
            "SaMD classification drives the regulatory pathway and pre-market obligations.",
        ),
        (
            "Define a Predetermined Change Control Plan (PCCP) if the model will be "
            "updated post-market.",
            "high",
            "The FDA expects a PCCP for AI/ML devices that learn or are updated over time.",
        ),
    ],
    "reg-ffiec-ai": [
        (
            "Apply model risk management — validation, monitoring, and documentation "
            "— per FFIEC guidance.",
            "high",
            "Financial-institution models require formal validation and ongoing monitoring.",
        ),
        (
            "Assess third-party and vendor risk for any external model or inference providers.",
            "medium",
            "FFIEC expects diligence on third-party dependencies in the model supply chain.",
        ),
    ],
    "reg-sec-ai-guidance": [
        (
            "Ensure public statements about AI capabilities are accurate — avoid 'AI-washing'.",
            "high",
            "The SEC scrutinizes overstated AI claims in disclosures.",
        ),
        (
            "Identify and disclose conflicts of interest introduced by AI-driven recommendations.",
            "medium",
            "AI-driven advice can create conflicts the SEC expects to be surfaced.",
        ),
    ],
    "reg-nist-ai-rmf": [
        (
            "Map the system to the NIST AI RMF functions (Govern, Map, Measure, Manage).",
            "medium",
            "Voluntary, but a strong governance baseline that structures the rest of the controls.",
        ),
    ],
    "reg-ca-sb-1001": [
        (
            "Disclose to users when they are interacting with a bot (California SB-1001).",
            "high",
            "SB-1001 requires clear bot-disclosure to California consumers.",
        ),
    ],
}

# Cross-cutting items keyed on declared data types (added when not already implied
# by a matched regulation).
_DATA_TYPE_ITEMS: dict[str, tuple[str, str, str]] = {
    "phi": (
        "Treat health data as PHI: restrict access, de-identify where possible, and "
        "keep an audit trail.",
        "high",
        "Health data is highly sensitive even where HIPAA is not the governing regime.",
    ),
    "pii": (
        "Minimize personally identifiable information and define retention and deletion policies.",
        "high",
        "PII handling drives privacy obligations across most regimes.",
    ),
    "financial": (
        "Apply model risk controls and explainability for any financial decisioning.",
        "medium",
        "Financial decisions carry heightened fairness and explainability expectations.",
    ),
    "biometric": (
        "Confirm consent and a lawful basis before processing biometric data.",
        "high",
        "Biometric data is a special category with stricter consent requirements.",
    ),
}

# Always-on governance baseline.
_BASELINE_ITEMS: list[tuple[str, str, str]] = [
    (
        "Define human oversight and an escalation path for AI-driven decisions.",
        "high",
        "A human-in-the-loop control is the most broadly expected governance safeguard.",
    ),
    (
        "Document the use case, data sources, and intended decisions for auditability.",
        "medium",
        "Traceable documentation underpins every regulatory regime and internal review.",
    ),
]


class ChecklistGeneratorWorker(Worker):
    agent_id = WORKER_ID

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.run_tool("generate_checklist", lambda _u: self._generate(args))

    def _generate(self, args: dict[str, Any]) -> dict[str, Any]:
        regulations = args.get("regulations") or []
        context = args.get("engagement_context") or {}
        data_types = [
            str(d).strip().lower() for d in (context.get("data_types") or []) if str(d).strip()
        ]

        matched_ids = {str(r.get("id")) for r in regulations}
        items: list[ChecklistItem] = []
        seen: set[str] = set()

        def add(statement: str, priority: str, rationale: str, links: list[str]) -> None:
            key = statement.strip().lower()
            if key in seen:
                # Merge regulation links if the same statement recurs.
                for existing in items:
                    if existing.statement.strip().lower() == key:
                        for link in links:
                            if link not in existing.regulation_links:
                                existing.regulation_links.append(link)
                        break
                return
            seen.add(key)
            items.append(
                ChecklistItem(
                    statement=statement,
                    priority=priority if priority in _PRIORITY_ORDER else "medium",
                    regulation_links=list(links),
                    rationale=rationale,
                )
            )

        # 1. Regulation-driven items, in the order WORKER-04 ranked them.
        for reg in regulations:
            reg_id = str(reg.get("id"))
            for statement, priority, rationale in _REG_ITEMS.get(reg_id, []):
                add(statement, priority, rationale, [reg_id])

        # 2. Data-type items (skip phi if HIPAA already covers it).
        for dt in data_types:
            if dt == "phi" and "reg-hipaa-ai" in matched_ids:
                continue
            entry = _DATA_TYPE_ITEMS.get(dt)
            if entry:
                add(entry[0], entry[1], entry[2], [])

        # 3. Governance baseline.
        for statement, priority, rationale in _BASELINE_ITEMS:
            add(statement, priority, rationale, [])

        # Stable sort by priority (critical -> low); ties keep insertion order.
        items.sort(key=lambda it: _PRIORITY_ORDER.get(it.priority, 2))
        for i, it in enumerate(items, start=1):
            it.id = f"chk-{i:02d}"

        return {"status": "ok", "checklist": [it.model_dump() for it in items]}
