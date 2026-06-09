from agents.lambdas.workers.dimensions import DIMENSIONS, score_answer
from agents.lambdas.workers.worker_02_scorer import ScorerWorker

from .conftest import FakeMetrics, qa


def score(history):
    return ScorerWorker(metrics_client=FakeMetrics()).handle({"history": history})


def test_score_answer_rule():
    assert score_answer("none, no tooling, manual, ad hoc") <= 1
    assert score_answer("production, automated pipelines, formal governance") >= 4
    assert score_answer("") == 2  # baseline


def test_all_strong_high_stage():
    strong = "production, deployed, monitored, formal policies, committed budget, prioritized roi"
    history = [qa(d, strong) for d in DIMENSIONS]
    out = score(history)
    assert out["status"] == "ok"
    assert out["stage"] >= 4
    assert set(out["dimension_scores"]) == set(DIMENSIONS)


def test_all_weak_low_stage():
    weak = "none, no, manual, ad hoc, not sure, nothing"
    out = score([qa(d, weak) for d in DIMENSIONS])
    assert out["stage"] <= 1


def test_deterministic():
    history = [qa(d, "we have some pilots, exploring, informal") for d in DIMENSIONS]
    assert score(history) == score(history)


def test_rationale_mentions_stage():
    out = score([qa(d, "production formal budget") for d in DIMENSIONS])
    assert f"stage {out['stage']}" in out["rationale"]
