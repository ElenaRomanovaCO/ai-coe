"""AGENT-14 client report: generate (skeleton + Sonnet prose) / get / list / update_section.

Composes the real AGENT-21 BenchmarkAgent in-process, so a benchmark seed + a completed
assessment state are planted in the (bucket-agnostic) FakeS3.
"""

import json

from agents.lambdas.modules import router
from agents.lambdas.modules.agent_14_report import ReportAgent

from .conftest import FakeMetrics, FakeS3

REPORT_JSON = json.dumps(
    {
        "executive_summary": "The organization is at stage 2 and building momentum.",
        "stage_placement": "Stage 2 reflects a working pilot with gaps in strategy.",
        "what_this_means": "Closing the strategy gap is the fastest path to stage 3.",
        "benchmark_paragraph": "You sit ahead of most peers at this stage.",
        "top_next_steps": ["Promote the pilot to production", "Stand up LLMOps monitoring"],
        "recommended_use_cases": ["Document Q&A", "Internal copilot"],
    }
)

ASSESSMENT = {
    "assessment_id": "assess-abc123",
    "display_name": "Dana",
    "client_context": "A regional hospital network scaling clinical AI",
    "industry": "healthcare",
    "status": "complete",
    "created_at": "2026-06-10T12:00:00Z",
    "result": {
        "assessment_id": "assess-abc123",
        "stage": 2,
        "rationale": "Strong data foundations but no formal strategy or governance.",
        "dimension_scores": {
            "strategy": 1,
            "data": 4,
            "talent": 2,
            "governance": 1,
            "technology": 3,
            "adoption": 2,
        },
        "recommendations": [
            {"title": "Clinical Notes RAG", "id": "ref-arch-clinical-notes-rag", "file_path": "a"}
        ],
        "vault_file_path": "assessments/dana/2026.md",
    },
}

SEED = {
    "industries": {
        "healthcare": {"0": 10, "1": 25, "2": 30, "3": 20, "4": 10, "5": 5},
        "cross-industry": {"0": 20, "1": 30, "2": 25, "3": 15, "4": 7, "5": 3},
    }
}


class FakeSonnet:
    def __init__(self, text=REPORT_JSON):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


def _seeded_s3():
    return FakeS3(
        {
            "assessments/dana/assess-abc123.json": json.dumps(ASSESSMENT),
            "benchmarks/_seed_peer_distribution.json": json.dumps(SEED),
        }
    )


def _agent(s3=None, sonnet=None):
    return ReportAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=s3 if s3 is not None else _seeded_s3(),
        bedrock_client=sonnet or FakeSonnet(),
        metrics_client=FakeMetrics(),
    )


GEN = {"op": "generate", "assessment_id": "assess-abc123"}


# --- generate --------------------------------------------------------------
def test_generate_builds_six_sections_with_prose_and_persists():
    s3 = _seeded_s3()
    out = _agent(s3=s3).handle(dict(GEN))
    assert out["status"] == "ok"
    assert out["stage"] == 2 and out["industry"] == "healthcare"
    assert len(out["section_order"]) == 6
    secs = out["sections"]
    # Sonnet prose woven into the structured sections.
    assert secs["executive_summary"] == "The organization is at stage 2 and building momentum."
    assert secs["top_next_steps"] == [
        "Promote the pilot to production",
        "Stand up LLMOps monitoring",
    ]
    assert secs["recommended_use_cases"] == ["Document Q&A", "Internal copilot"]
    # Markdown renders all six headings + a next step.
    md = out["markdown"]
    assert "## Executive Summary" in md and "## Recommended Use Cases" in md
    assert "Promote the pilot to production" in md
    # Persisted to the SESSIONS bucket (never vault).
    rid = out["report_id"]
    assert f"reports/dana/{rid}.md" in s3.objects and f"reports/dana/{rid}.json" in s3.objects


