"""AGENT-28 ROI calculator: deterministic math + one Sonnet narrative + sessions I/O."""

from agents.lambdas.modules.agent_28_roi import RoiCalculatorAgent, RoiRequest, compute

from .conftest import FakeMetrics, FakeS3


class FakeSonnet:
    def __init__(self, text="This project pays back quickly and returns strongly."):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


def _agent(s3=None, sonnet=None):
    return RoiCalculatorAgent(
        sessions_bucket="sessions",
        s3=s3 if s3 is not None else FakeS3({}),
        bedrock_client=sonnet or FakeSonnet(),
        metrics_client=FakeMetrics(),
    )


BASE = {
    "op": "calculate",
    "display_name": "Dana",
    "project_name": "Doc Processing Assistant",
    "industry": "healthcare",
    "build_cost_usd": 100000,
    "run_cost_usd_yr": 20000,
    "hours_saved_yr": 2000,
    "loaded_hourly_rate_usd": 80,
    "horizon_years": 3,
}


# --- compute (deterministic, no LLM) ---------------------------------------
def test_compute_core_figures():
    r = compute(RoiRequest.model_validate(BASE))
    assert r.total_cost_usd == 160000  # 100k build + 20k*3 run
    assert r.annual_value_usd == 160000  # 2000h * $80
    assert r.net_value_usd == 320000  # 160k*3 - 160k
    assert r.roi_pct == 200.0
    assert r.payback_months == 8.6  # 100k / (160k-20k) * 12


def test_compute_includes_revenue_and_other_benefits():
    r = compute(RoiRequest.model_validate(
        {**BASE, "revenue_uplift_usd_yr": 50000, "other_benefit_usd_yr": 10000}
    ))
    assert r.annual_value_usd == 220000  # 160k + 50k + 10k


def test_compute_zero_build_cost_pays_back_immediately():
    r = compute(RoiRequest.model_validate({**BASE, "build_cost_usd": 0}))
    assert r.payback_months == 0.0


def test_compute_never_pays_back_when_value_below_run_cost():
    r = compute(RoiRequest.model_validate(
        {**BASE, "hours_saved_yr": 100, "loaded_hourly_rate_usd": 50, "run_cost_usd_yr": 20000}
    ))
    # annual_value 5000 < run_cost 20000 -> negative net cash -> no payback
    assert r.payback_months is None


def test_compute_zero_total_cost_guards_divide_by_zero():
    r = compute(RoiRequest.model_validate(
        {"build_cost_usd": 0, "run_cost_usd_yr": 0, "hours_saved_yr": 100,
         "loaded_hourly_rate_usd": 50, "horizon_years": 2}
    ))
    assert r.total_cost_usd == 0
    assert r.roi_pct == 0.0  # guarded, not a ZeroDivisionError
    assert r.net_value_usd == 10000  # (100h * $50) * 2yr - $0


# --- narrative -------------------------------------------------------------
def test_calculate_uses_sonnet_narrative():
    fake = FakeSonnet("Strong business case here.")
    out = _agent(sonnet=fake).handle(dict(BASE))
    assert out["status"] == "ok"
    assert out["result"]["narrative"] == "Strong business case here."
    assert fake.calls == 1


def test_calculate_falls_back_when_llm_errors():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("sonnet down")

    out = _agent(sonnet=Boom()).handle(dict(BASE))
    assert out["status"] == "ok"
    # Templated fallback embeds the computed figures.
    assert "200.0% ROI" in out["result"]["narrative"]
    assert "8.6 months" in out["result"]["narrative"]


# --- persistence (sessions only) -------------------------------------------
def test_calculate_persists_to_sessions_and_round_trips():
    s3 = FakeS3({})
    agent = _agent(s3=s3)
    out = agent.handle(dict(BASE))
    rid = out["roi_id"]
    # Stored in the sessions bucket under roi/, never the vault.
    assert f"roi/dana/{rid}.json" in s3.objects
    got = _agent(s3=s3).handle({"op": "get", "roi_id": rid})
    assert got["status"] == "ok"
    assert got["result"]["roi_pct"] == 200.0
    assert got["inputs"]["project_name"] == "Doc Processing Assistant"


def test_get_via_id_alias_and_not_found():
    s3 = FakeS3({})
    agent = _agent(s3=s3)
    rid = agent.handle(dict(BASE))["roi_id"]
    assert _agent(s3=s3).handle({"id": rid})["status"] == "ok"
    assert _agent(s3=s3).handle({"op": "get", "roi_id": "roi-nope"})["status"] == "not_found"


def test_list_returns_caller_results():
    s3 = FakeS3({})
    agent = _agent(s3=s3)
    agent.handle(dict(BASE))
    agent.handle({**BASE, "project_name": "Second"})
    out = _agent(s3=s3).handle({"op": "list", "display_name": "Dana"})
    assert out["status"] == "ok" and len(out["results"]) == 2
    assert {r["project_name"] for r in out["results"]} == {"Doc Processing Assistant", "Second"}


def test_calculate_requires_display_name():
    assert _agent().handle({"op": "calculate"})["status"] == "error"
