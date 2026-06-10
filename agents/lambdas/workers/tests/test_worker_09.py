from agents.lambdas.workers.worker_09_regulation_mapper import RegulationMapperWorker

from .conftest import FakeMetrics


def mapr(args):
    return RegulationMapperWorker(metrics_client=FakeMetrics()).handle(args)


def _fw(out, name):
    return next((f for f in out["frameworks"] if f["framework"] == name), None)


def test_automated_lending_is_high_tier():
    out = mapr(
        {
            "use_case": "automated lending decision",
            "decision_type": "automated",
            "geography": "US",
            "industry": "financial-services",
            "data_types": ["financial"],
        }
    )
    assert out["status"] == "ok"
    eu = _fw(out, "EU AI Act")
    assert eu["tier"] == "high"
    assert eu["reg_id"] == "reg-eu-ai-act"


def test_recommendation_only_high_stakes_is_limited():
    out = mapr(
        {
            "use_case": "credit scoring",
            "decision_type": "recommendation-only",
            "geography": "US",
            "industry": "financial-services",
            "data_types": [],
        }
    )
    assert _fw(out, "EU AI Act")["tier"] == "limited"


def test_non_sensitive_is_minimal():
    out = mapr(
        {
            "use_case": "internal document search",
            "decision_type": "assisted",
            "geography": "US",
            "industry": "retail",
            "data_types": [],
        }
    )
    assert _fw(out, "EU AI Act")["tier"] == "minimal"


def test_healthcare_attaches_hipaa_with_existing_reg_id():
    out = mapr(
        {
            "use_case": "clinical decision support",
            "decision_type": "assisted",
            "geography": "US",
            "industry": "healthcare",
            "data_types": ["phi"],
        }
    )
    hipaa = _fw(out, "HIPAA")
    assert hipaa is not None and hipaa["reg_id"] == "reg-hipaa-ai"


def test_financial_attaches_ffiec_with_existing_reg_id():
    out = mapr(
        {
            "use_case": "loan underwriting",
            "decision_type": "automated",
            "geography": "US",
            "industry": "financial-services",
            "data_types": [],
        }
    )
    ffiec = _fw(out, "FFIEC")
    assert ffiec is not None and ffiec["reg_id"] == "reg-ffiec-ai"


def test_no_dangling_reg_ids():
    # Every attached reg_id must be one of the three confirmed-to-exist vault regs.
    out = mapr(
        {
            "use_case": "clinical lending",
            "decision_type": "automated",
            "geography": "EU",
            "industry": "healthcare",
            "data_types": ["phi"],
        }
    )
    allowed = {"reg-eu-ai-act", "reg-hipaa-ai", "reg-ffiec-ai"}
    for f in out["frameworks"]:
        if f["reg_id"] is not None:
            assert f["reg_id"] in allowed


def test_regulatory_tier_dict_mirrors_frameworks():
    out = mapr(
        {
            "use_case": "hiring screener",
            "decision_type": "automated",
            "geography": "US",
            "industry": "cross-industry",
            "data_types": [],
        }
    )
    assert out["regulatory_tier"]["EU AI Act"] == _fw(out, "EU AI Act")["tier"]