def test_generate_falls_back_to_deterministic_sections_when_llm_errors():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("sonnet down")

    out = _agent(sonnet=Boom()).handle(dict(GEN))
    assert out["status"] == "ok"
    secs = out["sections"]
    # Deterministic exec summary mentions industry + stage.
    assert "healthcare" in secs["executive_summary"] and "stage 2" in secs["executive_summary"]
    # Next steps fall back to the stage-2 common next moves from the benchmark.
    assert "Promote a pilot to production" in secs["top_next_steps"]
    # What-this-means cites the weak (strategy/governance) dimensions.
    assert "governance" in secs["what_this_means"] and "strategy" in secs["what_this_means"]


def test_generate_requires_complete_assessment():
    s3 = FakeS3(
        {
            "assessments/dana/assess-wip.json": json.dumps(
                {**ASSESSMENT, "assessment_id": "assess-wip", "status": "in_progress",
                 "result": None}
            ),
            "benchmarks/_seed_peer_distribution.json": json.dumps(SEED),
        }
    )
    out = _agent(s3=s3).handle({"op": "generate", "assessment_id": "assess-wip"})
    assert out["status"] == "error"


def test_generate_missing_assessment_is_not_found():
    out = _agent().handle({"op": "generate", "assessment_id": "assess-nope"})
    assert out["status"] == "not_found"


def test_generate_requires_assessment_id():
    assert _agent().handle({"op": "generate"})["status"] == "error"


# --- update_section (FR-059 persistence) -----------------------------------
def test_update_section_rewrites_prose_and_persists():
    s3 = _seeded_s3()
    agent = _agent(s3=s3)
    rid = agent.handle(dict(GEN))["report_id"]
    upd = _agent(s3=s3).handle(
        {
            "op": "update_section",
            "report_id": rid,
            "section": "executive_summary",
            "content": "Hand-edited executive summary.",
        }
    )
    assert upd["status"] == "ok"
    assert upd["sections"]["executive_summary"] == "Hand-edited executive summary."
    assert "Hand-edited executive summary." in upd["markdown"]
    # Persisted: a fresh get reflects the edit.
    got = _agent(s3=s3).handle({"op": "get", "report_id": rid})
    assert got["sections"]["executive_summary"] == "Hand-edited executive summary."


def test_update_list_section_accepts_list_and_text():
    s3 = _seeded_s3()
    agent = _agent(s3=s3)
    rid = agent.handle(dict(GEN))["report_id"]
    upd = _agent(s3=s3).handle(
        {
            "op": "update_section",
            "report_id": rid,
            "section": "top_next_steps",
            "content": ["Only step A", "Only step B"],
        }
    )
    assert upd["sections"]["top_next_steps"] == ["Only step A", "Only step B"]
    # Newline-delimited text also normalizes to a list.
    upd2 = _agent(s3=s3).handle(
        {
            "op": "update_section",
            "report_id": rid,
            "section": "recommended_use_cases",
            "content": "Case 1\nCase 2\n",
        }
    )
    assert upd2["sections"]["recommended_use_cases"] == ["Case 1", "Case 2"]


def test_update_unknown_section_errors():
    s3 = _seeded_s3()
    rid = _agent(s3=s3).handle(dict(GEN))["report_id"]
    out = _agent(s3=s3).handle(
        {"op": "update_section", "report_id": rid, "section": "nope", "content": "x"}
    )
    assert out["status"] == "error"


# --- get / list ------------------------------------------------------------
def test_get_round_trip_and_id_alias():
    s3 = _seeded_s3()
    rid = _agent(s3=s3).handle(dict(GEN))["report_id"]
    got = _agent(s3=s3).handle({"id": rid})
    assert got["status"] == "ok" and got["report_id"] == rid
    assert _agent(s3=s3).handle({"op": "get", "report_id": "report-nope"})["status"] == "not_found"


def test_list_returns_caller_reports():
    s3 = _seeded_s3()
    agent = _agent(s3=s3)
    agent.handle(dict(GEN))
    agent.handle(dict(GEN))
    out = _agent(s3=s3).handle({"op": "list", "display_name": "Dana"})
    assert out["status"] == "ok" and len(out["reports"]) == 2
    assert all(r["assessment_id"] == "assess-abc123" for r in out["reports"])


def test_router_registration():
    assert router.REGISTRY.get("AGENT-14") is ReportAgent
