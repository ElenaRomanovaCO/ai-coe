from agents.lambdas.workers.worker_03_recommender import RecommenderWorker

from .conftest import ASSET_KEYS, FakeMetrics, FakeS3


def recommend(args):
    agent = RecommenderWorker(
        vault_bucket="vault-bucket", s3=FakeS3(ASSET_KEYS), metrics_client=FakeMetrics()
    )
    return agent.handle(args)


def test_filters_by_industry_and_stage():
    out = recommend({"stage": 2, "industry": "healthcare", "weak_dimensions": []})
    assert out["status"] == "ok"
    industries = {r["industry"] for r in out["recommendations"]}
    # healthcare + cross-industry allowed; financial-services excluded.
    assert "financial-services" not in industries
    # stage range 1..3 -> all healthcare/cross assets qualify.
    assert {r["id"] for r in out["recommendations"]} == {
        "ref-arch-clinical",
        "pattern-triage",
        "kickoff-template",
    }


def test_weak_dimension_boosts_governance_asset():
    out = recommend({"stage": 2, "industry": "healthcare", "weak_dimensions": ["governance"]})
    # ref-arch-clinical has a 'governance' tag -> boosted to the top.
    assert out["recommendations"][0]["id"] == "ref-arch-clinical"


def test_caps_at_top_k():
    out = recommend({"stage": 2, "industry": "", "weak_dimensions": [], "top_k": 2})
    assert len(out["recommendations"]) == 2


def test_relaxes_when_no_industry_match():
    # An industry with no assets -> falls back to stage-only, then all, never empty.
    out = recommend({"stage": 2, "industry": "energy", "weak_dimensions": []})
    assert len(out["recommendations"]) >= 1
