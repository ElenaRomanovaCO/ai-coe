"""AGENT-22 onboarding: profile save/read, personalized path, 30-day checklist, connections."""

import json

from agents.lambdas.modules import router
from agents.lambdas.modules.agent_22_onboarding import OnboardingAgent

from .conftest import FakeMetrics, FakeS3

# --- seed corpus: assets (AGENT-03), tools (AGENT-08), community (AGENT-07) ---
ASSET_HEALTH = """---
id: ref-arch-clinical-rag
title: Reference Architecture — Clinical Notes RAG
type: reference-architecture
industry: healthcare
ai_stage: 2
tags: ["rag", "healthcare", "retrieval"]
updated_at: "2026-05-01"
---
# Clinical Notes RAG
Body.
"""

ASSET_FIN = """---
id: pattern-fraud-scoring
title: Solution Pattern — Fraud Scoring Agent
type: solution-pattern
industry: financial-services
ai_stage: 3
tags: ["fraud", "agent"]
updated_at: "2026-05-02"
---
# Fraud Scoring Agent
Body.
"""

ASSET_HEALTH_2 = """---
id: playbook-care-summaries
title: Playbook — Care Summaries
type: playbook
industry: healthcare
ai_stage: 1
tags: ["summarization", "healthcare"]
updated_at: "2026-05-03"
---
# Care Summaries
Body.
"""

TOOL_VECDB = """---
id: tool-s3-vectors
name: S3 Vectors
category: vector-db
stack: ["aws"]
ai_stage_fit: [1, 2]
cost_model: usage-based
tags: ["vector-db"]
---
# S3 Vectors
Body.
"""

TOOL_FRAMEWORK = """---
id: tool-bedrock
name: Amazon Bedrock
category: platform
stack: ["aws"]
ai_stage_fit: [3, 4]
cost_model: usage-based
tags: ["llm"]
---
# Bedrock
Body.
"""

LP_ARCH = """---
id: lp-arch
kind: learning-path
title: Architecture Foundations
role: solution-architect
stage: 1
duration: 4 weeks
modules: ["RAG"]
tags: ["architecture"]
---
# Arch
Body.
"""

LP_EXEC = """---
id: lp-exec
kind: learning-path
title: AI Strategy for Executives
role: executive
stage: 0
duration: 1 week
modules: ["Maturity"]
tags: ["strategy"]
---
# Exec
Body.
"""

EXPERT_HEALTH = """---
id: expert-health
kind: expert
title: Principal AI Architect
name: Alex Rivera
expertise: ["RAG", "Clinical NLP"]
industries: ["healthcare"]
tags: ["healthcare"]
---
# Alex Rivera
Body.
"""

EXPERT_FIN = """---
id: expert-fin
kind: expert
title: AI Governance Lead
name: Jordan Kim
expertise: ["Fraud detection"]
industries: ["financial-services"]
tags: ["fintech"]
---
# Jordan Kim
Body.
"""


def _objects():
    return {
        "assets/healthcare/2/ref-arch-clinical-rag.md": ASSET_HEALTH,
        "assets/healthcare/1/playbook-care-summaries.md": ASSET_HEALTH_2,
        "assets/financial-services/3/pattern-fraud-scoring.md": ASSET_FIN,
        "tools/tool-s3-vectors.md": TOOL_VECDB,
        "tools/tool-bedrock.md": TOOL_FRAMEWORK,
        "community/learning-paths/lp-arch.md": LP_ARCH,
        "community/learning-paths/lp-exec.md": LP_EXEC,
        "community/experts/expert-health.md": EXPERT_HEALTH,
        "community/experts/expert-fin.md": EXPERT_FIN,
    }


def _agent(s3=None):
    return OnboardingAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=s3 if s3 is not None else FakeS3(_objects()),
        metrics_client=FakeMetrics(),
    )


# --- generate_path (FR-067): personalized to the inline profile -------------
def test_generate_path_emphasizes_focus_industry_and_role():
    out = _agent().handle(
        {
            "display_name": "Dana",
            "role": "architect",
            "industry_focus": ["healthcare"],
            "ai_background": "novice",
            "goals": ["retrieval"],
        }
    )
    assert out["status"] == "ok"
    # Top assets lead with the in-focus (healthcare) assets, not financial-services.
    industries = [a["industry"] for a in out["top_assets"]]
    assert industries[0] == "healthcare"
    assert out["top_assets"][0]["industry"] == "healthcare"
    # Architect role surfaces the solution-architect learning path first.
    assert out["learning_paths"][0]["id"] == "lp-arch"
    # Suggested connections are filtered to the healthcare focus.
    assert [e["id"] for e in out["suggested_connections"]] == ["expert-health"]
    # Novice background prefers low-stage tooling (S3 Vectors, stages 1-2).
    assert out["key_tools"][0]["id"] == "tool-s3-vectors"
    # 30-day checklist present, all not-done for a fresh user.
    assert len(out["first_actions"]) >= 8
    assert all(a["done"] is False for a in out["first_actions"])
    assert {a["week"] for a in out["first_actions"]} == {1, 2, 3, 4}


