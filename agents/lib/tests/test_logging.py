import json

import pytest

from agents.lib.logging import build_record, hash_display_name, log_invocation


def test_hash_display_name():
    assert hash_display_name("Alice").startswith("sha256:")
    assert hash_display_name(None) is None
    assert hash_display_name("") is None


def test_build_record_shape():
    rec = build_record(
        request_id="req_1",
        agent_id="AGENT-01",
        outcome="success",
        session_id="sess_1",
        display_name="Bob",
        tool_name="search_knowledge_base",
        model_id="anthropic.claude-sonnet-4-6",
        tokens_in=5,
        tokens_out=6,
        cost_usd=0.001,
        latency_ms=42,
        parent_agent="AGENT-00",
        depth=2,
    )
    for key in ("ts", "request_id", "session_id", "agent_id", "outcome", "trace"):
        assert key in rec
    assert rec["display_name_hash"].startswith("sha256:")
    assert rec["trace"] == {"parent_agent": "AGENT-00", "depth": 2}
    assert rec["ts"].endswith("Z")


def test_log_invocation_emits_valid_json(capsys):
    log_invocation(request_id="req_2", agent_id="AGENT-02", outcome="success")
    out = capsys.readouterr().out.strip()
    parsed = json.loads(out)
    assert parsed["request_id"] == "req_2"


def test_log_invocation_requires_core_fields():
    with pytest.raises(ValueError):
        log_invocation(request_id="", agent_id="AGENT-02", outcome="success")
