"""AGENT-05 governance pipeline + the AGENT-05 -> workers wire contract.

Exercises the full mechanical pipeline (WORKER-04 -> WORKER-05 -> summary -> vault)
with real workers behind injected fakes; the single Sonnet summary call is faked.
"""

import json

from agents.lambdas.modules.agent_05_governance import GovernanceAgent
from agents.lambdas.modules.worker_client import WorkerInvoker
from agents.lambdas.workers import router as workers_router
from agents.lambdas.workers.worker_04_regulation_finder import RegulationFinderWorker
from agents.lambdas.workers.worker_05_checklist_generator import ChecklistGeneratorWorker

from .conftest import FakeMetrics, FakeS3


def _reg(id_, name, geo, scope, tags):
    scope_list = ", ".join(f'"{s}"' for s in scope)
    tag_list = ", ".join(f'"{t}"' for t in tags)
    return (
        f"---\nid: {id_}\nname: {name}\ngeo: {geo}\n"
        f"industry_scope: [{scope_list}]\nstatus: in-effect\ntags: [{tag_list}]\n---\n\n"
        f"# {name}\n\n## Risk tiers\n\nText.\n\n## What this means\n\nText.\n"
    )


REG_KEYS = {
    "regs/eu/ai-act/eu-ai-act.md": _reg(
        "reg-eu-ai-act", "EU Artificial Intelligence Act", "eu",
        ["cross-industry", "healthcare"], ["eu", "ai-act", "high-risk"],
    ),
    "regs/us-federal/hipaa/hipaa-ai.md": _reg(
        "reg-hipaa-ai", "HIPAA — AI and PHI", "us-federal",
        ["healthcare"], ["hipaa", "phi", "baa"],
    ),
}


class FakeBedrockClient:
    """Stands in for BedrockClient.converse — returns a canned summary."""

    def __init__(self, text="Executive summary of the governance review."):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


class FakeWorkers:
    def __init__(self, s3):
        self.s3 = s3

    def invoke(self, worker_id, args):
        m = FakeMetrics()
        if worker_id == "WORKER-04":
            w = RegulationFinderWorker(vault_bucket="vault", s3=self.s3, metrics_client=m)
            return w.handle(args)
        if worker_id == "WORKER-05":
            return ChecklistGeneratorWorker(metrics_client=m).handle(args)
        return {"status": "not_implemented"}


def _agent(bedrock=None):
    s3 = FakeS3(dict(REG_KEYS))
    agent = GovernanceAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=s3,
        bedrock_client=bedrock or FakeBedrockClient(),
        worker_invoker=FakeWorkers(s3),
        metrics_client=FakeMetrics(),
    )
    return agent, s3


CHECK = {
    "op": "check",
    "industry": "healthcare",
    "geography": "EU",
    "data_types": ["phi"],
    "ai_use_case_type": "clinical decision support",
    "display_name": "Dana",
}


def test_check_runs_pipeline_and_writes_vault():
    agent, s3 = _agent()
    out = agent.handle(CHECK)
    assert out["status"] == "ok"
    reg_ids = {r["id"] for r in out["regulations"]}
    assert {"reg-eu-ai-act", "reg-hipaa-ai"} <= reg_ids  # smoke expectation
    assert out["checklist"]
    assert out["summary"] == "Executive summary of the governance review."
    # Review markdown written to the vault under reviews/governance/<slug>/.
    assert out["vault_file_path"].startswith("reviews/governance/dana/")
    md = s3.objects[out["vault_file_path"]]
    assert "type: governance-review" in md
    assert "Business Associate Agreement" in md  # a HIPAA checklist item rendered


def test_checklist_references_at_least_two_regulations():
    agent, _ = _agent()
    out = agent.handle(CHECK)
    linked = {rid for c in out["checklist"] for rid in c.get("regulation_links", [])}
    assert len(linked) >= 2  # DoD: checklist references 2-3 regulations


def test_summary_falls_back_when_llm_errors():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("bedrock down")

    agent, _ = _agent(bedrock=Boom())
    out = agent.handle(CHECK)
    assert out["status"] == "ok"
    assert "regulation" in out["summary"].lower()  # deterministic fallback used


def test_get_and_list_after_check():
    agent, _ = _agent()
    out = agent.handle(CHECK)
    rid = out["review_id"]
    got = agent.handle({"op": "get", "review_id": rid})
    assert got["status"] == "ok" and got["review_id"] == rid
    listed = agent.handle({"op": "list", "display_name": "Dana"})
    assert listed["status"] == "ok"
    assert [r["review_id"] for r in listed["reviews"]] == [rid]


def test_check_requires_core_inputs():
    agent, _ = _agent()
    assert agent.handle({"op": "check", "industry": "healthcare"})["status"] == "error"


def test_get_unknown_review_not_found():
    agent, _ = _agent()
    assert agent.handle({"op": "get", "review_id": "gov-nope"})["status"] == "not_found"


# --- AGENT-05 -> workers wire contract (deploy-time-only path) --------------
class RouterBackedLambda:
    def __init__(self, route_fn):
        self.route = route_fn
        self.last = None

    def invoke(self, *, FunctionName, Payload):
        import io

        self.last = json.loads(Payload.decode("utf-8"))
        return {"Payload": io.BytesIO(json.dumps(self.route(self.last)).encode("utf-8"))}


def test_worker_invoker_contract_checklist():
    fake = RouterBackedLambda(workers_router.route)
    invoker = WorkerInvoker(lambda_client=fake)
    out = invoker.invoke("WORKER-05", {"regulations": [], "engagement_context": {"data_types": []}})
    assert out["status"] == "ok" and out["checklist"]
    assert fake.last["worker_id"] == "WORKER-05"
