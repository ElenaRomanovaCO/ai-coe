"""AGENT-24 compliance: list / get / apply over the reg corpus.

Runs the real WORKER-12/13 behind an injected fake invoker; the single Sonnet
narrative call (apply path only) is faked.
"""

from agents.lambdas.modules.agent_24_compliance import ComplianceAgent
from agents.lambdas.workers.worker_12_reg_summarizer import RegSummarizerWorker
from agents.lambdas.workers.worker_13_applicability_checker import ApplicabilityCheckerWorker

from .conftest import FakeMetrics, FakeS3


def _reg(id_, name, geo, scope, status, tags, clauses):
    scope_list = ", ".join(f'"{s}"' for s in scope)
    tag_list = ", ".join(f'"{t}"' for t in tags)
    body = "\n\n".join(f"## {h}\n\n{t}" for h, t in clauses)
    return (
        f"---\nid: {id_}\nname: {name}\ngeo: {geo}\n"
        f"industry_scope: [{scope_list}]\nstatus: {status}\n"
        f'effective_date: "2024-08-01"\nrisk_tier: null\ntags: [{tag_list}]\n---\n\n'
        f"# {name}\n\nIntro paragraph describing {name}.\n\n{body}\n"
    )


REG_KEYS = {
    "regs/eu/ai-act/eu-ai-act.md": _reg(
        "reg-eu-ai-act", "EU Artificial Intelligence Act", "eu",
        ["cross-industry", "healthcare", "financial-services"], "in-effect",
        ["eu", "ai-act", "high-risk", "transparency"],
        [
            ("Risk tiers", "Systems are sorted into risk tiers."),
            ("High-risk obligations",
             "Medical devices and clinical diagnostic systems are high-risk."),
            ("Limited-risk transparency",
             "Chatbots and conversational assistants must disclose AI use."),
            ("What this means for engagements", "Classify each use case by tier early."),
        ],
    ),
    "regs/us-federal/hipaa/hipaa-ai.md": _reg(
        "reg-hipaa-ai", "HIPAA — AI and PHI", "us-federal",
        ["healthcare"], "in-effect", ["hipaa", "phi", "baa"],
        [
            ("Key implications for AI",
             "- **Business Associate Agreements (BAAs)** — vendors processing PHI need a BAA."),
            ("What this means for engagements", "De-identify PHI before embedding."),
        ],
    ),
    "regs/us-federal/ffiec/ffiec-ai-financial.md": _reg(
        "reg-ffiec-ai", "FFIEC — AI in Financial Institutions", "us-federal",
        ["financial-services"], "guidance", ["ffiec", "model-risk", "banking"],
        [("Model risk management", "Validate and monitor financial models.")],
    ),
}


class FakeBedrockClient:
    def __init__(self, text="EU AI Act applies; classify the system's risk tier first."):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


class FakeWorkers:
    def invoke(self, worker_id, args):
        m = FakeMetrics()
        if worker_id == "WORKER-12":
            return RegSummarizerWorker(metrics_client=m).handle(args)
        if worker_id == "WORKER-13":
            return ApplicabilityCheckerWorker(metrics_client=m).handle(args)
        return {"status": "not_implemented"}


def _agent(bedrock=None):
    return ComplianceAgent(
        vault_bucket="vault",
        s3=FakeS3(dict(REG_KEYS)),
        bedrock_client=bedrock or FakeBedrockClient(),
        worker_invoker=FakeWorkers(),
        metrics_client=FakeMetrics(),
    )


# --- list ------------------------------------------------------------------
def test_list_all_returns_every_reg():
    out = _agent().handle({"op": "list"})
    assert out["status"] == "ok"
    assert {r["id"] for r in out["regulations"]} == {
        "reg-eu-ai-act", "reg-hipaa-ai", "reg-ffiec-ai"
    }


def test_list_filters_by_geography_and_industry():
    out = _agent().handle({"op": "list", "geography": "EU", "industry": "healthcare"})
    ids = {r["id"] for r in out["regulations"]}
    assert ids == {"reg-eu-ai-act"}  # EU geo + healthcare (or cross-industry) scope


def test_list_filters_by_status():
    out = _agent().handle({"op": "list", "status": "guidance"})
    assert {r["id"] for r in out["regulations"]} == {"reg-ffiec-ai"}


def test_list_filters_by_use_case_type():
    out = _agent().handle({"op": "list", "use_case_type": "transparency"})
    assert "reg-eu-ai-act" in {r["id"] for r in out["regulations"]}


def test_list_default_op_is_list():
    out = _agent().handle({})
    assert out["status"] == "ok" and out["regulations"]


# --- get -------------------------------------------------------------------
def test_get_resolves_by_frontmatter_id_and_summarizes():
    out = _agent().handle({"op": "get", "reg_id": "reg-hipaa-ai"})
    assert out["status"] == "ok"
    assert out["regulation"]["name"].startswith("HIPAA")
    assert "Business Associate Agreements" in out["regulation"]["body_markdown"]
    # WORKER-12 summary is attached.
    assert out["summary"]["summary"].startswith("Intro paragraph")
    labels = [r.split(" — ")[0] for r in out["summary"]["key_requirements"]]
    assert "Business Associate Agreements (BAAs)" in labels


def test_get_unknown_reg_not_found():
    out = _agent().handle({"op": "get", "reg_id": "reg-nope"})
    assert out["status"] == "not_found"


def test_get_via_id_alias_and_inferred_op():
    out = _agent().handle({"id": "reg-eu-ai-act"})  # op inferred from reg_id alias
    assert out["status"] == "ok" and out["regulation"]["id"] == "reg-eu-ai-act"


# --- apply -----------------------------------------------------------------
def test_apply_returns_applicability_and_narrative():
    fake = FakeBedrockClient()
    out = _agent(bedrock=fake).handle(
        {
            "op": "apply",
            "reg_id": "reg-eu-ai-act",
            "use_case_description": "clinical imaging classifier",
            "industry": "healthcare",
            "geography": "EU",
        }
    )
    assert out["status"] == "ok"
    assert out["regulation_applies"] is True
    clauses = {a["clause"]: a["applies"] for a in out["applicability"]}
    assert clauses["High-risk obligations"] is True  # clinical → health domain
    assert clauses["Limited-risk transparency"] is False  # not a chatbot
    assert out["narrative"] == fake.text
    assert fake.calls == 1


def test_apply_falls_back_when_llm_errors():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("bedrock down")

    out = _agent(bedrock=Boom()).handle(
        {
            "op": "apply",
            "reg_id": "reg-eu-ai-act",
            "use_case_description": "clinical imaging classifier",
            "industry": "healthcare",
            "geography": "EU",
        }
    )
    assert out["status"] == "ok"
    assert "Focus first on" in out["narrative"]  # deterministic fallback


def test_apply_requires_use_case():
    out = _agent().handle({"op": "apply", "reg_id": "reg-eu-ai-act"})
    assert out["status"] == "error"
