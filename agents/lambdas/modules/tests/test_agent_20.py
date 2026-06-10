"""AGENT-20 ethics pipeline + the AGENT-20 -> workers wire contract.

Real workers behind injected fakes; the single Sonnet summary call is faked.
"""

import json

from agents.lambdas.modules.agent_20_ethics import EthicsAgent
from agents.lambdas.modules.worker_client import WorkerInvoker
from agents.lambdas.workers import router as workers_router
from agents.lambdas.workers.worker_08_bias_analyzer import BiasAnalyzerWorker
from agents.lambdas.workers.worker_09_regulation_mapper import RegulationMapperWorker

from .conftest import FakeMetrics, FakeS3


class FakeBedrockClient:
    def __init__(self, text="Ethics review executive summary."):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


class FakeWorkers:
    def invoke(self, worker_id, args):
        m = FakeMetrics()
        if worker_id == "WORKER-08":
            return BiasAnalyzerWorker(metrics_client=m).handle(args)
        if worker_id == "WORKER-09":
            return RegulationMapperWorker(metrics_client=m).handle(args)
        return {"status": "not_implemented"}


def _agent(bedrock=None):
    s3 = FakeS3({})
    agent = EthicsAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=s3,
        bedrock_client=bedrock or FakeBedrockClient(),
        worker_invoker=FakeWorkers(),
        metrics_client=FakeMetrics(),
    )
    return agent, s3


CHECK = {
    "op": "check",
    "use_case": "automated lending decision",
    "data_types": ["financial", "historical"],
    "affected_populations": ["racial minorities"],
    "decision_type": "automated",
    "geography": "US",
    "industry": "financial-services",
    "display_name": "Pat",
}


def test_check_covers_all_five_areas_and_writes_vault():
    agent, s3 = _agent()
    out = agent.handle(CHECK)
    assert out["status"] == "ok"
    # All five areas present and non-empty (DoD).
    assert out["bias_risks"]
    assert out["fairness_considerations"]
    assert out["explainability_requirements"]
    assert out["human_oversight_recommendations"]
    assert out["regulatory_tier"]
    # EU AI Act high tier for automated lending; summary is the (faked) LLM text.
    assert out["regulatory_tier"]["EU AI Act"] == "high"
    assert out["summary"] == "Ethics review executive summary."
    assert out["vault_file_path"].startswith("reviews/ethics/pat/")
    md = s3.objects[out["vault_file_path"]]
    assert "type: ethics-review" in md
    assert "## Bias risks" in md


def test_summary_falls_back_when_llm_errors():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("bedrock down")

    agent, _ = _agent(bedrock=Boom())
    out = agent.handle(CHECK)
    assert out["status"] == "ok"
    assert "EU AI Act tier" in out["summary"]  # deterministic fallback


def test_no_dangling_framework_reg_ids():
    agent, _ = _agent()
    out = agent.handle(CHECK)
    allowed = {"reg-eu-ai-act", "reg-hipaa-ai", "reg-ffiec-ai"}
    for f in out["frameworks"]:
        if f.get("reg_id") is not None:
            assert f["reg_id"] in allowed


def test_get_and_list_after_check():
    agent, _ = _agent()
    out = agent.handle(CHECK)
    rid = out["review_id"]
    got = agent.handle({"op": "get", "review_id": rid})
    assert got["status"] == "ok" and got["review_id"] == rid
    listed = agent.handle({"op": "list", "display_name": "Pat"})
    assert [r["review_id"] for r in listed["reviews"]] == [rid]


def test_check_requires_use_case():
    agent, _ = _agent()
    assert agent.handle({"op": "check", "industry": "healthcare"})["status"] == "error"


# --- AGENT-20 -> workers wire contract --------------------------------------
class RouterBackedLambda:
    def __init__(self, route_fn):
        self.route = route_fn
        self.last = None

    def invoke(self, *, FunctionName, Payload):
        import io

        self.last = json.loads(Payload.decode("utf-8"))
        return {"Payload": io.BytesIO(json.dumps(self.route(self.last)).encode("utf-8"))}


def test_worker_invoker_contract_bias():
    fake = RouterBackedLambda(workers_router.route)
    invoker = WorkerInvoker(lambda_client=fake)
    out = invoker.invoke(
        "WORKER-08", {"decision_type": "automated", "data_types": [], "affected_populations": []}
    )
    assert out["status"] == "ok" and out["bias_risks"]
    assert fake.last["worker_id"] == "WORKER-08"
