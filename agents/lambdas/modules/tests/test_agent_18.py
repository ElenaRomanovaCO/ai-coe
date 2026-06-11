"""AGENT-18 decision log: write / search / get / similar.

Vault writes + reads run against in-memory S3; the Haiku tag-suggestion call and the
Titan embed / S3 Vectors query are faked.
"""

from agents.lambdas.modules.agent_18_decisions import DecisionsAgent
from agents.lambdas.modules.vault_export import export_frontmatter

from .conftest import FakeBedrockEmbed, FakeMetrics, FakeS3, FakeS3Vectors


class FakeHaiku:
    """Tag-suggestion Converse call."""

    def __init__(self, text='["vector-db", "rag"]'):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


def _decision_md(decision_id, decision, *, tags, context="", rationale="", created_at="2026-06-01"):
    fm = export_frontmatter(
        "decision",
        {
            "decision_id": decision_id,
            "decision": decision,
            "context": context,
            "alternatives": [],
            "rationale": rationale,
            "outcome": None,
            "tags": tags,
            "engagement_id": None,
            "created_at": created_at,
            "updated_at": created_at,
        },
    )
    return f"{fm}\n# Decision — {decision}\n\n{context} {rationale}\n"


# Three seeded logged decisions in the healthcare-RAG space + one for contrast.
SEED = {
    "decisions/dana/dec-aaa.md": _decision_md(
        "dec-aaa", "Use a managed vector store for clinical-notes RAG",
        tags=["vector-db", "healthcare", "rag"], context="clinical notes", rationale="managed ops",
        created_at="2026-06-01",
    ),
    "decisions/dana/dec-bbb.md": _decision_md(
        "dec-bbb", "Chunk clinical notes by section heading",
        tags=["rag", "healthcare", "chunking"], context="clinical notes retrieval",
        created_at="2026-06-02",
    ),
    "decisions/dana/dec-ccc.md": _decision_md(
        "dec-ccc", "Adopt Titan embeddings for the RAG index",
        tags=["embeddings", "rag"], context="healthcare rag", created_at="2026-06-03",
    ),
    # A CURATED architecture-decision doc shares the decisions/ folder — NO generated flag.
    "decisions/worker-pattern.md": (
        '---\nid: worker-pattern\ntitle: Worker pattern\nkind: decision\n'
        'owner: demo\nupdated_at: "2026-06-09"\n---\n\n# Worker pattern\n\nCurated.\n'
    ),
}


def _vec(key, content_type="decisions", generated=True, idx=0):
    meta = {"file_path": key, "content_type": content_type, "chunk_index": idx}
    if generated:
        meta["generated"] = True
    return {"key": f"{key}#{idx}", "metadata": meta}


def _agent(s3=None, haiku=None, vectors=None):
    return DecisionsAgent(
        vault_bucket="vault",
        s3=s3 if s3 is not None else FakeS3({}),
        bedrock=FakeBedrockEmbed(),
        bedrock_client=haiku or FakeHaiku(),
        s3vectors=FakeS3Vectors(vectors or []),
        metrics_client=FakeMetrics(),
    )


# --- write -----------------------------------------------------------------
def test_write_persists_generated_artifact_with_suggested_tags():
    s3 = FakeS3({})
    out = _agent(s3=s3, haiku=FakeHaiku('["vector-db", "rag"]')).handle(
        {
            "op": "write",
            "display_name": "Dana",
            "decision": "Use a managed vector store",
            "context": "clinical notes RAG",
            "alternatives": ["self-hosted pgvector"],
            "rationale": "less ops",
            "tags": ["healthcare"],
        }
    )
    assert out["status"] == "ok"
    assert out["decision"]["decision_id"].startswith("dec-")
    # User tag + Haiku-suggested tags merged + de-duped.
    assert set(out["decision"]["tags"]) == {"healthcare", "vector-db", "rag"}
    key = out["vault_file_path"]
    assert key.startswith("decisions/dana/") and key.endswith(".md")
    md = s3.objects[key]
    assert "content_type: decision" in md and "generated: true" in md
    assert "## Rationale" in md  # prose rendered in the body for embedding


