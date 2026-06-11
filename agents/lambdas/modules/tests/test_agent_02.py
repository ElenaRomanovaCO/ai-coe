"""AGENT-02 assessment flow + the AGENT-02 -> workers wire contract.

Uses the REAL workers (constructed with injected fakes) so the full delegation
path is exercised in-process without AWS.
"""

import json

from agents.lambdas.modules.agent_02_assessment import AssessmentAgent
from agents.lambdas.modules.worker_client import WorkerInvoker
from agents.lambdas.workers import router as workers_router
from agents.lambdas.workers.worker_01_question_picker import QuestionPickerWorker
from agents.lambdas.workers.worker_02_scorer import ScorerWorker
from agents.lambdas.workers.worker_03_recommender import RecommenderWorker

from .conftest import ASSET_KEYS, FakeMetrics, FakeS3

STRONG = "production, formal governance, committed budget, prioritized, automated"
WEAK = "none, no tooling, manual, ad hoc, not sure, nothing"


class FakeWorkers:
    """Dispatches to real worker instances with injected fakes (no AWS)."""

    def __init__(self, s3):
        self.s3 = s3

    def invoke(self, worker_id, args):
        m = FakeMetrics()
        if worker_id == "WORKER-01":
            return QuestionPickerWorker(metrics_client=m).handle(args)
        if worker_id == "WORKER-02":
            return ScorerWorker(metrics_client=m).handle(args)
        if worker_id == "WORKER-03":
            w = RecommenderWorker(vault_bucket="vault", s3=self.s3, metrics_client=m)
            return w.handle(args)
        return {"status": "not_implemented"}


def _agent():
    s3 = FakeS3(dict(ASSET_KEYS))
    return AssessmentAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=s3,
        worker_invoker=FakeWorkers(s3),
        metrics_client=FakeMetrics(),
    ), s3


def _run(agent, answer, *, max_turns=20):
    start = agent.handle(
        {"op": "start", "display_name": "Alex", "client_context": "healthcare insurer"}
    )
    assert start["status"] == "ok"
    aid = start["assessment_id"]
    turns = 0
    last = start
    while not last.get("is_complete"):
        turns += 1
        assert turns <= max_turns
        last = agent.handle({"op": "answer", "assessment_id": aid, "user_answer": answer})
        assert last["status"] == "ok"
    return aid, turns, last["result"]


def test_full_run_strong_eight_turns_and_result():
    agent, s3 = _agent()
    aid, turns, result = _run(agent, STRONG)
    assert turns == 8  # all-strong -> minimum-length adaptive flow
    assert result["assessment_id"] == aid
    assert result["stage"] >= 4
    assert len(result["dimension_scores"]) == 6
    assert result["recommendations"]  # WORKER-03 returned items
    assert result["vault_file_path"].startswith("assessments/alex/")
    # Result markdown was written to the vault bucket, tagged as a generated artifact
    # so chat search scopes it out of curated KB results.
    md = s3.objects[result["vault_file_path"]]
    assert "content_type: assessment" in md
    assert "generated: true" in md
    assert f"stage: {result['stage']}" in md


def test_weak_run_extends_to_twelve():
    agent, _ = _agent()
    _, turns, result = _run(agent, WEAK)
    assert turns == 12
    assert result["stage"] <= 1


def test_deterministic_same_inputs_same_stage():
    a1, _ = _agent()
    a2, _ = _agent()
    _, _, r1 = _run(a1, STRONG)
    _, _, r2 = _run(a2, STRONG)
    assert r1["stage"] == r2["stage"]
    assert r1["dimension_scores"] == r2["dimension_scores"]


def test_get_and_list_after_completion():
    agent, _ = _agent()
    aid, _, result = _run(agent, STRONG)
    got = agent.handle({"op": "get", "assessment_id": aid})
    assert got["is_complete"] and got["result"]["stage"] == result["stage"]
    listed = agent.handle({"op": "list", "display_name": "Alex"})
    assert listed["status"] == "ok"
    assert [a["assessment_id"] for a in listed["assessments"]] == [aid]


def test_industry_inferred_from_context():
    agent, s3 = _agent()
    _, _, result = _run(agent, STRONG)
    md = s3.objects[result["vault_file_path"]]
    assert "industry: healthcare" in md


def test_start_requires_display_name():
    agent, _ = _agent()
    assert agent.handle({"op": "start"})["status"] == "error"


# --- AGENT-02 -> workers wire contract (the deploy-time-only path) ----------
class RouterBackedLambda:
    def __init__(self, route_fn):
        self.route = route_fn
        self.last = None

    def invoke(self, *, FunctionName, Payload):
        import io

        self.last = json.loads(Payload.decode("utf-8"))
        result = self.route(self.last)
        return {"Payload": io.BytesIO(json.dumps(result).encode("utf-8"))}


def test_worker_invoker_contract():
    fake = RouterBackedLambda(workers_router.route)
    invoker = WorkerInvoker(lambda_client=fake)
    out = invoker.invoke("WORKER-01", {"history": []})
    assert out["status"] == "ok" and out["is_final"] is False
    assert fake.last == {"worker_id": "WORKER-01", "args": {"history": []}}
