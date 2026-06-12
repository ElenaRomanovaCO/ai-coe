"""AGENT-21 benchmark: get / export. Deterministic peer distribution from the seed +
one (faked) Haiku narrative; reads the assessment's sessions state by id."""

import json

from agents.lambdas.modules.agent_21_benchmark import BenchmarkAgent

from .conftest import FakeMetrics, FakeS3

SEED = json.dumps({
    "industries": {
        "healthcare": {"0": 10, "1": 25, "2": 30, "3": 20, "4": 10, "5": 5},
        "cross-industry": {"0": 10, "1": 22, "2": 28, "3": 22, "4": 13, "5": 5},
    }
})


def _assessment(aid, stage, industry, display_name="Dana"):
    return json.dumps({
        "assessment_id": aid,
        "display_name": display_name,
        "industry": industry,
        "status": "complete",
        "result": {"assessment_id": aid, "stage": stage, "rationale": "…"},
    })


def _store(extra=None):
    objs = {
        "benchmarks/_seed_peer_distribution.json": SEED,
        "assessments/dana/assess-hc2.json": _assessment("assess-hc2", 2, "healthcare"),
        "assessments/dana/assess-energy.json": _assessment("assess-energy", 3, "energy"),
    }
    objs.update(extra or {})
    return FakeS3(objs)


class FakeHaiku:
    def __init__(self, text="This healthcare client is in line with peers at stage 2."):
        self.text = text

    def converse(self, **kwargs):
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


def _agent(s3=None, haiku=None):
    return BenchmarkAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=s3 if s3 is not None else _store(),
        bedrock_client=haiku or FakeHaiku(),
        metrics_client=FakeMetrics(),
    )


# --- get -------------------------------------------------------------------
def test_get_returns_distribution_and_context():
    out = _agent().handle({"op": "get", "assessment_id": "assess-hc2"})
    assert out["status"] == "ok"
    assert out["client_stage"] == 2
    assert out["industry"] == "healthcare"
    assert out["peer_distribution"] == {0: 10.0, 1: 25.0, 2: 30.0, 3: 20.0, 4: 10.0, 5: 5.0}
    assert out["common_next_moves"]  # stage-2 moves
    assert out["typical_use_cases_at_stage"][2]
    assert out["narrative"]
    assert out["markdown"].startswith("---\ncontent_type: benchmark\ngenerated: true")
    assert "← client" in out["markdown"]


def test_get_unknown_industry_falls_back_to_cross_industry():
    # energy isn't in the seed -> cross-industry distribution.
    out = _agent().handle({"op": "get", "assessment_id": "assess-energy"})
    assert out["status"] == "ok"
    assert out["peer_distribution"][3] == 22.0  # cross-industry stage 3


def test_get_via_id_alias_and_inferred_op():
    out = _agent().handle({"id": "assess-hc2"})
    assert out["status"] == "ok" and out["client_stage"] == 2


def test_get_narrative_fallback_on_llm_error():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("haiku down")

    out = _agent(haiku=Boom()).handle({"op": "get", "assessment_id": "assess-hc2"})
    assert out["status"] == "ok"
    # Deterministic fallback references the peer cluster (healthcare peaks at stage 2).
    assert "stage 2" in out["narrative"]


def test_get_unknown_assessment_not_found():
    out = _agent().handle({"op": "get", "assessment_id": "assess-nope"})
    assert out["status"] == "not_found"


def test_get_requires_assessment_id():
    out = _agent().handle({"op": "get"})
    assert out["status"] == "error"


# --- export ----------------------------------------------------------------
def test_export_writes_generated_slide_to_vault():
    s3 = _store()
    out = _agent(s3=s3).handle({"op": "export", "assessment_id": "assess-hc2"})
    assert out["status"] == "ok"
    key = out["vault_file_path"]
    assert key.startswith("benchmarks/dana/") and key.endswith(".md")
    md = s3.objects[key]
    assert "content_type: benchmark" in md and "generated: true" in md
    assert "Peer distribution" in md
