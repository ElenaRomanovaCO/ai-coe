from agents.lambdas.workers.worker_12_reg_summarizer import RegSummarizerWorker

from .conftest import FakeMetrics

# A reg body shaped like the seeded files: intro paragraph, bolded-bullet clauses,
# and a "What this means for engagements" implications section.
HIPAA_BODY = """# HIPAA and AI Systems

HIPAA governs the use and disclosure of protected health information (PHI). Using AI
over PHI does not change the rules; it raises the stakes for getting them right.

## Key implications for AI

- **Business Associate Agreements (BAAs)** — Any vendor that processes PHI must be
  under a BAA. Confirm coverage before sending PHI to any model endpoint.
- **Minimum necessary** — Only the PHI needed for the task should reach the model.
- **De-identification** — Properly de-identified data falls outside HIPAA.

## What this means for engagements

Default to de-identifying before embedding. Keep a BAA in place for any PHI-touching
service. Scope retrieval to the requesting user's access.
"""

# A reg with prose sections (no bolded bullets) — exercises the heading fallback.
PROSE_BODY = """# NIST AI Risk Management Framework

A voluntary framework that structures AI governance into four functions.

## Govern

Establish the policies and accountability for AI risk.

## Measure

Assess and track AI risks with repeatable methods.
"""


def summarize(args):
    return RegSummarizerWorker(metrics_client=FakeMetrics()).handle(args)


def test_summary_is_intro_paragraph():
    out = summarize({"frontmatter": {"name": "HIPAA"}, "body": HIPAA_BODY})
    assert out["status"] == "ok"
    assert out["summary"].startswith("HIPAA governs the use and disclosure")
    assert "#" not in out["summary"]


def test_key_requirements_from_bold_bullets():
    out = summarize({"frontmatter": {}, "body": HIPAA_BODY})
    labels = [r.split(" — ")[0] for r in out["key_requirements"]]
    assert "Business Associate Agreements (BAAs)" in labels
    assert "Minimum necessary" in labels
    # The descriptions are trimmed to the first sentence.
    baa = next(r for r in out["key_requirements"] if r.startswith("Business Associate"))
    assert baa.endswith("BAA.")


def test_sector_implications_split_into_points():
    out = summarize({"frontmatter": {}, "body": HIPAA_BODY})
    assert len(out["sector_implications"]) >= 2
    assert any("BAA" in p for p in out["sector_implications"])
    # The implications section is not duplicated into key requirements.
    assert all("Default to de-identifying" not in r for r in out["key_requirements"])


def test_prose_reg_falls_back_to_headings():
    out = summarize({"frontmatter": {}, "body": PROSE_BODY})
    assert out["key_requirements"] == ["Govern", "Measure"]


def test_empty_body_is_safe():
    out = summarize({"frontmatter": {"name": "Empty Reg"}, "body": ""})
    assert out["status"] == "ok"
    assert out["summary"] == "Empty Reg"
    assert out["key_requirements"] == []
    assert out["sector_implications"] == []
