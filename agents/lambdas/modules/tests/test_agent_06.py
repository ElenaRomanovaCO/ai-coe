"""AGENT-06 knowledge contribution: submit / anonymize / tags / queue / approve / reject."""

import json

from agents.lambdas.modules import router
from agents.lambdas.modules.agent_06_contribute import ContributeAgent

from .conftest import FakeMetrics, FakeS3

ANALYZE_JSON = json.dumps(
    {
        "flagged_spans": [
            {
                "span": "Acme Health",
                "suggested_replacement": "a regional health system",
                "reason": "identifiable company name",
            }
        ],
        "suggested_anonymized_body": "We helped a regional health system deploy clinical RAG.",
        "tags": ["RAG", "Healthcare"],
    }
)

BODY = "We helped Acme Health deploy clinical RAG."


class FakeSonnet:
    def __init__(self, text=ANALYZE_JSON):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


class FakeAssets:
    """Stand-in for the composed AGENT-03 duplicate search."""

    def handle(self, args):
        return {
            "status": "ok",
            "assets": [{"id": "ref-arch-existing", "title": "Existing RAG", "file_path": "a.md"}],
        }


def _agent(s3=None, sonnet=None):
    return ContributeAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=s3 if s3 is not None else FakeS3({}),
        bedrock_client=sonnet or FakeSonnet(),
        asset_agent=FakeAssets(),
        metrics_client=FakeMetrics(),
    )


SUBMIT = {
    "op": "submit_asset",
    "display_name": "Dana",
    "title": "Clinical RAG Lessons",
    "type": "solution-pattern",
    "industry": "healthcare",
    "ai_stage": 2,
    "body_markdown": BODY,
}


# --- submit (FR-064/066) ---------------------------------------------------
def test_submit_runs_anonymization_tags_and_duplicates_and_persists():
    s3 = FakeS3({})
    out = _agent(s3=s3).handle(dict(SUBMIT))
    assert out["status"] == "ok"
    pid = out["pending_id"]
    spans = out["anonymization"]["flagged_spans"]
    assert spans[0]["span"] == "Acme Health"
    assert spans[0]["offset"] == BODY.find("Acme Health")  # computed server-side
    assert "regional health system" in out["anonymization"]["suggested_anonymized_body"]
    assert out["tag_suggestions"]["tags"] == ["rag", "healthcare"]  # lowercased
    assert out["tag_suggestions"]["duplicates"][0]["id"] == "ref-arch-existing"
    # Persisted to the SESSIONS bucket (never vault).
    assert f"contributions/{pid}.json" in s3.objects
    assert not any(k.startswith("assets/") for k in s3.objects)


def test_submit_requires_core_fields():
    assert _agent().handle({"op": "submit_asset", "display_name": "Dana"})["status"] == "error"


# --- anonymization / tags standalone (FR-066) ------------------------------
def test_run_anonymization_by_body():
    out = _agent().handle({"op": "run_anonymization", "body_markdown": BODY})
    assert out["status"] == "ok" and out["flagged_spans"][0]["span"] == "Acme Health"


def test_suggest_tags_by_pending_id_updates_record():
    s3 = FakeS3({})
    pid = _agent(s3=s3).handle(dict(SUBMIT))["pending_id"]
    out = _agent(s3=s3).handle({"op": "suggest_tags", "pending_id": pid})
    assert out["status"] == "ok" and out["tags"] == ["rag", "healthcare"]
    assert out["duplicates"][0]["id"] == "ref-arch-existing"


# --- queue (FR-065) --------------------------------------------------------
def test_list_pending_and_get():
    s3 = FakeS3({})
    a = _agent(s3=s3)
    pid = a.handle(dict(SUBMIT))["pending_id"]
    a.handle({**SUBMIT, "title": "Second"})
    listed = _agent(s3=s3).handle({"op": "list_pending"})
    assert listed["status"] == "ok" and len(listed["pending"]) == 2
    assert listed["pending"][0]["flag_count"] == 1
    got = _agent(s3=s3).handle({"op": "get_pending", "pending_id": pid})
    assert got["status"] == "ok" and got["title"] == "Clinical RAG Lessons"


# --- approve (FR-065) ------------------------------------------------------
def test_approve_writes_asset_to_vault_and_marks_approved():
    s3 = FakeS3({})
    pid = _agent(s3=s3).handle(dict(SUBMIT))["pending_id"]
    out = _agent(s3=s3).handle(
        {
            "op": "approve_asset",
            "pending_id": pid,
            "final_body": "We helped a regional health system deploy clinical RAG.",
            "final_frontmatter": {
                "id": "clinical-rag-lessons",
                "title": "Clinical RAG Lessons",
                "type": "solution-pattern",
                "industry": "healthcare",
                "ai_stage": 2,
                "tags": ["rag", "healthcare"],
                "use_case_type": ["rag"],
            },
        }
    )
    assert out["status"] == "ok"
    key = out["file_path"]
    assert key == "assets/healthcare/2/clinical-rag-lessons.md"
    doc = s3.objects[key]
    assert doc.startswith("---") and "id: clinical-rag-lessons" in doc
    assert "regional health system" in doc
    # Pending record marked approved (no delete needed).
    rec = json.loads(s3.objects[f"contributions/{pid}.json"])
    assert rec["review_status"] == "approved" and rec["approved"]["file_path"] == key


def test_approve_rejects_path_outside_assets():
    s3 = FakeS3({})
    pid = _agent(s3=s3).handle(dict(SUBMIT))["pending_id"]
    out = _agent(s3=s3).handle(
        {
            "op": "approve_asset",
            "pending_id": pid,
            "target_path": "secrets/evil.md",
            "final_body": "x",
        }
    )
    assert out["status"] == "error"


def test_reject_marks_rejected():
    s3 = FakeS3({})
    pid = _agent(s3=s3).handle(dict(SUBMIT))["pending_id"]
    out = _agent(s3=s3).handle({"op": "reject_asset", "pending_id": pid, "reason": "duplicate"})
    assert out["status"] == "ok"
    rec = json.loads(s3.objects[f"contributions/{pid}.json"])
    assert rec["review_status"] == "rejected" and rec["rejection_reason"] == "duplicate"


def test_router_registration():
    assert router.REGISTRY.get("AGENT-06") is ContributeAgent
