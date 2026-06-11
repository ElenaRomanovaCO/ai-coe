"""AGENT-17 project health: register / post_update (analyze) / get / list_portfolio.

Vault + sessions writes run against in-memory S3; the Titan embed and S3 Vectors
pattern search and the Sonnet analysis are faked.
"""

import json

from agents.lambdas.modules.agent_17_health import ProjectHealthAgent

from .conftest import FakeBedrockEmbed, FakeMetrics, FakeS3, FakeS3Vectors

# A curated asset the pattern search can return as a best-practice reference.
ASSET_MD = """---
id: solution-pattern-rag-eval
title: RAG Evaluation Pattern
type: solution-pattern
industry: cross-industry
ai_stage: 3
tags: ["rag", "evals"]
updated_at: "2026-05-01"
---

# RAG Evaluation Pattern

Evaluate retrieval quality before scaling.
"""

ANALYSIS_JSON = json.dumps(
    {
        "flags": [
            {
                "severity": "high",
                "description": "Scope expanded without re-baselining the plan.",
                "remediation": "Re-baseline scope and timeline with the client.",
                "reference_ids": ["solution-pattern-rag-eval"],
            }
        ],
        "risk_score": 72,
        "summary": "Scope creep is the main risk.",
    }
)


class FakeSonnet:
    def __init__(self, text=ANALYSIS_JSON):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


def _vec(key, content_type="assets", idx=0):
    return {
        "key": f"{key}#{idx}",
        "metadata": {"file_path": key, "content_type": content_type, "chunk_index": idx},
    }


def _agent(s3=None, sonnet=None, vectors=None):
    return ProjectHealthAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=s3 if s3 is not None else FakeS3({"assets/x/solution-pattern-rag-eval.md": ASSET_MD}),
        bedrock=FakeBedrockEmbed(),
        bedrock_client=sonnet or FakeSonnet(),
        s3vectors=FakeS3Vectors(vectors if vectors is not None else [_vec(
            "assets/x/solution-pattern-rag-eval.md"
        )]),
        metrics_client=FakeMetrics(),
    )


REG = {
    "op": "register",
    "display_name": "Dana",
    "name": "Fintech RAG Platform",
    "industry": "financial-services",
    "ai_stage": 2,
    "use_cases": ["doc Q&A", "fraud triage"],
    "start_date": "2026-05-01",
}


def _register(agent):
    return agent.handle(dict(REG))["engagement"]["engagement_id"]


# --- register --------------------------------------------------------------
def test_register_creates_engagement_green():
    s3 = FakeS3({"assets/x/solution-pattern-rag-eval.md": ASSET_MD})
    agent = _agent(s3=s3)
    out = agent.handle(dict(REG))
    assert out["status"] == "ok"
    eng = out["engagement"]
    assert eng["engagement_id"].startswith("eng-")
    assert eng["risk_score"] == 0 and eng["band"] == "green"
    # State JSON in sessions + meta.md/health.md in vault (generated-tagged).
    eid = eng["engagement_id"]
    assert f"engagements/dana/{eid}.json" in s3.objects
    meta = s3.objects[f"engagements/dana/{eid}/meta.md"]
    assert "content_type: engagement" in meta and "generated: true" in meta
    assert f"engagements/dana/{eid}/health.md" in s3.objects


def test_register_requires_name():
    out = _agent().handle({"op": "register", "display_name": "Dana"})
    assert out["status"] == "error"


# --- post_update + analyze -------------------------------------------------
def test_post_update_analyzes_and_persists_flags():
    s3 = FakeS3({"assets/x/solution-pattern-rag-eval.md": ASSET_MD})
    agent = _agent(s3=s3)
    eid = _register(agent)
    out = agent.handle(
        {
            "op": "update",
            "engagement_id": eid,
            "update_text": "We added two more use cases this week beyond the original scope.",
            "update_type": "scope-change",
        }
    )
    assert out["status"] == "ok"
    assert out["risk_score"] == 72 and out["band"] == "red"
    assert out["flags"][0]["severity"] == "high"
    # Reference resolved from the vector hit.
    assert out["flags"][0]["references"][0]["id"] == "solution-pattern-rag-eval"
    # Update markdown written to the vault, generated-tagged.
    upd_keys = [
        k for k in s3.objects
        if k.startswith(f"engagements/dana/{eid}/updates/") and k.endswith(".md")
    ]
    assert len(upd_keys) == 1
    assert "generated: true" in s3.objects[upd_keys[0]]


def test_post_update_updates_portfolio_band():
    agent = _agent()
    eid = _register(agent)
    agent.handle({"op": "update", "engagement_id": eid, "update_text": "scope grew",
                  "update_type": "scope-change"})
    port = agent.handle({"op": "list", "display_name": "Dana"})
    eng = next(e for e in port["engagements"] if e["engagement_id"] == eid)
    assert eng["risk_score"] == 72 and eng["band"] == "red"
    assert eng["update_count"] == 1 and eng["open_flags"] == 1


def test_post_update_falls_back_when_llm_errors():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("sonnet down")

    agent = _agent(sonnet=Boom())
    eid = _register(agent)
    out = agent.handle({"op": "update", "engagement_id": eid,
                        "update_text": "blocked on data access", "update_type": "blocker"})
    assert out["status"] == "ok"
    # Heuristic: blocker -> baseline 70 (red) + a high flag.
    assert out["risk_score"] == 70 and out["band"] == "red"
    assert out["flags"][0]["severity"] == "high"


def test_post_update_unknown_engagement():
    out = _agent().handle({"op": "update", "engagement_id": "eng-nope", "update_text": "x"})
    assert out["status"] == "not_found"


def test_post_update_requires_text():
    agent = _agent()
    eid = _register(agent)
    out = agent.handle({"op": "update", "engagement_id": eid})
    assert out["status"] == "error"


# --- get / list ------------------------------------------------------------
def test_get_returns_timeline_newest_first():
    agent = _agent()
    eid = _register(agent)
    agent.handle({"op": "update", "engagement_id": eid, "update_text": "kickoff done",
                  "update_type": "status"})
    agent.handle({"op": "update", "engagement_id": eid, "update_text": "scope grew",
                  "update_type": "scope-change"})
    out = agent.handle({"op": "get", "engagement_id": eid})
    assert out["status"] == "ok"
    updates = out["engagement"]["updates"]
    assert len(updates) == 2
    assert updates[0]["update_type"] == "scope-change"  # newest first
    assert out["engagement"]["use_cases"] == ["doc Q&A", "fraud triage"]


def test_get_via_id_alias_and_inferred_op():
    agent = _agent()
    eid = _register(agent)
    out = agent.handle({"id": eid})
    assert out["status"] == "ok" and out["engagement"]["engagement_id"] == eid


def test_list_portfolio_sorted_riskiest_first():
    agent = _agent()
    e1 = _register(agent)
    agent.handle({**REG, "name": "Calm Project"})  # a second, untouched (low-risk) engagement
    # e1 gets a risky update; it should rank above the untouched one.
    agent.handle({"op": "update", "engagement_id": e1, "update_text": "scope grew",
                  "update_type": "scope-change"})
    out = agent.handle({"op": "list", "display_name": "Dana"})
    ids = [e["engagement_id"] for e in out["engagements"]]
    assert ids[0] == e1  # riskiest first


def test_list_requires_display_name():
    out = _agent().handle({"op": "list"})
    assert out["status"] == "error"
