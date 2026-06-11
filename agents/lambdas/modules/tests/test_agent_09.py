"""AGENT-09 Q&A: community (list/get/post/answer/upvote) + AI (answer_with_citations)."""

from agents.lambdas.modules.agent_09_qa import QaAgent

from .conftest import FakeBedrockEmbed, FakeMetrics, FakeS3, FakeS3Vectors


def _thread(id_, question, tags, answers):
    tag_list = ", ".join(f'"{t}"' for t in tags)
    ans_yaml = ""
    for a in answers:
        ans_yaml += (
            f"  - id: {a['id']}\n"
            f"    text: \"{a['text']}\"\n"
            f"    posted_by: {a.get('posted_by', 'demo')}\n"
            f"    posted_at: \"{a['posted_at']}\"\n"
        )
    if not answers:
        ans_yaml = " []\n"
        answers_field = f"answers:{ans_yaml}"
    else:
        answers_field = f"answers:\n{ans_yaml}"
    return (
        f"---\nid: {id_}\nquestion: \"{question}\"\ntags: [{tag_list}]\n"
        f"posted_by: demo\nposted_at: \"2026-05-20T10:00:00Z\"\n{answers_field}---\n\n"
        f"# {question}\n\n## Answers\n\nbody.\n"
    )


REG_MD = (
    "---\nid: reg-eu-ai-act\nname: EU Artificial Intelligence Act\ngeo: eu\n"
    "industry_scope: [\"healthcare\"]\nstatus: in-effect\ntags: [\"eu\"]\n---\n\n"
    "# EU Artificial Intelligence Act\n\nHigh-risk systems include medical devices.\n"
)

THREAD_A = _thread(
    "qa-thread-a", "What vector DB for a small RAG pilot?", ["rag", "vector-db"],
    [
        {"id": "ans-1", "text": "Use S3 Vectors for AWS-native.", "posted_at": "2026-05-20T11:00Z"},
        {"id": "ans-2", "text": "Pinecone for high QPS.", "posted_at": "2026-05-20T12:00Z"},
    ],
)
THREAD_B = _thread(
    "qa-thread-b", "How to size Bedrock throughput?", ["bedrock", "cost"], []
)

BASE_KEYS = {
    "qa/2026-05/qa-thread-a.md": THREAD_A,
    "qa/2026-05/qa-thread-b.md": THREAD_B,
    "regs/eu/ai-act/eu-ai-act.md": REG_MD,
}


class FakeBedrockClient:
    def __init__(self, text="Per the [EU Artificial Intelligence Act], medical AI is high-risk."):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


def _agent(*, vectors=None, bedrock_client=None, objects=None):
    return QaAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=FakeS3(dict(BASE_KEYS) if objects is None else objects),
        s3vectors=FakeS3Vectors(vectors or []),
        bedrock=FakeBedrockEmbed(),
        bedrock_client=bedrock_client or FakeBedrockClient(),
        metrics_client=FakeMetrics(),
    )


# --- list ------------------------------------------------------------------
def test_list_recent_default():
    out = _agent().handle({"op": "list_threads"})
    assert out["status"] == "ok"
    assert {t["id"] for t in out["threads"]} == {"qa-thread-a", "qa-thread-b"}
    a = next(t for t in out["threads"] if t["id"] == "qa-thread-a")
    assert a["answer_count"] == 2


def test_list_unanswered_sort_puts_empty_first():
    out = _agent().handle({"op": "list_threads", "sort": "unanswered"})
    assert out["threads"][0]["id"] == "qa-thread-b"  # 0 answers


def test_list_filters_by_tag():
    out = _agent().handle({"op": "list_threads", "tag": "bedrock"})
    assert {t["id"] for t in out["threads"]} == {"qa-thread-b"}


# --- get -------------------------------------------------------------------
def test_get_thread_answers_and_score():
    out = _agent().handle({"op": "get_thread", "thread_id": "qa-thread-a"})
    assert out["status"] == "ok"
    assert len(out["thread"]["answers"]) == 2
    assert out["thread"]["score"] == 0


def test_get_unknown_not_found():
    assert _agent().handle({"op": "get_thread", "thread_id": "nope"})["status"] == "not_found"


