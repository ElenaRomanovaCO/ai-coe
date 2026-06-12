"""AGENT-30 vendor vetting: list / get / assess / set_status.

Runs the real WORKER-20 behind a fake invoker; the single Sonnet narrative is faked.
Vendor reads + the org-shared sidecar run against in-memory S3.
"""

from agents.lambdas.modules.agent_30_vendor_vetting import VendorVettingAgent
from agents.lambdas.workers.worker_20_vetting_scorer import VettingScorerWorker

from .conftest import FakeMetrics, FakeS3


def _vendor(id_, category, vetting_lines):
    return (
        f"---\nid: {id_}\ncategory: {category}\n"
        f'vendors_compared: ["A", "B"]\ncriteria: ["x"]\nlast_verified: "2026-05-20"\n'
        f"vetting:\n{vetting_lines}\n---\n\n# {id_}\n\nComparison body.\n"
    )


CLEAN_VETTING = (
    "  data_residency: \"configurable\"\n  sub_processors_disclosed: true\n"
    "  encryption_at_rest: true\n  encryption_in_transit: true\n  soc2_type2: true\n"
    "  iso27001: true\n  hipaa_baa: true\n  trains_on_customer_data: false\n"
    "  data_retention_days: 30\n  sso: true"
)
TRAINS_VETTING = (
    "  data_residency: \"US\"\n  encryption_at_rest: true\n  encryption_in_transit: true\n"
    "  soc2_type2: true\n  hipaa_baa: false\n  trains_on_customer_data: true\n  sso: true"
)

VENDOR_KEYS = {
    "vendors/clean.md": _vendor("vendor-clean", "cloud-ai-platform", CLEAN_VETTING),
    "vendors/risky.md": _vendor("vendor-risky", "llm-provider", TRAINS_VETTING),
}


class FakeBedrock:
    def __init__(self, text="Risk note: medium; close the listed gaps before approval."):
        self.text = text

    def converse(self, **kwargs):
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


class FakeWorkers:
    def invoke(self, worker_id, args):
        if worker_id == "WORKER-20":
            return VettingScorerWorker(metrics_client=FakeMetrics()).handle(args)
        return {"status": "not_implemented"}


def _agent(s3=None, bedrock=None):
    return VendorVettingAgent(
        vault_bucket="vault",
        s3=s3 if s3 is not None else FakeS3(dict(VENDOR_KEYS)),
        bedrock_client=bedrock or FakeBedrock(),
        worker_invoker=FakeWorkers(),
        metrics_client=FakeMetrics(),
    )


# --- list / get ------------------------------------------------------------
def test_list_vendors_default_unvetted():
    out = _agent().handle({"op": "list"})
    assert out["status"] == "ok"
    by_id = {v["vendor_id"]: v for v in out["vendors"]}
    assert {"vendor-clean", "vendor-risky"} <= set(by_id)
    assert by_id["vendor-clean"]["approval_status"] == "unvetted"
    assert by_id["vendor-clean"]["risk_tier"] is None  # not assessed yet


def test_get_vendor_profile():
    out = _agent().handle({"op": "get", "vendor_id": "vendor-clean"})
    assert out["status"] == "ok"
    assert out["vendor"]["category"] == "cloud-ai-platform"
    assert out["vetting"]["approval_status"] == "unvetted"


def test_get_unknown_not_found():
    assert _agent().handle({"op": "get", "vendor_id": "vendor-nope"})["status"] == "not_found"


# --- assess ----------------------------------------------------------------
def test_assess_clean_vendor_low_and_persists():
    s3 = FakeS3(dict(VENDOR_KEYS))
    out = _agent(s3=s3).handle({"op": "assess", "vendor_id": "vendor-clean"})
    assert out["status"] == "ok"
    assert out["risk_tier"] == "low"
    assert len(out["controls"]) == 10
    assert out["narrative"]
    # Persisted to the org-shared sidecar (vault, non-indexed .json).
    assert "vendors/_vetting/vendor-clean.json" in s3.objects
    # And now surfaces on the browse list.
    lst = _agent(s3=s3).handle({"op": "list"})
    clean = next(v for v in lst["vendors"] if v["vendor_id"] == "vendor-clean")
    assert clean["risk_tier"] == "low"


def test_assess_training_vendor_is_high():
    out = _agent().handle({"op": "assess", "vendor_id": "vendor-risky"})
    assert out["risk_tier"] == "high"
    assert any("train" in g.lower() for g in out["gaps"])


def test_assess_phi_context_without_baa_is_high():
    # clean vendor has BAA; risky vendor lacks it -> PHI makes it high regardless of training
    out = _agent().handle(
        {"op": "assess", "vendor_id": "vendor-risky", "data_sensitivity": "phi"}
    )
    assert out["risk_tier"] == "high"


def test_assess_narrative_fallback_on_llm_error():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("sonnet down")

    out = _agent(bedrock=Boom()).handle({"op": "assess", "vendor_id": "vendor-risky"})
    assert out["status"] == "ok"
    assert "Overall risk: high" in out["narrative"]  # deterministic fallback


# --- set_status ------------------------------------------------------------
def test_set_status_persists_and_surfaces():
    s3 = FakeS3(dict(VENDOR_KEYS))
    out = _agent(s3=s3).handle({
        "op": "set_status", "vendor_id": "vendor-clean", "status": "conditional",
        "note": "approved for non-PHI use", "display_name": "Dana",
    })
    assert out["status"] == "ok" and out["approval_status"] == "conditional"
    lst = _agent(s3=s3).handle({"op": "list"})
    clean = next(v for v in lst["vendors"] if v["vendor_id"] == "vendor-clean")
    assert clean["approval_status"] == "conditional"


def test_set_status_rejects_bad_value():
    out = _agent().handle({"op": "set_status", "vendor_id": "vendor-clean", "status": "maybe"})
    assert out["status"] == "error"


def test_assess_then_set_status_coexist():
    s3 = FakeS3(dict(VENDOR_KEYS))
    _agent(s3=s3).handle({"op": "assess", "vendor_id": "vendor-clean"})
    _agent(s3=s3).handle({"op": "set_status", "vendor_id": "vendor-clean", "status": "approved"})
    got = _agent(s3=s3).handle({"op": "get", "vendor_id": "vendor-clean"})
    # Both the assessment and the approval persist in the same sidecar.
    assert got["vetting"]["risk_tier"] == "low"
    assert got["vetting"]["approval_status"] == "approved"
