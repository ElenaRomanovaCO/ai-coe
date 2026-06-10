"""AGENT-25 — Universal Asset Q&A tests.

A scripted fake Converse client drives the real ``BedrockClient`` through the
tool-loop, while the agent's read/search tools run against the conftest fake
vault (via a composed ``AssetLibraryAgent``). No AWS, no real model.
"""

from __future__ import annotations

import json

from agents.lambdas.modules import router
from agents.lambdas.modules.agent_25_asset_qa import AGENT_ID, AssetQAAgent
from agents.lib.bedrock_client import BedrockClient

from .conftest import ASSET_KEYS, FakeMetrics, make_agent, vec

# conftest asset ids/keys
A_ID = "reference-arch-clinical-notes-rag"
A_KEY = "assets/healthcare/2/reference-arch-clinical-notes-rag.md"
B_ID = "solution-pattern-fraud-scoring-agent"
B_KEY = "assets/financial-services/3/solution-pattern-fraud-scoring-agent.md"

ASSET_A_CONTENT = (
    "# Clinical Notes RAG\n\nA reference architecture for retrieval over clinical notes."
)
ASSET_A_FM = {
    "id": A_ID,
    "title": "Reference Architecture — Clinical Notes RAG",
    "type": "reference-architecture",
    "industry": "healthcare",
}