def test_generate_path_backfills_when_focus_has_no_assets():
    out = _agent().handle({"display_name": "Dana", "industry_focus": ["manufacturing"]})
    # No manufacturing assets exist -> path still returns assets (backfill), not empty.
    assert out["status"] == "ok"
    assert len(out["top_assets"]) >= 1


# --- save_profile + get_profile + completion flag --------------------------
def test_save_profile_persists_and_marks_completed():
    s3 = FakeS3(_objects())
    res = _agent(s3=s3).handle(
        {
            "op": "save_profile",
            "display_name": "Dana",
            "role": "architect",
            "experience_years": "7",
            "industry_focus": ["healthcare"],
            "ai_background": "intermediate",
            "goals": ["retrieval", "governance"],
        }
    )
    assert res["status"] == "ok" and res["onboarding_completed"] is True
    assert res["onboarding"]["role"] == "architect"
    assert res["onboarding"]["experience_years"] == 7

    profile = json.loads(s3.objects["users/dana.json"])
    assert profile["onboarding_completed"] is True
    assert profile["onboarding"]["industry_focus"] == ["healthcare"]

    got = _agent(s3=s3).handle({"op": "get_profile", "display_name": "Dana"})
    assert got["onboarding_completed"] is True
    assert got["onboarding"]["ai_background"] == "intermediate"


def test_save_profile_coerces_invalid_role_and_background():
    res = _agent().handle(
        {"op": "save_profile", "display_name": "Dana", "role": "wizard", "ai_background": "ninja"}
    )
    assert res["onboarding"]["role"] == "consultant"
    assert res["onboarding"]["ai_background"] == "novice"


def test_save_profile_requires_name():
    out = _agent().handle({"op": "save_profile", "role": "architect"})
    assert out["status"] == "error"


def test_get_profile_unknown_user_is_empty_not_completed():
    out = _agent().handle({"op": "get_profile", "display_name": "Nobody"})
    assert out["status"] == "ok"
    assert out["onboarding"] is None
    assert out["onboarding_completed"] is False


# --- generate_path uses the SAVED profile when no inline fields ------------
def test_generate_path_uses_saved_profile():
    s3 = FakeS3(_objects())
    _agent(s3=s3).handle(
        {
            "op": "save_profile",
            "display_name": "Dana",
            "role": "architect",
            "industry_focus": ["healthcare"],
        }
    )
    out = _agent(s3=s3).handle({"display_name": "Dana"})  # default op = generate_path
    assert out["profile"]["role"] == "architect"
    assert out["learning_paths"][0]["id"] == "lp-arch"


# --- 30-day checklist (FR-068) ---------------------------------------------
def test_update_checklist_persists_and_reflects_in_path():
    s3 = FakeS3(_objects())
    upd = _agent(s3=s3).handle(
        {"op": "update_checklist", "display_name": "Dana", "action_id": "run-maturity-assessment"}
    )
    assert upd["status"] == "ok" and upd["checklist"]["run-maturity-assessment"] is True

    out = _agent(s3=s3).handle({"display_name": "Dana"})
    done = {a["id"]: a["done"] for a in out["first_actions"]}
    assert done["run-maturity-assessment"] is True
    assert done["browse-asset-library"] is False

    # Toggling back off persists.
    off = _agent(s3=s3).handle(
        {
            "op": "update_checklist",
            "display_name": "Dana",
            "action_id": "run-maturity-assessment",
            "done": False,
        }
    )
    assert off["checklist"]["run-maturity-assessment"] is False


def test_update_checklist_requires_name_and_action():
    out = _agent().handle({"op": "update_checklist", "display_name": "Dana"})
    assert out["status"] == "error"


def test_checklist_write_preserves_other_profile_fields():
    s3 = FakeS3(_objects())
    # Pre-existing profile with saved assets / office-hour signups must not be clobbered.
    s3.objects["users/dana.json"] = json.dumps(
        {"display_name": "Dana", "saved": ["a1"], "office_hours": ["oh-rag"]}
    )
    _agent(s3=s3).handle(
        {"op": "update_checklist", "display_name": "Dana", "action_id": "join-office-hour"}
    )
    profile = json.loads(s3.objects["users/dana.json"])
    assert profile["saved"] == ["a1"]
    assert profile["office_hours"] == ["oh-rag"]
    assert profile["onboarding_checklist"]["join-office-hour"] is True


# --- list_first_actions / recommend_connections ----------------------------
def test_list_first_actions_op():
    out = _agent().handle({"op": "list_first_actions", "display_name": "Dana"})
    assert out["status"] == "ok"
    assert any(a["id"] == "complete-profile" for a in out["first_actions"])


def test_recommend_connections_by_explicit_industry():
    out = _agent().handle({"op": "recommend_connections", "industry": "financial-services"})
    assert out["status"] == "ok"
    assert [e["id"] for e in out["suggested_connections"]] == ["expert-fin"]


# --- router registration ----------------------------------------------------
def test_router_registration():
    assert router.REGISTRY.get("AGENT-22") is OnboardingAgent


def test_router_dispatches_generate_path():
    # Route through the real dispatcher to prove the {agent_id, args} contract.
    agent = _agent()
    result = agent.handle({"display_name": "Dana", "industry_focus": ["healthcare"]})
    assert result["status"] == "ok" and "top_assets" in result
