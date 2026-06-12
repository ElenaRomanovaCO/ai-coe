"""AGENT-07 community hub: learning paths / office hours (+ signup) / experts / threads."""

import json

from agents.lambdas.modules import router
from agents.lambdas.modules.agent_07_community import CommunityAgent

from .conftest import FakeMetrics, FakeS3

LP_ARCHITECT = """---
id: lp-arch
kind: learning-path
title: Architecture Foundations
role: solution-architect
stage: 1
duration: 4 weeks
modules: ["RAG", "Bedrock"]
tags: ["architecture"]
---
# Architecture Foundations
Body.
"""

LP_EXEC = """---
id: lp-exec
kind: learning-path
title: AI Strategy for Executives
role: executive
stage: 0
duration: 1 week
modules: ["Maturity curve"]
tags: ["strategy"]
---
# Exec
Body.
"""

OH_RAG = """---
id: oh-rag
kind: office-hours
title: RAG Patterns
host: Guild
date: "2026-06-18T16:00:00Z"
topic: RAG
capacity: 25
tags: ["rag"]
---
# RAG Office Hours
Body.
"""

OH_GOV = """---
id: oh-gov
kind: office-hours
title: Governance
host: Working Group
date: "2026-06-25T15:00:00Z"
topic: Governance
capacity: 30
tags: ["governance"]
---
# Gov Office Hours
Body.
"""

EXPERT_HEALTH = """---
id: expert-health
kind: expert
title: Principal AI Architect
name: Alex Rivera
expertise: ["Retrieval-augmented generation", "Clinical NLP"]
industries: ["healthcare"]
tags: ["rag", "healthcare"]
---
# Alex Rivera
Body.
"""

EXPERT_FIN = """---
id: expert-fin
kind: expert
title: AI Governance Lead
name: Jordan Kim
expertise: ["AI governance", "Fraud detection"]
industries: ["financial-services"]
tags: ["fintech"]
---
# Jordan Kim
Body.
"""

QA_THREAD = """---
id: thread-1
question: How should we chunk long PDFs for RAG?
tags: ["rag"]
posted_by: demo
posted_at: "2026-05-10T10:00:00Z"
answers: []
---
# How should we chunk long PDFs for RAG?
Body.
"""


def _objects():
    return {
        "community/learning-paths/lp-arch.md": LP_ARCHITECT,
        "community/learning-paths/lp-exec.md": LP_EXEC,
        "community/office-hours/oh-rag.md": OH_RAG,
        "community/office-hours/oh-gov.md": OH_GOV,
        "community/experts/expert-health.md": EXPERT_HEALTH,
        "community/experts/expert-fin.md": EXPERT_FIN,
        "qa/2026-05/thread-1.md": QA_THREAD,
    }


def _agent(s3=None):
    return CommunityAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=s3 if s3 is not None else FakeS3(_objects()),
        metrics_client=FakeMetrics(),
    )


# --- learning paths (FR-061) -----------------------------------------------
def test_list_learning_paths_all_and_filtered():
    out = _agent().handle({"op": "list_learning_paths"})
    assert out["status"] == "ok" and len(out["learning_paths"]) == 2

    by_role = _agent().handle({"op": "list_learning_paths", "role": "executive"})
    assert [p["id"] for p in by_role["learning_paths"]] == ["lp-exec"]

    by_stage = _agent().handle({"op": "list_learning_paths", "stage": 1})
    assert [p["id"] for p in by_stage["learning_paths"]] == ["lp-arch"]


# --- office hours + signup (FR-062) ----------------------------------------
def test_list_office_hours_sorted_and_unsigned():
    out = _agent().handle({"op": "list_office_hours"})
    assert out["status"] == "ok"
    # Sorted by date ascending.
    assert [o["id"] for o in out["office_hours"]] == ["oh-rag", "oh-gov"]
    assert all(o["signed_up"] is False for o in out["office_hours"])


def test_signup_then_listed_as_signed_up_idempotent_and_cancel():
    s3 = FakeS3(_objects())
    res = _agent(s3=s3).handle(
        {"op": "signup_office_hours", "display_name": "Dana", "office_hour_id": "oh-rag"}
    )
    assert res["status"] == "ok" and res["signed_up"] is True
    # Idempotent: signing up again keeps a single entry.
    res2 = _agent(s3=s3).handle(
        {"op": "signup_office_hours", "display_name": "Dana", "office_hour_id": "oh-rag"}
    )
    assert res2["signups"] == ["oh-rag"]
    # The listing reflects the signup for this user.
    listed = _agent(s3=s3).handle({"op": "list_office_hours", "display_name": "Dana"})
    flags = {o["id"]: o["signed_up"] for o in listed["office_hours"]}
    assert flags == {"oh-rag": True, "oh-gov": False}
    # Persisted to the user profile.
    profile = json.loads(s3.objects["users/dana.json"])
    assert profile["office_hours"] == ["oh-rag"]
    # Cancel removes it.
    cancelled = _agent(s3=s3).handle(
        {"op": "cancel_office_hours", "display_name": "Dana", "office_hour_id": "oh-rag"}
    )
    assert cancelled["signed_up"] is False and cancelled["signups"] == []


def test_signup_requires_name_and_id():
    out = _agent().handle({"op": "signup_office_hours", "display_name": "Dana"})
    assert out["status"] == "error"


# --- experts (FR-063) ------------------------------------------------------
def test_expert_directory_all_and_filtered():
    out = _agent().handle({"op": "get_expert_directory"})
    assert out["status"] == "ok" and len(out["experts"]) == 2
    # Sorted by name (Alex before Jordan).
    assert [e["name"] for e in out["experts"]] == ["Alex Rivera", "Jordan Kim"]

    by_exp = _agent().handle({"op": "get_expert_directory", "expertise": "fraud"})
    assert [e["id"] for e in by_exp["experts"]] == ["expert-fin"]

    by_ind = _agent().handle({"op": "get_expert_directory", "industry": "healthcare"})
    assert [e["id"] for e in by_ind["experts"]] == ["expert-health"]


# --- threads (composes AGENT-09) -------------------------------------------
def test_list_threads_delegates_to_qa_agent():
    out = _agent().handle({"op": "list_threads"})
    assert out["status"] == "ok"
    ids = [t.get("thread_id") or t.get("id") for t in out.get("threads", [])]
    assert "thread-1" in ids


# --- overview + registration -----------------------------------------------
def test_overview_counts():
    out = _agent().handle({})
    assert out["status"] == "ok"
    assert out["learning_paths_count"] == 2
    assert out["office_hours_count"] == 2
    assert out["experts_count"] == 2


def test_router_registration():
    assert router.REGISTRY.get("AGENT-07") is CommunityAgent