# --- scripted Converse fake ------------------------------------------------
class FakeConverse:
    """Stands in for a boto3 ``bedrock-runtime`` client: yields scripted turns."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def _text(text):
    return {
        "stopReason": "end_turn",
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "usage": {"inputTokens": 12, "outputTokens": 6},
    }


def _tool(tool_use_id, name, inp):
    return {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"toolUse": {"toolUseId": tool_use_id, "name": name, "input": inp}}],
            }
        },
        "usage": {"inputTokens": 12, "outputTokens": 6},
    }


def _make_qa(responses, *, vectors=None):
    return AssetQAAgent(
        bedrock_client=BedrockClient(client=FakeConverse(responses)),
        asset_agent=make_agent(vectors=vectors or []),
        metrics_client=FakeMetrics(),
    )


def _req(message, **over):
    base = {
        "asset_id": A_ID,
        "asset_content": ASSET_A_CONTENT,
        "asset_frontmatter": dict(ASSET_A_FM),
        "session_id": "sess-1",
        "message": message,
    }
    base.update(over)
    return base


# --- grounding -------------------------------------------------------------
def test_simple_answer_is_grounded_and_cites_the_asset():
    fake = FakeConverse([_text("This architecture covers retrieval over clinical notes.")])
    agent = AssetQAAgent(
        bedrock_client=BedrockClient(client=fake),
        asset_agent=make_agent(),
        metrics_client=FakeMetrics(),
    )
    out = agent.handle(_req("What is this about?"))

    assert out["status"] == "ok"
    assert "clinical notes" in out["assistant_message"]
    # primary asset is always the first (grounding) citation
    assert out["citations"][0]["asset_id"] == A_ID
    assert out["citations"][0]["asset_library_url"] == f"/modules/asset-library/{A_ID}"
    assert out["suggestions"]  # quick-prompts present
    # the full asset content was baked into the system prompt
    system_text = fake.calls[0]["system"][0]["text"]
    assert "Clinical Notes RAG" in system_text
    assert A_ID in system_text


def test_history_is_threaded_before_the_new_message():
    fake = FakeConverse([_text("Yes, as I said.")])
    agent = AssetQAAgent(
        bedrock_client=BedrockClient(client=fake),
        asset_agent=make_agent(),
        metrics_client=FakeMetrics(),
    )
    agent.handle(
        _req(
            "And the risks?",
            history=[
                {"role": "user", "text": "Summarize this"},
                {"role": "assistant", "text": "It is a RAG architecture."},
            ],
        )
    )
    # the fake stores the messages list by reference and the loop appends the
    # assistant reply after the call — so inspect the input prefix (first 3).
    msgs = fake.calls[0]["messages"]
    assert [m["role"] for m in msgs[:3]] == ["user", "assistant", "user"]
    assert msgs[2]["content"][0]["text"] == "And the risks?"


# --- summarize_for_role ----------------------------------------------------
def test_summarize_for_role_framing_reaches_the_model():
    fake = FakeConverse(
        [
            _tool("t1", "summarize_for_role", {"role": "executive"}),
            _text("Bottom line: this reduces clinical documentation effort."),
        ]
    )
    agent = AssetQAAgent(
        bedrock_client=BedrockClient(client=fake),
        asset_agent=make_agent(),
        metrics_client=FakeMetrics(),
    )
    out = agent.handle(_req("Summarize this for an executive"))

    assert out["status"] == "ok"
    assert "Bottom line" in out["assistant_message"]
    # the executive framing was handed back to the model on the 2nd turn
    second_turn = json.dumps(fake.calls[1]["messages"])
    assert "senior leadership" in second_turn
    assert "business value" in second_turn


def test_summarize_for_role_dispatch_known_and_unknown():
    agent = _make_qa([])
    from agents.lambdas.modules.agent_25_asset_qa import AssetChatRequest, _Accumulator

    req = AssetChatRequest.model_validate(_req("x"))
    accum = _Accumulator()
    known = agent._dispatch("summarize_for_role", {"role": "Compliance"}, accum=accum, req=req)
    assert known["role"] == "compliance"
    assert "controls and safeguards" in known["framing"]["emphasize"]

    unknown = agent._dispatch("summarize_for_role", {"role": "wizard"}, accum=accum, req=req)
    assert unknown["status"] == "ok"
    assert unknown["role"] == "wizard"
    assert "general reader" in unknown["framing"]["audience"]


# --- compare via read_asset ------------------------------------------------
def test_compare_pulls_other_asset_and_cites_it():
    fake = FakeConverse(
        [
            _tool("t1", "read_asset", {"asset_id": B_ID}),
            _text("Unlike the fraud-scoring pattern, this one targets clinical retrieval."),
        ]
    )
    agent = AssetQAAgent(
        bedrock_client=BedrockClient(client=fake),
        asset_agent=make_agent(),
        metrics_client=FakeMetrics(),
    )
    out = agent.handle(_req(f"Compare this to {B_ID}"))

    cited = {c["asset_id"] for c in out["citations"]}
    assert cited == {A_ID, B_ID}
    # the other asset's body was returned to the model
    second_turn = json.dumps(fake.calls[1]["messages"])
    assert "Fraud Scoring Agent" in second_turn


# --- scoped search ---------------------------------------------------------
def test_scoped_search_excludes_the_context_asset():
    # vectors return BOTH assets; the in-context one must be filtered out.
    vectors = [vec(A_KEY), vec(B_KEY)]
    fake = FakeConverse(
        [
            _tool("t1", "search_vector_index_scoped", {"query": "fraud patterns"}),
            _text("The closest related asset is the fraud-scoring pattern."),
        ]
    )
    agent = AssetQAAgent(
        bedrock_client=BedrockClient(client=fake),
        asset_agent=make_agent(vectors=vectors),
        metrics_client=FakeMetrics(),
    )
    out = agent.handle(_req("How does this relate to other assets?"))

    # search results handed to the model exclude A_ID
    tool_result = json.dumps(fake.calls[1]["messages"])
    assert B_ID in tool_result
    returned_ids = {c["asset_id"] for c in out["citations"]}
    assert B_ID in returned_ids
    # only the in-context asset (A) was excluded from the SEARCH results, but it
    # still appears as the primary grounding citation — so A is present once.
    assert A_ID in returned_ids
    # a search happened → comparison-flavored suggestions
    assert any("Compare" in s for s in out["suggestions"])


def test_scoped_search_respects_explicit_exclude_id():
    agent = _make_qa([], vectors=[vec(A_KEY), vec(B_KEY)])
    from agents.lambdas.modules.agent_25_asset_qa import AssetChatRequest, _Accumulator

    req = AssetChatRequest.model_validate(_req("x"))
    accum = _Accumulator()
    res = agent._dispatch(
        "search_vector_index_scoped",
        {"query": "anything", "exclude_asset_id": B_ID, "top_k": 5},
        accum=accum,
        req=req,
    )
    ids = {a["id"] for a in res["assets"]}
    assert B_ID not in ids
    assert A_ID in ids


# --- budget + validation ---------------------------------------------------
def test_tool_turn_budget_exhausted_degrades_gracefully():
    # always asks for a tool → never terminates with text
    loop = [_tool(f"t{i}", "summarize_for_role", {"role": "executive"}) for i in range(8)]
    agent = AssetQAAgent(
        bedrock_client=BedrockClient(client=FakeConverse(loop)),
        asset_agent=make_agent(),
        metrics_client=FakeMetrics(),
    )
    out = agent.handle(_req("loop forever"))
    assert out["status"] == "ok"
    assert "rephrase" in out["assistant_message"].lower()


def test_missing_message_and_asset_id_error():
    agent = _make_qa([])
    assert agent.handle({"asset_id": A_ID})["status"] == "error"
    assert agent.handle({"message": "hi"})["status"] == "error"


def test_id_alias_accepted():
    fake = FakeConverse([_text("ok")])
    agent = AssetQAAgent(
        bedrock_client=BedrockClient(client=fake),
        asset_agent=make_agent(),
        metrics_client=FakeMetrics(),
    )
    out = agent.handle({"id": A_ID, "message": "hi", "asset_content": "x"})
    assert out["status"] == "ok"


# --- registration ----------------------------------------------------------
def test_agent_25_registered():
    assert router.REGISTRY.get("AGENT-25") is AssetQAAgent
    assert AGENT_ID == "AGENT-25"


def test_router_dispatches_agent_25():
    # exercise the real router path with a fake-backed agent injected
    from agents.lambdas.modules.agent_25_asset_qa import AssetQAAgent as _A

    orig = router.REGISTRY["AGENT-25"]
    try:
        router.REGISTRY["AGENT-25"] = lambda: AssetQAAgent(
            bedrock_client=BedrockClient(client=FakeConverse([_text("hello")])),
            asset_agent=make_agent(),
            metrics_client=FakeMetrics(),
        )
        out = router.route({"agent_id": "AGENT-25", "args": _req("hi")})
        assert out["status"] == "ok"
        assert out["assistant_message"] == "hello"
    finally:
        router.REGISTRY["AGENT-25"] = orig
    assert _A is AssetQAAgent
    assert ASSET_KEYS  # sanity: conftest fixtures imported
