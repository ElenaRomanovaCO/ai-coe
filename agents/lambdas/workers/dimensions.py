"""Shared assessment constants: the 6 maturity dimensions, the question bank, and
the deterministic per-answer scoring rule used by WORKER-01 and WORKER-02.
"""

from __future__ import annotations

# The 6 dimensions, in the fixed order questions are first asked.
DIMENSIONS: list[str] = [
    "data_readiness",
    "org_culture",
    "ai_tooling",
    "use_case_clarity",
    "governance",
    "budget_sponsorship",
]

# Primary + one follow-up question per dimension (friendly, plain language).
QUESTION_BANK: dict[str, dict[str, str]] = {
    "data_readiness": {
        "primary": "How would you describe the state of your data — centralized, clean, and "
        "accessible, or siloed and gathered manually?",
        "followup": "Do you have established data pipelines, or is data pulled together ad hoc "
        "for each project?",
    },
    "org_culture": {
        "primary": "How does your organization view AI today — skeptical, curious, or actively "
        "investing?",
        "followup": "Do teams have the time and leadership support to experiment with AI?",
    },
    "ai_tooling": {
        "primary": "What AI/ML tooling is in place — none yet, a few pilots, or production "
        "systems?",
        "followup": "Are any models deployed and monitored in production, or is it still "
        "experimental?",
    },
    "use_case_clarity": {
        "primary": "How clearly defined are your target AI use cases — vague ideas, a shortlist, "
        "or a prioritized backlog with expected ROI?",
        "followup": "Have you quantified the expected value of your top use cases?",
    },
    "governance": {
        "primary": "What AI governance exists — none, informal guidelines, or formal policies "
        "with review?",
        "followup": "Is there a process for reviewing AI risk, bias, or compliance before launch?",
    },
    "budget_sponsorship": {
        "primary": "Is there executive sponsorship and budget for AI — none, exploratory, or "
        "committed funding?",
        "followup": "Do you have a named executive sponsor and an allocated AI budget?",
    },
}

# Keyword signals for the deterministic 0-5 per-answer score. Lowercased substring
# match. STRONG raises the score, WEAK lowers it from a baseline of 2.
_STRONG = (
    "production", "deployed", "monitored", "centralized", "clean", "automated", "pipeline",
    "pipelines", "formal", "policies", "policy", "committed", "sponsor", "budget", "prioritized",
    "roi", "established", "mature", "actively", "investing", "governance", "strong", "robust",
    "scaled", "enterprise", "yes",
)
_WEAK = (
    "none", "no ", "not ", "n't", "manual", "ad hoc", "ad-hoc", "siloed", "skeptical", "vague",
    "experimental", "pilot", "exploring", "unsure", "not sure", "informal", "limited", "nothing",
    "early", "minimal", "lacking", "struggle", "legacy", "scattered",
)


def score_answer(answer: str) -> int:
    """Deterministic 0-5 maturity signal for a single free-text answer."""
    text = f" {(answer or '').lower()} "
    strong = sum(1 for k in _STRONG if k in text)
    weak = sum(1 for k in _WEAK if k in text)
    return max(0, min(5, 2 + strong - weak))


def is_weak_answer(answer: str) -> bool:
    """Whether an answer signals low maturity (warrants a follow-up / is a weak dimension)."""
    return score_answer(answer) <= 2
