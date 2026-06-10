"""AGENT-08 tools repository: list / get / recommend over the tools corpus."""

from agents.lambdas.modules.agent_08_tools import ToolsRepoAgent

from .conftest import FakeBedrockEmbed, FakeMetrics, FakeS3, FakeS3Vectors


def _tool(id_, name, category, stack, stages, cost, tags):
    stack_list = ", ".join(f'"{s}"' for s in stack)
    stage_list = ", ".join(str(s) for s in stages)
    tag_list = ", ".join(f'"{t}"' for t in tags)
    return (
        f"---\nid: {id_}\nname: {name}\ncategory: {category}\n"
        f"stack: [{stack_list}]\nai_stage_fit: [{stage_list}]\ncost_model: {cost}\n"
        f"tags: [{tag_list}]\n---\n\n# {name}\n\n## Best-fit scenarios\n\nUse {name}.\n"
    )


TOOL_KEYS = {
    "tools/pinecone.md": _tool(
        "tool-pinecone", "Pinecone", "vector-db", ["managed-service"], [2, 3], "usage-based",
        ["vector-db", "managed", "rag"],
    ),
    "tools/s3-vectors.md": _tool(
        "tool-s3-vectors", "S3 Vectors", "vector-db", ["aws"], [1, 2], "usage-based",
        ["vector-db", "aws", "serverless"],
    ),
    "tools/langchain.md": _tool(
        "tool-langchain", "LangChain", "framework", ["python", "javascript"], [1, 2, 3],
        "open-source", ["framework", "rag", "orchestration"],
    ),
    "tools/aws-bedrock.md": _tool(
        "tool-aws-bedrock", "AWS Bedrock", "llm-provider", ["aws", "boto3"], [1, 2, 3, 4],
        "usage-based", ["llm-provider", "aws"],
    ),
}


def make_agent(*, vectors=None):
    return ToolsRepoAgent(
        vault_bucket="vault-bucket",
        s3=FakeS3(dict(TOOL_KEYS)),
        bedrock=FakeBedrockEmbed(),
        s3vectors=FakeS3Vectors(vectors or []),
        metrics_client=FakeMetrics(),
    )


# --- list ------------------------------------------------------------------
def test_list_all_tools():
    out = make_agent().handle({"op": "list_tools"})
    assert out["status"] == "ok"
    assert {t["id"] for t in out["tools"]} == set(
        ["tool-pinecone", "tool-s3-vectors", "tool-langchain", "tool-aws-bedrock"]
    )


def test_list_filters_by_category():
    # The task smoke: category=vector-db returns the vector stores.
    out = make_agent().handle({"op": "list_tools", "category": "vector-db"})
    assert {t["id"] for t in out["tools"]} == {"tool-pinecone", "tool-s3-vectors"}


def test_list_filters_by_cost_and_stack():
    out = make_agent().handle({"op": "list_tools", "cost": "open-source"})
    assert {t["id"] for t in out["tools"]} == {"tool-langchain"}
    out2 = make_agent().handle({"op": "list_tools", "stack": "aws"})
    assert {t["id"] for t in out2["tools"]} == {"tool-s3-vectors", "tool-aws-bedrock"}


def test_list_filters_by_stage():
    out = make_agent().handle({"op": "list_tools", "stage": 4})
    assert {t["id"] for t in out["tools"]} == {"tool-aws-bedrock"}


def test_list_default_op_is_list():
    out = make_agent().handle({})
    assert out["status"] == "ok" and len(out["tools"]) == 4


# --- get -------------------------------------------------------------------
def test_get_tool_by_id():
    out = make_agent().handle({"op": "get_tool", "tool_id": "tool-s3-vectors"})
    assert out["status"] == "ok"
    assert out["tool"]["summary"]["name"] == "S3 Vectors"
    assert "Best-fit scenarios" in out["tool"]["body_markdown"]
    assert out["tool"]["frontmatter"]["cost_model"] == "usage-based"


def test_get_via_id_alias_and_inferred_op():
    out = make_agent().handle({"id": "tool-pinecone"})
    assert out["status"] == "ok" and out["tool"]["summary"]["id"] == "tool-pinecone"


def test_get_unknown_tool_not_found():
    out = make_agent().handle({"op": "get_tool", "tool_id": "tool-nope"})
    assert out["status"] == "not_found"


# --- recommend -------------------------------------------------------------
def test_recommend_filters_to_tools_content_type():
    vectors = [
        {"metadata": {"content_type": "tools", "file_path": "tools/pinecone.md"}},
        {"metadata": {"content_type": "assets", "file_path": "assets/x.md"}},
        {"metadata": {"content_type": "tools", "file_path": "tools/s3-vectors.md"}},
    ]
    out = make_agent(vectors=vectors).handle(
        {"op": "recommend_tools_for_context", "query": "vector database for rag"}
    )
    assert out["status"] == "ok"
    assert [t["id"] for t in out["tools"]] == ["tool-pinecone", "tool-s3-vectors"]


def test_recommend_applies_context_filter():
    vectors = [
        {"metadata": {"content_type": "tools", "file_path": "tools/pinecone.md"}},
        {"metadata": {"content_type": "tools", "file_path": "tools/s3-vectors.md"}},
    ]
    out = make_agent(vectors=vectors).handle(
        {"op": "recommend", "query": "vector db", "stage": 3}
    )
    # Only Pinecone fits stage 3 among the two vector stores.
    assert {t["id"] for t in out["tools"]} == {"tool-pinecone"}


def test_recommend_requires_query():
    out = make_agent().handle({"op": "recommend_tools_for_context"})
    assert out["status"] == "error"
