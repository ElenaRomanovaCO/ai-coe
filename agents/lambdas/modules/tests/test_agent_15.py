"""AGENT-15 retrospective: write_retro (+ insight extraction) / get / list.

Vault + sessions writes run against in-memory S3; the Sonnet extraction call is faked.
Also checks that the orchestrator maps the insights/ folder so extracted insights are
chat-retrievable (FR-055).
"""

import json

from agents.lambdas.modules.agent_15_retro import RetrospectiveAgent

from .conftest import FakeMetrics, FakeS3

INSIGHTS_JSON = json.dumps(
    {
        "insights": [
            {
                "type": "pattern",
                "statement": "Validate retrieval quality before scaling RAG.",
                "evidence": "Skipping eval caused rework mid-engagement.",
                "asset_id": "solution-pattern-rag-eval",
            },
            {
                "type": "risk",
                "statement": "Scope creep without re-baselining erodes delivery.",
                "evidence": "Use cases were added late with no timeline change.",
                "asset_id": "not-a-real-pattern",
            },
        ]
    }
)


class FakeSonnet:
    def __init__(self, text=INSIGHTS_JSON):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


def _agent(s3=None, sonnet=None):
    return RetrospectiveAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=s3 if s3 is not None else FakeS3({}),
        bedrock_client=sonnet or FakeSonnet(),
        metrics_client=FakeMetrics(),
    )


RETRO = {
    "op": "write",
    "display_name": "Dana",
    "engagement_id": "eng-123",
    "use_cases_attempted": ["doc Q&A"],
    "patterns_used": ["solution-pattern-rag-eval"],
    "what_worked": "Strong retrieval grounding.",
    "what_failed": "Late scope additions caused rework.",
    "tools_recommended": ["titan-embed"],
    "tools_not_recommended": ["legacy-keyword-search"],
    "stage_reassessment": 3,
}


# --- write -----------------------------------------------------------------
def test_write_persists_retro_and_extracts_insights():
    s3 = FakeS3({})
    out = _agent(s3=s3).handle(dict(RETRO))
    assert out["status"] == "ok"
    rid = out["retro"]["retro_id"]
    assert rid.startswith("retro-")
    assert len(out["insights"]) == 2
    # Retro markdown is generated-flagged (scoped out of chat); state JSON in sessions.
    retro_md = s3.objects[f"retros/dana/{rid}.md"]
    assert "content_type: retro" in retro_md and "generated: true" in retro_md
    assert f"retros/dana/{rid}.json" in s3.objects


def test_insights_are_searchable_not_generated():
    s3 = FakeS3({})
    _agent(s3=s3).handle(dict(RETRO))
    ins_keys = [k for k in s3.objects if k.startswith("insights/") and k.endswith(".md")]
    assert len(ins_keys) == 2
    for k in ins_keys:
        md = s3.objects[k]
        assert "content_type: insight" in md
        assert "generated: true" not in md  # reusable KB → retrievable by chat


def test_asset_link_only_for_real_patterns():
    out = _agent().handle(dict(RETRO))
    by_type = {i["type"]: i for i in out["insights"]}
    assert by_type["pattern"]["asset_link"] == "solution-pattern-rag-eval"  # in patterns_used
    assert by_type["risk"]["asset_link"] is None  # "not-a-real-pattern" dropped


def test_write_requires_engagement_and_name():
    assert _agent().handle({"op": "write", "display_name": "Dana"})["status"] == "error"
    assert _agent().handle({"op": "write", "engagement_id": "eng-1"})["status"] == "error"


def test_write_falls_back_when_llm_errors():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("sonnet down")

    out = _agent(sonnet=Boom()).handle(dict(RETRO))
    assert out["status"] == "ok"
    # Deterministic fallback derives insights from what_worked / what_failed / tools.
    assert len(out["insights"]) >= 2
    assert any(i["type"] == "risk" for i in out["insights"])


# --- get / list ------------------------------------------------------------
def test_get_round_trip():
    s3 = FakeS3({})
    agent = _agent(s3=s3)
    rid = agent.handle(dict(RETRO))["retro"]["retro_id"]
    got = _agent(s3=s3).handle({"op": "get", "retro_id": rid})
    assert got["status"] == "ok"
    assert got["retro"]["engagement_id"] == "eng-123"
    assert got["retro"]["what_worked"].startswith("Strong retrieval")
    assert len(got["insights"]) == 2


def test_get_via_id_alias():
    s3 = FakeS3({})
    agent = _agent(s3=s3)
    rid = agent.handle(dict(RETRO))["retro"]["retro_id"]
    got = _agent(s3=s3).handle({"id": rid})
    assert got["status"] == "ok" and got["retro"]["retro_id"] == rid


def test_get_unknown_not_found():
    out = _agent().handle({"op": "get", "retro_id": "retro-nope"})
    assert out["status"] == "not_found"


def test_list_returns_caller_retros():
    s3 = FakeS3({})
    agent = _agent(s3=s3)
    agent.handle(dict(RETRO))
    out = _agent(s3=s3).handle({"op": "list", "display_name": "Dana"})
    assert out["status"] == "ok" and len(out["retros"]) == 1
    assert out["retros"][0]["insight_count"] == 2


# --- orchestrator wiring (FR-055: insights retrievable by chat) ------------
def test_orchestrator_maps_insights_folder():
    from agents.orchestrator.models import CONTENT_TYPE_FROM_DIR

    assert CONTENT_TYPE_FROM_DIR.get("insights") == "insight"
