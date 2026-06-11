"""AGENT-29 SOW generator: deterministic skeleton + Sonnet prose + sessions/presign."""

import json

from agents.lambdas.modules.agent_29_sow import SowGeneratorAgent

from .conftest import FakeMetrics, FakeS3

PROSE_JSON = json.dumps(
    {
        "objectives_narrative": "Deliver a production-ready fraud-scoring pilot.",
        "scope_description": "Covers data prep, model training, and a scored API.",
        "acceptance_criteria": ["Model AUC >= target on holdout", "API returns scores < 200ms"],
        "assumptions_extra": ["Client provides labeled training data"],
    }
)


class FakeSonnet:
    def __init__(self, text=PROSE_JSON):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


def _agent(s3=None, sonnet=None):
    return SowGeneratorAgent(
        sessions_bucket="sessions",
        s3=s3 if s3 is not None else FakeS3({}),
        bedrock_client=sonnet or FakeSonnet(),
        metrics_client=FakeMetrics(),
    )


REQ = {
    "op": "generate",
    "display_name": "Dana",
    "client_context": "A fintech scaling fraud detection",
    "engagement_type": "pilot",
    "objectives": ["reduce fraud losses"],
    "scope_items": ["data prep", "model training"],
    "deliverables": ["scored API", "evaluation report"],
    "timeline_weeks": 6,
    "milestones": ["week 2: data ready", "week 6: pilot live"],
    "pricing_model": "fixed",
    "assumptions": ["client SME available"],
}


# --- generate --------------------------------------------------------------
def test_generate_assembles_sow_with_verbatim_inputs():
    s3 = FakeS3({})
    out = _agent(s3=s3).handle(dict(REQ))
    assert out["status"] == "ok"
    md = out["markdown"]
    assert out["title"] == "Statement of Work — Pilot"
    # Structured inputs appear verbatim.
    assert "scored API" in md and "evaluation report" in md
    assert "week 2: data ready" in md and "week 6: pilot live" in md
    assert "data prep" in md and "model training" in md
    assert "6-week engagement" in md
    assert "Pricing model: **fixed**" in md
    # Sonnet prose woven in.
    assert "production-ready fraud-scoring pilot" in md
    assert "Covers data prep, model training" in md
    assert "Model AUC >= target on holdout" in md
    # Section TOC + persisted artifacts + presigned export.
    assert out["sections"][0] == "Objectives" and len(out["sections"]) == 7
    assert out["download_url"]
    sid = out["sow_id"]
    assert f"sow/dana/{sid}.md" in s3.objects and f"sow/dana/{sid}.json" in s3.objects


def test_generate_falls_back_to_skeleton_when_llm_errors():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("sonnet down")

    out = _agent(sonnet=Boom()).handle(dict(REQ))
    assert out["status"] == "ok"
    md = out["markdown"]
    # Structured inputs still verbatim; acceptance derived from deliverables.
    assert "scored API" in md and "week 6: pilot live" in md
    assert "Delivery and sign-off of: scored API" in md
    assert "This engagement will deliver the objectives below." in md  # default narrative


def test_generate_requires_display_name():
    assert _agent().handle({"op": "generate"})["status"] == "error"


# --- get / list ------------------------------------------------------------
def test_get_round_trip_with_fresh_presign():
    s3 = FakeS3({})
    agent = _agent(s3=s3)
    sid = agent.handle(dict(REQ))["sow_id"]
    got = _agent(s3=s3).handle({"op": "get", "sow_id": sid})
    assert got["status"] == "ok"
    assert got["title"] == "Statement of Work — Pilot"
    assert "scored API" in got["markdown"]
    assert got["download_url"]  # re-presigned on get


def test_get_via_id_alias_and_not_found():
    s3 = FakeS3({})
    agent = _agent(s3=s3)
    sid = agent.handle(dict(REQ))["sow_id"]
    assert _agent(s3=s3).handle({"id": sid})["status"] == "ok"
    assert _agent(s3=s3).handle({"op": "get", "sow_id": "sow-nope"})["status"] == "not_found"


def test_list_returns_caller_sows():
    s3 = FakeS3({})
    agent = _agent(s3=s3)
    agent.handle(dict(REQ))
    agent.handle({**REQ, "engagement_type": "build"})
    out = _agent(s3=s3).handle({"op": "list", "display_name": "Dana"})
    assert out["status"] == "ok" and len(out["sows"]) == 2
    assert {s["engagement_type"] for s in out["sows"]} == {"pilot", "build"}
