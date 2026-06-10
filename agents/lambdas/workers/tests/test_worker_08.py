from agents.lambdas.workers.worker_08_bias_analyzer import BiasAnalyzerWorker

from .conftest import FakeMetrics


def analyze(args):
    return BiasAnalyzerWorker(metrics_client=FakeMetrics()).handle(args)


def _categories(out):
    return {r["category"] for r in out["bias_risks"]}


def test_always_emits_representation_and_automation():
    out = analyze(
        {"use_case": "x", "data_types": [], "affected_populations": [], "decision_type": "assisted"}
    )
    assert out["status"] == "ok"
    cats = _categories(out)
    assert {"data_representation", "automation_bias"} <= cats


def test_automated_decision_raises_automation_severity():
    auto = analyze(
        {
            "use_case": "x",
            "decision_type": "automated",
            "data_types": [],
            "affected_populations": [],
        }
    )
    rec = analyze(
        {
            "use_case": "x",
            "decision_type": "recommendation-only",
            "data_types": [],
            "affected_populations": [],
        }
    )
    auto_sev = next(r["severity"] for r in auto["bias_risks"] if r["category"] == "automation_bias")
    rec_sev = next(r["severity"] for r in rec["bias_risks"] if r["category"] == "automation_bias")
    assert auto_sev == "high"
    assert rec_sev == "low"


def test_protected_population_raises_representation_severity():
    out = analyze(
        {
            "use_case": "lending",
            "data_types": [],
            "affected_populations": ["racial minorities"],
            "decision_type": "automated",
        }
    )
    rep = next(r for r in out["bias_risks"] if r["category"] == "data_representation")
    assert rep["severity"] == "high"


def test_historical_data_adds_sample_bias():
    out = analyze(
        {
            "use_case": "credit",
            "data_types": ["historical", "financial"],
            "affected_populations": [],
            "decision_type": "automated",
        }
    )
    assert "sample_bias" in _categories(out)


def test_recommendation_only_skips_label_bias():
    out = analyze(
        {
            "use_case": "x",
            "data_types": [],
            "affected_populations": [],
            "decision_type": "recommendation-only",
        }
    )
    assert "label_bias" not in _categories(out)


def test_every_risk_has_mitigation_and_id():
    out = analyze(
        {
            "use_case": "hiring",
            "data_types": ["behavioral"],
            "affected_populations": ["women"],
            "decision_type": "automated",
        }
    )
    for i, r in enumerate(out["bias_risks"], start=1):
        assert r["id"] == f"bias-{i:02d}"
        assert r["mitigation"]


def test_deterministic_same_inputs():
    args = {
        "use_case": "hiring",
        "data_types": ["behavioral"],
        "affected_populations": ["women"],
        "decision_type": "automated",
    }
    assert analyze(args)["bias_risks"] == analyze(args)["bias_risks"]
