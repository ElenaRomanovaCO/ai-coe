"""AGENT-31 trainings: list (filters) / get / save+unsave / list_saved."""

import json

from agents.lambdas.modules import router
from agents.lambdas.modules.agent_31_trainings import TrainingsAgent

from .conftest import FakeMetrics, FakeS3

TUT_RAG = """---
id: trn-rag
title: Building RAG Applications
summary: Chunking, embeddings, and grounded generation.
kind: tutorial
theme: RAG & Retrieval
source: YouTube
level: intermediate
url: "https://youtube.test/rag"
duration_min: 95
author: Generic Instructor
presenter: ""
session_date: ""
materials: []
tags: ["rag", "embeddings"]
last_verified: "2026-06-12"
updated_at: "2026-06-12"
---
# Building RAG Applications
Body.
"""

TUT_PROMPT = """---
id: trn-prompt
title: Prompt Engineering Essentials
summary: Patterns for reliable prompts.
kind: tutorial
theme: Prompt Engineering
source: Udemy
level: beginner
url: "https://udemy.test/prompt"
duration_min: 150
author: Generic Instructor
presenter: ""
session_date: ""
materials: []
tags: ["prompting"]
last_verified: "2026-06-12"
updated_at: "2026-06-12"
---
# Prompt Engineering Essentials
Body.
"""

HOSTED_RAG = """---
id: trn-hosted-rag
title: Hosted Clinic Production RAG
summary: Recorded CoE clinic on production RAG.
kind: hosted
theme: RAG & Retrieval
source: Internal
level: intermediate
url: "https://rec.test/rag-clinic"
duration_min: 60
author: ""
presenter: AI Architecture Guild
session_date: "2026-05-14T16:00:00Z"
materials:
  - label: Slides
    url: "https://mat.test/slides.pdf"
tags: ["rag", "production"]
last_verified: "2026-06-12"
updated_at: "2026-06-12"
---
# Hosted Clinic Production RAG
Body.
"""


def _objects():
    return {
        "trainings/trn-rag.md": TUT_RAG,
        "trainings/trn-prompt.md": TUT_PROMPT,
        "trainings/trn-hosted-rag.md": HOSTED_RAG,
    }


def _agent(s3=None):
    return TrainingsAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=s3 if s3 is not None else FakeS3(_objects()),
        metrics_client=FakeMetrics(),
    )


# --- list + filters (FR-090/091/092) ---------------------------------------
def test_list_all_sorted():
    out = _agent().handle({"op": "list"})
    assert out["status"] == "ok" and len(out["trainings"]) == 3
    # Sorted by (theme, title): Prompt Engineering < RAG & Retrieval.
    assert out["trainings"][0]["id"] == "trn-prompt"


def test_list_filters_by_theme_source_level_kind():
    a = _agent()

    def ids(**f):
        return [t["id"] for t in a.handle({"op": "list", **f})["trainings"]]

    assert set(ids(theme="RAG & Retrieval")) == {"trn-rag", "trn-hosted-rag"}
    assert ids(source="Udemy") == ["trn-prompt"]
    assert ids(level="beginner") == ["trn-prompt"]
    assert ids(kind="hosted") == ["trn-hosted-rag"]


def test_list_query_substring():
    out = _agent().handle({"op": "list", "query": "chunking"})
    assert [t["id"] for t in out["trainings"]] == ["trn-rag"]


# --- get -------------------------------------------------------------------
def test_get_returns_body_and_hosted_fields():
    out = _agent().handle({"op": "get", "training_id": "trn-hosted-rag"})
    assert out["status"] == "ok"
    t = out["training"]
    assert t["presenter"] == "AI Architecture Guild"
    assert t["session_date"].startswith("2026-05-14")
    assert t["materials"] == [{"label": "Slides", "url": "https://mat.test/slides.pdf"}]
    assert "Hosted Clinic" in t["body_markdown"]


def test_get_via_id_alias_and_not_found():
    assert _agent().handle({"id": "trn-rag"})["status"] == "ok"
    assert _agent().handle({"op": "get", "training_id": "trn-nope"})["status"] == "not_found"


# --- save / unsave / list_saved --------------------------------------------
def test_save_unsave_round_trip_and_list_saved():
    s3 = FakeS3(_objects())
    saved = _agent(s3=s3).handle(
        {"op": "save", "display_name": "Dana", "training_id": "trn-rag"}
    )
    assert saved["status"] == "ok" and saved["saved"] is True
    # Idempotent.
    again = _agent(s3=s3).handle({"op": "save", "display_name": "Dana", "training_id": "trn-rag"})
    assert again["saved_trainings"] == ["trn-rag"]
    # Persisted under saved_trainings (separate from asset saves).
    profile = json.loads(s3.objects["users/dana.json"])
    assert profile["saved_trainings"] == ["trn-rag"]
    # list_saved resolves to full summaries.
    listed = _agent(s3=s3).handle({"op": "list_saved", "display_name": "Dana"})
    assert [t["id"] for t in listed["trainings"]] == ["trn-rag"]
    # The list op reflects saved state for this user.
    relist = _agent(s3=s3).handle({"op": "list", "display_name": "Dana"})
    flags = {t["id"]: t["saved"] for t in relist["trainings"]}
    assert flags["trn-rag"] is True and flags["trn-prompt"] is False
    # Unsave removes it.
    un = _agent(s3=s3).handle({"op": "unsave", "display_name": "Dana", "training_id": "trn-rag"})
    assert un["saved"] is False and un["saved_trainings"] == []


def test_save_requires_name_and_id():
    out = _agent().handle({"op": "save", "display_name": "Dana"})
    assert out["status"] == "error"


def test_router_registration():
    assert router.REGISTRY.get("AGENT-31") is TrainingsAgent