# --- post ------------------------------------------------------------------
def test_post_thread_writes_to_vault_qa():
    agent = _agent()
    out = agent.handle({
        "op": "post_thread", "question": "How do I pick an embedding model?",
        "tags": ["rag"], "display_name": "Dana",
    })
    assert out["status"] == "ok"
    tid = out["thread"]["id"]
    assert tid.startswith("qa-")
    # Written under qa/{yyyy-mm}/...
    key = next(k for k in agent.s3.objects if k.endswith(f"{tid}.md") and k.startswith("qa/"))
    assert "/20" in key  # qa/<yyyy-mm>/
    # Now visible in list.
    listed = agent.handle({"op": "list_threads"})["threads"]
    assert tid in {t["id"] for t in listed}


def test_post_thread_with_initial_answer():
    out = _agent().handle({
        "op": "post_thread", "question": "Save this AI answer?", "display_name": "Dana",
        "initial_answer": "Yes — here is the synthesized answer.",
    })
    assert out["thread"]["answer_count"] == 1


def test_post_requires_question():
    assert _agent().handle({"op": "post_thread", "display_name": "Dana"})["status"] == "error"


# --- answer ----------------------------------------------------------------
def test_answer_thread_appends():
    agent = _agent()
    out = agent.handle({
        "op": "answer_thread", "thread_id": "qa-thread-b",
        "answer_text": "Start on-demand and measure.", "display_name": "Dana",
    })
    assert out["status"] == "ok" and out["thread"]["answer_count"] == 1
    # Persisted: re-get sees the new answer.
    got = agent.handle({"op": "get_thread", "thread_id": "qa-thread-b"})
    assert got["thread"]["answers"][0]["text"] == "Start on-demand and measure."


# --- upvote ----------------------------------------------------------------
def test_upvote_increments_once_idempotent():
    agent = _agent()
    a = {"op": "upvote", "thread_id": "qa-thread-a", "answer_id": "ans-1", "display_name": "Dana"}
    first = agent.handle(a)
    assert first["status"] == "ok" and first["upvotes"] == 1
    second = agent.handle(a)  # same user, same answer
    assert second["upvotes"] == 1  # idempotent
    # Reflected in get.
    got = agent.handle({"op": "get_thread", "thread_id": "qa-thread-a", "display_name": "Dana"})
    ans1 = next(x for x in got["thread"]["answers"] if x["id"] == "ans-1")
    assert ans1["upvotes"] == 1 and ans1["voted"] is True


def test_upvote_requires_display_name():
    out = _agent().handle({"op": "upvote", "thread_id": "qa-thread-a", "answer_id": "ans-1"})
    assert out["status"] == "error"


# --- answer_with_citations (AI mode) ---------------------------------------
def _rag_vectors():
    return [
        {"metadata": {"content_type": "regs", "file_path": "regs/eu/ai-act/eu-ai-act.md"}},
        {"metadata": {"content_type": "qa", "file_path": "qa/2026-05/qa-thread-a.md"}},
    ]


def test_answer_with_citations_synthesizes_and_cites():
    fake = FakeBedrockClient()
    out = _agent(vectors=_rag_vectors(), bedrock_client=fake).handle({
        "op": "answer_with_citations",
        "question": "Is a medical imaging classifier high-risk under the EU AI Act?",
    })
    assert out["status"] == "ok"
    assert "high-risk" in out["answer"].lower()
    cited = {c["id"] for c in out["citations"]}
    assert "reg-eu-ai-act" in cited
    # The reg citation deep-links into the compliance tracker.
    reg = next(c for c in out["citations"] if c["id"] == "reg-eu-ai-act")
    assert reg["url"] == "/modules/compliance-tracker/reg-eu-ai-act"
    # The qa hit surfaces as a related thread.
    assert any(r["id"] == "qa-thread-a" for r in out["related_threads"])
    assert out["confidence"] in ("high", "medium", "low")
    assert fake.calls == 1


def test_answer_with_citations_confidence_low_when_no_hits():
    out = _agent(vectors=[]).handle({
        "op": "answer_with_citations", "question": "totally unrelated question",
    })
    assert out["status"] == "ok"
    assert out["confidence"] == "low"
    assert out["citations"] == []


def test_answer_with_citations_fallback_on_llm_error():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("bedrock down")

    out = _agent(vectors=_rag_vectors(), bedrock_client=Boom()).handle({
        "op": "answer_with_citations", "question": "high-risk medical AI?",
    })
    assert out["status"] == "ok"
    assert out["citations"]  # still returns the sources
    assert "EU Artificial Intelligence Act" in out["answer"]  # fallback names sources
