import json

from agents.lambdas.modules import router
from agents.lambdas.modules.agent_16_dashboard import DashboardAgent

from .conftest import (
    ASSET_KEYS,
    FakeBedrockEmbed,
    FakeMetrics,
    FakeS3,
    FakeS3Vectors,
    vec,
)

CLINICAL = "reference-arch-clinical-notes-rag"
CLINICAL_PATH = "assets/healthcare/2/reference-arch-clinical-notes-rag.md"
FRAUD = "solution-pattern-fraud-scoring-agent"
FRAUD_PATH = "assets/financial-services/3/solution-pattern-fraud-scoring-agent.md"


def _objects(*, saved=None, sessions=None):
    objs = dict(ASSET_KEYS)
    if saved is not None:
        objs["users/alex.json"] = json.dumps(
            {"display_name": "Alex", "saved": saved, "ratings": {}, "flags": []}
        )
    for sid, doc in (sessions or {}).items():
        objs[f"sessions/alex/{sid}.json"] = json.dumps(doc)
    return objs


def make_dashboard(*, saved=None, sessions=None, vectors=None, embeddings=None):
    s3 = FakeS3(_objects(saved=saved, sessions=sessions))
    s3v = FakeS3Vectors(vectors=vectors or [], embeddings=embeddings or {})
    return DashboardAgent(
        vault_bucket="vault-bucket",
        sessions_bucket="sessions-bucket",
        s3=s3,
        s3vectors=s3v,
        bedrock=FakeBedrockEmbed(),
        metrics_client=FakeMetrics(),
    )


def test_registered():
    assert router.REGISTRY.get("AGENT-16") is DashboardAgent


def test_requires_display_name():
    assert make_dashboard().handle({"op": "summary"})["status"] == "error"


def test_read_profile_op():
    agent = make_dashboard(saved=[CLINICAL])
    out = agent.handle({"op": "read_profile", "display_name": "Alex"})
    assert out["status"] == "ok"
    assert out["profile"]["saved"] == [CLINICAL]


def test_summary_assembles_all_sections():
    sessions = {
        "s1": {"session_id": "s1", "updated_at": "2026-06-08T09:00:00Z",
               "turns": [{"user_message": "older question", "assistant_message": "a"}]},
        "s2": {"session_id": "s2", "updated_at": "2026-06-08T11:00:00Z",
               "turns": [{"user_message": "newest question", "assistant_message": "b"}]},
    }
    agent = make_dashboard(
        saved=[CLINICAL],
        sessions=sessions,
        embeddings={f"{CLINICAL_PATH}#0": [0.1] * 1024},
        vectors=[vec(CLINICAL_PATH), vec(FRAUD_PATH)],  # clinical excluded (saved) -> fraud rec
    )
    out = agent.handle({"op": "summary", "display_name": "Alex"})
    assert out["status"] == "ok"
    assert [a["id"] for a in out["saved_assets"]] == [CLINICAL]
    assert [a["id"] for a in out["recommendations"]] == [FRAUD]  # saved one filtered out
    # Recent chats sorted newest-first; last_session_id points at it.
    assert [c["session_id"] for c in out["recent_chats"]] == ["s2", "s1"]
    assert out["recent_chats"][0]["snippet"] == "newest question"
    assert out["last_session_id"] == "s2"
    # Placeholders empty in Wave 1.
    assert out["active_engagements"] == []
    assert out["learning_progress"] == []


def test_recommend_cold_start_returns_sample():
    # No profile/saved activity -> fall back to most-tagged assets (no vectors used).
    agent = make_dashboard()
    out = agent.handle({"op": "recommend", "display_name": "Alex", "top_k": 2})
    assert out["status"] == "ok"
    assert len(out["assets"]) == 2  # both seed assets returned as a sample


def test_recommend_excludes_saved():
    agent = make_dashboard(
        saved=[CLINICAL],
        embeddings={f"{CLINICAL_PATH}#0": [0.2] * 1024},
        vectors=[vec(CLINICAL_PATH), vec(FRAUD_PATH)],
    )
    out = agent.handle({"op": "recommend", "display_name": "Alex"})
    ids = [a["id"] for a in out["assets"]]
    assert CLINICAL not in ids
    assert FRAUD in ids


def test_list_recent_chats_op_limit():
    sessions = {
        f"s{i}": {"session_id": f"s{i}", "updated_at": f"2026-06-0{i}T10:00:00Z", "turns": []}
        for i in range(1, 6)
    }
    agent = make_dashboard(sessions=sessions)
    out = agent.handle({"op": "list_recent_chats", "display_name": "Alex", "limit": 3})
    assert out["status"] == "ok"
    assert len(out["chats"]) == 3
    assert out["chats"][0]["session_id"] == "s5"  # newest first


def test_summary_empty_user():
    # Brand-new user: no saved, no sessions -> cold-start recs, empty chats, null session.
    agent = make_dashboard()
    out = agent.handle({"display_name": "Newbie"})
    assert out["status"] == "ok"
    assert out["saved_assets"] == []
    assert out["recent_chats"] == []
    assert out["last_session_id"] is None
    assert len(out["recommendations"]) >= 1