def test_write_requires_display_name_and_decision():
    assert _agent().handle({"op": "write", "decision": "x"})["status"] == "error"
    assert _agent().handle({"op": "write", "display_name": "Dana"})["status"] == "error"


def test_write_degrades_when_tag_llm_errors():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("haiku down")

    out = _agent(haiku=Boom()).handle(
        {"op": "write", "display_name": "Dana", "decision": "d", "tags": ["kept"]}
    )
    assert out["status"] == "ok"
    assert out["decision"]["tags"] == ["kept"]  # user tags still applied


def test_write_inferred_when_decision_present():
    out = _agent().handle({"display_name": "Dana", "decision": "d"})
    assert out["status"] == "ok" and out["decision"]["decision_id"]


# --- search ----------------------------------------------------------------
def test_search_all_returns_only_logged_decisions():
    out = _agent(s3=FakeS3(dict(SEED))).handle({"op": "search"})
    ids = {d["decision_id"] for d in out["decisions"]}
    assert ids == {"dec-aaa", "dec-bbb", "dec-ccc"}  # curated worker-pattern excluded


def test_search_filters_by_query_and_tags():
    agent = _agent(s3=FakeS3(dict(SEED)))
    by_query = agent.handle({"op": "search", "query": "chunk"})
    assert {d["decision_id"] for d in by_query["decisions"]} == {"dec-bbb"}
    by_tag = agent.handle({"op": "search", "tags": ["embeddings"]})
    assert {d["decision_id"] for d in by_tag["decisions"]} == {"dec-ccc"}


def test_search_sorted_recent_first():
    out = _agent(s3=FakeS3(dict(SEED))).handle({"op": "search"})
    dates = [d["created_at"] for d in out["decisions"]]
    assert dates == sorted(dates, reverse=True)


# --- get -------------------------------------------------------------------
def test_get_returns_full_record():
    out = _agent(s3=FakeS3(dict(SEED))).handle({"op": "get", "decision_id": "dec-aaa"})
    assert out["status"] == "ok"
    assert out["decision"]["decision"].startswith("Use a managed vector store")
    assert "rationale" in out["decision"]


def test_get_via_id_alias():
    out = _agent(s3=FakeS3(dict(SEED))).handle({"id": "dec-bbb"})
    assert out["status"] == "ok" and out["decision"]["decision_id"] == "dec-bbb"


def test_get_unknown_not_found():
    out = _agent(s3=FakeS3(dict(SEED))).handle({"op": "get", "decision_id": "dec-zzz"})
    assert out["status"] == "not_found"


# --- similar ---------------------------------------------------------------
def test_similar_scopes_to_logged_decisions_and_excludes_self():
    vectors = [
        _vec("decisions/dana/dec-aaa.md"),  # self — excluded
        _vec("decisions/dana/dec-bbb.md"),
        _vec("decisions/dana/dec-ccc.md"),
        _vec("decisions/worker-pattern.md", generated=False),  # curated — excluded
        _vec("assets/some-asset.md", content_type="assets"),  # wrong type — excluded
    ]
    out = _agent(s3=FakeS3(dict(SEED)), vectors=vectors).handle(
        {"op": "similar", "decision_id": "dec-aaa"}
    )
    assert out["status"] == "ok"
    ids = {d["decision_id"] for d in out["similar"]}
    assert ids == {"dec-bbb", "dec-ccc"}  # other logged decisions only


def test_similar_respects_top_k():
    vectors = [_vec("decisions/dana/dec-bbb.md"), _vec("decisions/dana/dec-ccc.md")]
    out = _agent(s3=FakeS3(dict(SEED)), vectors=vectors).handle(
        {"op": "similar", "decision_id": "dec-aaa", "top_k": 1}
    )
    assert len(out["similar"]) == 1


def test_similar_unknown_not_found():
    out = _agent(s3=FakeS3(dict(SEED))).handle({"op": "similar", "decision_id": "dec-zzz"})
    assert out["status"] == "not_found"
