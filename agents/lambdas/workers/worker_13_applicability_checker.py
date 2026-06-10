"""WORKER-13 — applicability_checker (deterministic; no LLM, no AWS).

Given one regulation and a described use case, decides which of the regulation's
clauses apply, which do not, and why. Deterministic and fully testable — clause
applicability is decided by keyword/domain-signal overlap between the use case and
each ``##`` clause, plus a regulation-level geography/industry gate, consistent with
``vault/decisions/worker-pattern.md``. AGENT-24 adds the one plain-language narrative
(the single Sonnet call) on top of this structured result.

Input:
  - ``regulation`` — ``{id, name, frontmatter, body}`` (AGENT-24 loads it from S3)
  - ``use_case_description`` — free text describing the AI use case
  - ``industry`` / ``geography`` — engagement context

Output: ``{status, regulation_applies, overall, applicability: [{clause, applies, reason}]}``.
"""

from __future__ import annotations

import re
from typing import Any

from .base import Worker
from .worker_04_regulation_finder import _norm_geo

WORKER_ID = "WORKER-13"

_H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_WORD = re.compile(r"[a-z0-9]+")

# Headings that are foundational/scene-setting — they apply whenever the regulation
# itself is in scope, regardless of the specific use case.
_GENERIC_RE = re.compile(
    r"overview|introduction|scope|what this means|implications for engagements"
    r"|key implications|risk tiers|summary",
    re.IGNORECASE,
)

# Common words to ignore when matching the use case against clause text.
_STOPWORDS = frozenset(
    """the a an and or of to for in on with by use using uses used ai system systems
    this that these those it its their our your from at as is are be model models data
    case engagement based over into about across new make build help support tool""".split()
)

# Domain signal groups: if the use case and a clause both light up the same group,
# they are related even without a literal shared token (e.g. "clinical imaging" and a
# "high-risk medical devices" clause both belong to the health/high-risk domain).
_SIGNAL_GROUPS: dict[str, set[str]] = {
    "health": {
        "clinical", "medical", "health", "healthcare", "patient", "phi", "imaging",
        "diagnosis", "diagnostic", "care", "hospital", "ehr", "scribe", "notes", "device",
        "devices", "samd",
    },
    "finance": {
        "credit", "lending", "loan", "loans", "financial", "finance", "bank", "banking",
        "fraud", "scoring", "underwriting", "trading", "investment", "fintech",
    },
    "people": {
        "employment", "hiring", "recruit", "recruiting", "candidate", "worker", "workforce",
        "hr", "resume",
    },
    "biometric": {"biometric", "biometrics", "facial", "face", "fingerprint", "voice"},
    "highrisk": {"critical", "infrastructure", "safety", "autonomous"},
    "transparency": {
        "chatbot", "bot", "assistant", "conversational", "chat", "disclosure", "disclose",
        "synthetic", "transparency", "consumer", "user",
    },
}


def _tokens(text: str) -> set[str]:
    return {w for w in _WORD.findall((text or "").lower()) if len(w) >= 3 and w not in _STOPWORDS}


def _groups(tokens: set[str]) -> set[str]:
    return {g for g, members in _SIGNAL_GROUPS.items() if tokens & members}


class ApplicabilityCheckerWorker(Worker):
    agent_id = WORKER_ID

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.run_tool("check_applicability", lambda _u: self._check(args))

    def _check(self, args: dict[str, Any]) -> dict[str, Any]:
        reg = args.get("regulation") or {}
        fm = reg.get("frontmatter") or {}
        body = str(reg.get("body") or "")
        industry = (args.get("industry") or "").strip().lower()
        geo = _norm_geo(args.get("geography") or "")

        # Use-case signal set: the description plus the engagement industry.
        uc_tokens = _tokens(f"{args.get('use_case_description', '')} {industry}")
        uc_groups = _groups(uc_tokens)

        # Regulation-level gate: geography or industry scope.
        scope = [str(s).lower() for s in (fm.get("industry_scope") or [])]
        geo_match = bool(geo) and str(fm.get("geo") or "").lower() == geo
        industry_match = "cross-industry" in scope or (bool(industry) and industry in scope)
        regulation_applies = geo_match or industry_match

        sections = _sections(body)
        applicability: list[dict[str, Any]] = []
        for heading, text in sections:
            applies, reason = self._clause_verdict(
                heading, text, uc_tokens, uc_groups, regulation_applies
            )
            applicability.append({"clause": heading, "applies": applies, "reason": reason})

        applies_count = sum(1 for a in applicability if a["applies"])
        overall = self._overall(
            str(reg.get("name") or "this regulation"),
            regulation_applies,
            geo_match,
            industry_match,
            applies_count,
            len(applicability),
        )
        return {
            "status": "ok",
            "regulation_applies": regulation_applies,
            "overall": overall,
            "applicability": applicability,
        }

    def _clause_verdict(
        self,
        heading: str,
        text: str,
        uc_tokens: set[str],
        uc_groups: set[str],
        regulation_applies: bool,
    ) -> tuple[bool, str]:
        if _GENERIC_RE.search(heading):
            return True, "Foundational provision that applies whenever this regulation is in scope."

        clause_tokens = _tokens(f"{heading} {text}")
        shared = uc_tokens & clause_tokens
        shared_groups = uc_groups & _groups(clause_tokens)

        if shared_groups:
            domains = ", ".join(sorted(shared_groups))
            return True, f"Relevant to the {domains} nature of the use case."
        if shared:
            terms = ", ".join(sorted(shared)[:4])
            return True, f"The use case touches on {terms}, which this clause governs."
        if regulation_applies and not uc_tokens:
            return True, "Applies by default; no use-case detail was provided to narrow it."
        return False, "No direct connection to the described use case."

    @staticmethod
    def _overall(
        name: str,
        regulation_applies: bool,
        geo_match: bool,
        industry_match: bool,
        applies_count: int,
        total: int,
    ) -> str:
        if not regulation_applies:
            return (
                f"{name} has limited applicability to this use case based on geography and "
                f"industry, but review the in-scope clauses below before ruling it out."
            )
        why = []
        if geo_match:
            why.append("the target geography")
        if industry_match:
            why.append("the industry scope")
        basis = " and ".join(why) or "its broad scope"
        return (
            f"{name} applies to this use case based on {basis}: "
            f"{applies_count} of {total} clauses are relevant. Address the applicable clauses."
        )


def _sections(body: str) -> list[tuple[str, str]]:
    matches = list(_H2.finditer(body))
    out: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        out.append((m.group(1).strip(), body[start:end].strip()))
    return out
