from agents.lambdas.workers.worker_20_vetting_scorer import VettingScorerWorker

from .conftest import FakeMetrics

CLEAN = {
    "data_residency": "configurable by region",
    "sub_processors_disclosed": True,
    "encryption_at_rest": True,
    "encryption_in_transit": True,
    "soc2_type2": True,
    "iso27001": True,
    "hipaa_baa": True,
    "trains_on_customer_data": False,
    "data_retention_days": 30,
    "sso": True,
}


def score(vetting, **ctx):
    return VettingScorerWorker(metrics_client=FakeMetrics()).handle(
        {"frontmatter": {"vetting": vetting}, **ctx}
    )


def test_clean_vendor_is_low_risk():
    out = score(CLEAN)
    assert out["status"] == "ok"
    assert out["risk_tier"] == "low"
    assert out["gaps"] == []
    assert all(c["result"] == "pass" for c in out["controls"])


def test_trains_on_customer_data_is_high():
    out = score({**CLEAN, "trains_on_customer_data": True})
    assert out["risk_tier"] == "high"
    # The training control shows as a gap.
    train = next(c for c in out["controls"] if "train" in c["control"].lower())
    assert train["result"] == "gap"


def test_phi_context_without_baa_is_high():
    # Otherwise-clean vendor, but no BAA + PHI data -> high (BAA is load-bearing).
    out = score({**CLEAN, "hipaa_baa": False}, data_sensitivity="phi")
    assert out["risk_tier"] == "high"


def test_no_baa_is_only_medium_without_phi():
    # Same vendor, public data -> the missing BAA is just one gap, not high.
    out = score({**CLEAN, "hipaa_baa": False}, data_sensitivity="public")
    assert out["risk_tier"] == "medium"


def test_several_gaps_is_high():
    out = score({
        **CLEAN, "sub_processors_disclosed": False, "iso27001": False, "sso": False,
    })
    assert out["risk_tier"] == "high"  # 3 gaps


def test_unknown_heavy_is_at_least_medium():
    # Sparse posture (open-source self-hosted): mostly unknowns.
    out = score({"data_residency": "self-hosted", "encryption_in_transit": True,
                 "trains_on_customer_data": False, "sso": False})
    assert out["risk_tier"] in ("medium", "high")
    assert any(c["result"] == "unknown" for c in out["controls"])


def test_controls_cover_full_catalog():
    out = score(CLEAN)
    assert len(out["controls"]) == 10  # fixed control catalog
    assert {"control", "result", "detail"} <= set(out["controls"][0])


def test_empty_vetting_all_unknown_high():
    out = score({})
    assert all(c["result"] == "unknown" for c in out["controls"])
    assert out["risk_tier"] == "high"  # >= 5 unknowns
