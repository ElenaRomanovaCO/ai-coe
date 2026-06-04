import json

import pytest

from agents.lib import models
from agents.lib.base_agent import BaseAgent, classify_outcome, instrumented
from agents.lib.cost_cap import OpusCapExceeded


class FakeCloudWatch:
    def __init__(self):
        self.calls = []

    def put_metric_data(self, **kwargs):
        self.calls.append(kwargs)


def test_instrumented_success_emits_log_and_metrics(capsys):
    cw = FakeCloudWatch()
    with instrumented(
        agent_id="AGENT-01",
        tool_name="search_knowledge_base",
        model_id=models.SONNET_4_6,
        metrics_client=cw,
    ) as usage:
        usage.tokens_in = 10
        usage.tokens_out = 5
        usage.cost_usd = 0.01

    rec = json.loads(capsys.readouterr().out.strip())
    assert rec["outcome"] == "success"
    assert rec["tokens_in"] == 10
    assert rec["latency_ms"] is not None
    assert cw.calls and cw.calls[0]["Namespace"] == "AICoE/Agents"


def test_instrumented_classifies_cap_exceeded_as_refused(capsys):
    cw = FakeCloudWatch()
    with pytest.raises(OpusCapExceeded):
        with instrumented(agent_id="AGENT-01", tool_name="t", metrics_client=cw):
            raise OpusCapExceeded(5.0, 1.0, 5.0)
    rec = json.loads(capsys.readouterr().out.strip())
    assert rec["outcome"] == "refused"


def test_classify_outcome_variants():
    assert classify_outcome(TimeoutError()) == "timeout"
    assert classify_outcome(ValueError("validation failed")) == "schema_failure"
    assert classify_outcome(RuntimeError("boom")) == "llm_error"


def test_base_agent_run_tool(capsys):
    cw = FakeCloudWatch()
    agent = BaseAgent(agent_id="AGENT-05", model_id=models.HAIKU_4_5, metrics_client=cw)

    def work(usage):
        usage.tokens_in = 3
        return "ok"

    assert agent.run_tool("describe_module", work) == "ok"
    rec = json.loads(capsys.readouterr().out.strip())
    assert rec["agent_id"] == "AGENT-05"
    assert rec["tokens_in"] == 3
    assert rec["model_id"] == models.HAIKU_4_5
