"""AGENT-12 ideation: generate (faked Sonnet) + deterministic rank + persist/get.

The candidate generation LLM call is faked; scoring, reference linking, export, and
persistence are exercised for real against in-memory S3.
"""

import json

from agents.lambdas.modules.agent_12_ideation import IdeationAgent

from .conftest import FakeMetrics, FakeS3

# A model response: deliberately unordered so the deterministic ranker has to sort it.
CANDIDATES_JSON = json.dumps(
    [
        {
            "title": "Low-value busywork bot",
            "description": "Automates a niche internal report.",
            "effort": "high",
            "impact": "low",
            "prerequisites": ["nothing special"],
            "rationale": "Marginal.",
        },
        {
            "title": "Customer churn predictor",
            "description": "Scores customers by churn risk from transaction history.",
            "effort": "low",
            "impact": "high",
            "prerequisites": ["customer transactions"],
            "rationale": "Directly targets the churn goal using available data.",
        },
        {
            "title": "Demand forecasting",
            "description": "Forecasts demand to optimize inventory.",
            "effort": "medium",
            "impact": "medium",
            "prerequisites": ["sales history"],
            "rationale": "Solid operational win.",
        },
    ]
)


class FakeBedrockClient:
    def __init__(self, text=CANDIDATES_JSON):
        self.text = text
        self.calls = 0
        self.last_user = None

    def converse(self, **kwargs):
        self.calls += 1
        self.last_user = kwargs["messages"][0]["content"][0]["text"]
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


class FakeAssetAgent:
    """Stands in for AGENT-03 search; returns a fixed reference asset."""

    def __init__(self, asset=None):
        self.asset = asset or {"id": "reference-arch-churn", "title": "Churn RAG Pattern"}
        self.queries = []

    def handle(self, args):
        self.queries.append(args.get("query", ""))
        return {"status": "ok", "assets": [self.asset]}


def _agent(bedrock=None, asset_agent=None, s3=None):
    return IdeationAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=s3 if s3 is not None else FakeS3({}),
        bedrock_client=bedrock or FakeBedrockClient(),
        asset_agent=asset_agent or FakeAssetAgent(),
        metrics_client=FakeMetrics(),
    )


REQ = {
    "op": "generate",
    "display_name": "Dana",
    "industry": "retail",
    "pain_points": ["customer churn"],
    "goals": ["reduce churn"],
    "available_data": ["customer transactions"],
    "ai_stage": 2,
}


# --- generate --------------------------------------------------------------
def test_generate_returns_ranked_candidates():
    out = _agent().handle(dict(REQ))
    assert out["status"] == "ok"
    titles = [c["title"] for c in out["candidates"]]
    # High-impact/low-effort churn predictor ranks first; low-impact/high-effort last.
    assert titles[0] == "Customer churn predictor"
    assert titles[-1] == "Low-value busywork bot"
    # rank_score is monotonically non-increasing.
    scores = [c["rank_score"] for c in out["candidates"]]
    assert scores == sorted(scores, reverse=True)


def test_generate_assigns_ids_and_coerces_levels():
    out = _agent().handle(dict(REQ))
    assert all(c["id"] for c in out["candidates"])
    assert all(c["effort"] in ("low", "medium", "high") for c in out["candidates"])
    assert all(c["impact"] in ("low", "medium", "high") for c in out["candidates"])


def test_data_prior_boosts_candidate_matching_available_data():
    # "customer transactions" is available -> churn predictor (which needs it) gets +1.
    out = _agent().handle(dict(REQ))
    churn = next(c for c in out["candidates"] if c["title"] == "Customer churn predictor")
    # base = 2*impact(3) - effort(1) = 5, + data prior 1 = 6
    assert churn["rank_score"] == 6.0


def test_reference_assets_attached():
    aa = FakeAssetAgent()
    out = _agent(asset_agent=aa).handle(dict(REQ))
    top = out["candidates"][0]
    assert top["reference_example_asset_id"] == "reference-arch-churn"
    assert top["reference_example_url"] == "/modules/asset-library/reference-arch-churn"
    assert len(aa.queries) == len(out["candidates"])  # one search per candidate


def test_context_is_woven_into_prompt():
    fake = FakeBedrockClient()
    _agent(bedrock=fake).handle(dict(REQ))
    assert "retail" in fake.last_user
    assert "customer churn" in fake.last_user
    assert "customer transactions" in fake.last_user


def test_export_markdown_has_context_and_candidates():
    out = _agent().handle(dict(REQ))
    md = out["markdown"]
    # Tagged as a generated vault artifact (scoped out of curated chat KB search).
    assert md.startswith("---\ncontent_type: ideation\ngenerated: true\n")
    assert "# AI Use Case Ideation" in md
    assert "Customer churn predictor" in md
    assert "Available data" in md
    assert out["vault_file_path"].startswith("ideation/dana/")
    assert out["vault_file_path"].endswith(".md")


def test_vault_markdown_is_written():
    s3 = FakeS3({})
    _agent(s3=s3).handle(dict(REQ))
    md_keys = [k for k in s3.objects if k.startswith("ideation/dana/") and k.endswith(".md")]
    assert len(md_keys) == 1


# --- persist + get ---------------------------------------------------------
def test_generate_then_get_round_trip():
    s3 = FakeS3({})
    agent = _agent(s3=s3)
    gen = agent.handle(dict(REQ))
    iid = gen["ideation_id"]
    got = _agent(s3=s3).handle({"op": "get", "ideation_id": iid})
    assert got["status"] == "ok"
    assert got["ideation_id"] == iid
    assert [c["title"] for c in got["candidates"]] == [c["title"] for c in gen["candidates"]]
    assert got["vault_file_path"] == gen["vault_file_path"]
    assert got["markdown"] == gen["markdown"]


def test_get_via_id_alias_and_inferred_op():
    s3 = FakeS3({})
    gen = _agent(s3=s3).handle(dict(REQ))
    got = _agent(s3=s3).handle({"id": gen["ideation_id"]})
    assert got["status"] == "ok" and got["ideation_id"] == gen["ideation_id"]


def test_get_unknown_not_found():
    out = _agent().handle({"op": "get", "ideation_id": "idea-nope"})
    assert out["status"] == "not_found"


# --- guards / errors -------------------------------------------------------
def test_generate_requires_display_name():
    out = _agent().handle({"op": "generate", "industry": "retail"})
    assert out["status"] == "error" and "display_name" in out["message"]


def test_generate_requires_industry():
    out = _agent().handle({"op": "generate", "display_name": "Dana", "industry": ""})
    assert out["status"] == "error" and "industry" in out["message"]


def test_unparseable_model_output_is_error():
    out = _agent(bedrock=FakeBedrockClient(text="sorry, I can't help with that")).handle(dict(REQ))
    assert out["status"] == "error"


def test_model_output_with_code_fence_is_parsed():
    fenced = f"```json\n{CANDIDATES_JSON}\n```"
    out = _agent(bedrock=FakeBedrockClient(text=fenced)).handle(dict(REQ))
    assert out["status"] == "ok" and len(out["candidates"]) == 3


def test_candidates_wrapped_in_object_are_parsed():
    wrapped = json.dumps({"candidates": json.loads(CANDIDATES_JSON)})
    out = _agent(bedrock=FakeBedrockClient(text=wrapped)).handle(dict(REQ))
    assert out["status"] == "ok" and len(out["candidates"]) == 3
