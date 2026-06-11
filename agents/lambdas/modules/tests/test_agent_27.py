"""AGENT-27 exchange catalog: list / get / search (mirrors the AGENT-03 tests).

Reads run against in-memory S3; search runs against a fake S3 Vectors. Also asserts the
real seed corpus is fully typed (content_type: exchange) so it never pollutes content
search.
"""

from pathlib import Path

import yaml

from agents.lambdas.modules.agent_27_exchange import ExchangeAgent

from .conftest import FakeBedrockEmbed, FakeMetrics, FakeS3, FakeS3Vectors


def _entry(id_, name, tool, category, summary, tags):
    tag_list = ", ".join(f'"{t}"' for t in tags)
    return (
        f"---\nid: {id_}\ncontent_type: exchange\nname: {name}\ntool: {tool}\n"
        f"category: {category}\nsummary: {summary}\ntags: [{tag_list}]\n"
        f'install: |\n  1. do a thing\nsource_url: ""\n---\n\n'
        f"# {name}\n\n{summary}\n\n## Install\n\nSee above.\n"
    )


EXCHANGE_KEYS = {
    "exchange/claude-code/security-review.md": _entry(
        "exch-claude-code-security-review", "Security Review Skill", "claude-code", "skill",
        "Reviews pending changes for security issues.", ["security", "review"],
    ),
    "exchange/claude-code/test-gen.md": _entry(
        "exch-claude-code-test-gen", "Test Generator", "claude-code", "slash-command",
        "Scaffolds unit tests.", ["testing"],
    ),
    "exchange/copilot/instructions-python-aws.md": _entry(
        "exch-copilot-instructions-python-aws", "Copilot Instructions", "copilot", "config",
        "Copilot instructions for Python/AWS.", ["copilot", "python"],
    ),
    "exchange/generic/rag-prompt-pack.md": _entry(
        "exch-generic-rag-prompt-pack", "Cross-Tool RAG Prompt Pack", "generic", "prompt-pack",
        "Grounded retrieval prompts.", ["rag", "prompts"],
    ),
}


EXCHANGE_KEYS_IDS = [
    "exch-claude-code-security-review",
    "exch-claude-code-test-gen",
    "exch-copilot-instructions-python-aws",
    "exch-generic-rag-prompt-pack",
]


def _vec(key, content_type="exchange", idx=0):
    return {
        "key": f"{key}#{idx}",
        "metadata": {"file_path": key, "content_type": content_type, "chunk_index": idx},
    }


def _agent(vectors=None):
    return ExchangeAgent(
        vault_bucket="vault",
        s3=FakeS3(dict(EXCHANGE_KEYS)),
        bedrock=FakeBedrockEmbed(),
        s3vectors=FakeS3Vectors(vectors or []),
        metrics_client=FakeMetrics(),
    )


# --- list ------------------------------------------------------------------
def test_list_all():
    out = _agent().handle({"op": "list"})
    assert out["status"] == "ok"
    assert {e["id"] for e in out["entries"]} == set(EXCHANGE_KEYS_IDS)
    # list entries carry no body.
    assert all(e["body_markdown"] == "" for e in out["entries"])


def test_list_filters_by_tool():
    out = _agent().handle({"op": "list", "tool": "claude-code"})
    assert {e["id"] for e in out["entries"]} == {
        "exch-claude-code-security-review", "exch-claude-code-test-gen"
    }


def test_list_filters_by_category():
    out = _agent().handle({"op": "list", "category": "slash-command"})
    assert {e["id"] for e in out["entries"]} == {"exch-claude-code-test-gen"}


def test_list_filters_by_tool_and_category():
    out = _agent().handle({"op": "list", "tool": "claude-code", "category": "skill"})
    assert {e["id"] for e in out["entries"]} == {"exch-claude-code-security-review"}


def test_list_text_filter():
    out = _agent().handle({"op": "list", "query": "security"})
    assert {e["id"] for e in out["entries"]} == {"exch-claude-code-security-review"}


def test_default_op_is_list():
    out = _agent().handle({})
    assert out["status"] == "ok" and out["entries"]


# --- get -------------------------------------------------------------------
def test_get_by_id_returns_body_and_install():
    out = _agent().handle({"op": "get", "entry_id": "exch-claude-code-security-review"})
    assert out["status"] == "ok"
    assert out["entry"]["name"] == "Security Review Skill"
    assert out["entry"]["body_markdown"].startswith("# Security Review Skill")
    assert "do a thing" in out["entry"]["install"]


def test_get_via_id_alias_and_inferred_op():
    out = _agent().handle({"id": "exch-copilot-instructions-python-aws"})
    assert out["status"] == "ok" and out["entry"]["tool"] == "copilot"


def test_get_unknown_not_found():
    out = _agent().handle({"op": "get", "entry_id": "exch-nope"})
    assert out["status"] == "not_found"


# --- search ----------------------------------------------------------------
def test_search_scopes_to_exchange_content_type():
    vectors = [
        _vec("exchange/claude-code/security-review.md"),
        _vec("assets/some-asset.md", content_type="assets"),  # wrong type — excluded
        _vec("exchange/copilot/instructions-python-aws.md"),
    ]
    out = _agent(vectors=vectors).handle({"op": "search", "query": "security review"})
    ids = [e["id"] for e in out["entries"]]
    assert "exch-claude-code-security-review" in ids
    assert "exch-copilot-instructions-python-aws" in ids
    assert all(not e["file_path"].startswith("assets/") for e in out["entries"])


def test_search_requires_query():
    out = _agent().handle({"op": "search", "query": ""})
    assert out["status"] == "error"


# --- seed corpus typing ----------------------------------------------------
def test_no_untyped_entries():
    """Every real seed entry must carry content_type: exchange (no search pollution)."""
    root = Path(__file__).resolve().parents[4] / "vault" / "exchange"
    files = list(root.rglob("*.md"))
    assert len(files) >= 10, f"expected >=10 seed entries, found {len(files)}"
    for f in files:
        text = f.read_text(encoding="utf-8")
        fm = yaml.safe_load(text.split("---", 2)[1])
        assert fm.get("content_type") == "exchange", f"{f.name} missing content_type: exchange"
        assert fm.get("tool") in {"claude-code", "claude-cowork", "copilot", "kiro", "google", "generic"}
        assert fm.get("category") in {
            "skill", "slash-command", "mcp-server", "plugin", "prompt-pack", "config",
        }
