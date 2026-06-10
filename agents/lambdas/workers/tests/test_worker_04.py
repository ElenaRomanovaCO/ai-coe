from agents.lambdas.workers.worker_04_regulation_finder import RegulationFinderWorker

from .conftest import REG_KEYS, FakeMetrics, FakeS3


def find(args):
    w = RegulationFinderWorker(
        vault_bucket="vault", s3=FakeS3(REG_KEYS), metrics_client=FakeMetrics()
    )
    return w.handle(args)


def test_healthcare_eu_phi_surfaces_eu_act_and_hipaa():
    # The task's smoke case: even with geography=EU, HIPAA still surfaces on the
    # healthcare + PHI signals (soft scoring, not a hard geo gate).
    out = find(
        {
            "industry": "healthcare",
            "geography": "EU",
            "data_types": ["phi"],
            "ai_use_case_type": "clinical decision support",
        }
    )
    assert out["status"] == "ok"
    ids = {r["id"] for r in out["regulations"]}
    assert "reg-eu-ai-act" in ids
    assert "reg-hipaa-ai" in ids


def test_sorted_by_relevance_desc():
    out = find(
        {
            "industry": "healthcare",
            "geography": "EU",
            "data_types": ["phi"],
            "ai_use_case_type": "clinical decision support",
        }
    )
    scores = [r["relevance_score"] for r in out["regulations"]]
    assert scores == sorted(scores, reverse=True)
    # EU AI Act scores highest here: geo(eu)=3 + industry(healthcare)=2 + cross=1.
    assert out["regulations"][0]["id"] == "reg-eu-ai-act"


def test_applicable_clauses_parsed_from_headings():
    out = find(
        {"industry": "healthcare", "geography": "eu", "data_types": [], "ai_use_case_type": "x"}
    )
    eu = next(r for r in out["regulations"] if r["id"] == "reg-eu-ai-act")
    assert "Risk tiers" in eu["applicable_clauses"]


def test_financial_us_matches_ffiec_not_hipaa():
    out = find(
        {
            "industry": "financial-services",
            "geography": "US",
            "data_types": ["financial"],
            "ai_use_case_type": "credit scoring",
        }
    )
    ids = {r["id"] for r in out["regulations"]}
    assert "reg-ffiec-ai" in ids
    assert "reg-hipaa-ai" not in ids


def test_no_signal_returns_empty():
    out = find(
        {
            "industry": "agriculture",
            "geography": "antarctica",
            "data_types": [],
            "ai_use_case_type": "zzz",
        }
    )
    assert out["status"] == "ok"
    assert out["regulations"] == []


def test_top_k_caps():
    out = find(
        {
            "industry": "healthcare",
            "geography": "eu",
            "data_types": ["phi", "pii"],
            "ai_use_case_type": "clinical",
            "top_k": 1,
        }
    )
    assert len(out["regulations"]) == 1
