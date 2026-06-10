"""AGENT-13 vendor eval: list / get / flag_stale / build_comparison."""

from agents.lambdas.modules.agent_13_vendor_eval import VendorEvalAgent

from .conftest import FakeMetrics, FakeS3


def _eval(id_, category, vendors, criteria, last_verified, title):
    v = ", ".join(f'"{x}"' for x in vendors)
    c = ", ".join(f'"{x}"' for x in criteria)
    return (
        f"---\nid: {id_}\ncategory: {category}\nvendors_compared: [{v}]\n"
        f'criteria: [{c}]\nlast_verified: "{last_verified}"\n---\n\n'
        f"# {title}\n\nIntro.\n\n## Criteria\n\nText.\n\n"
        f"## Recommendation\n\nDefault to the incumbent. Re-verify quarterly.\n"
    )


# Two llm-provider evals (so a same-category comparison has overlapping criteria),
# one cloud eval, and one deliberately stale entry.
EVAL_KEYS = {
    "vendors/llm-document-analysis.md": _eval(
        "vendor-eval-llm-document-analysis", "llm-provider",
        ["Claude Sonnet", "GPT-4o", "Gemini"],
        ["accuracy", "long-context", "cost", "latency", "safety-controls"],
        "2026-05-22", "LLM Provider Comparison — Document Analysis",
    ),
    "vendors/embedding-model-comparison.md": _eval(
        "vendor-eval-embedding-models", "llm-provider",
        ["Titan Embed v2", "OpenAI text-embedding-3", "Cohere Embed"],
        ["retrieval-quality", "dimensions", "cost", "multilingual", "aws-fit"],
        "2026-05-20", "Embedding Model Comparison",
    ),
    "vendors/cloud-ai-platform-comparison.md": _eval(
        "vendor-eval-cloud-ai-platform", "cloud-ai-platform",
        ["AWS Bedrock", "Azure AI Foundry", "Google Vertex AI"],
        ["model-choice", "governance", "cost", "guardrails"],
        "2026-05-23", "Cloud AI Platform Comparison",
    ),
    "vendors/old-eval.md": _eval(
        "vendor-eval-old", "vector-db", ["Pinecone", "pgvector"],
        ["cost", "scale"], "2025-01-01", "Stale Vector DB Comparison",
    ),
}


_INSIGHTS_MD = "- Sonnet leads on faithfulness.\n- GPT-4o is fastest.\n- Verify on your corpus."


class FakeBedrockClient:
    def __init__(self, text=_INSIGHTS_MD):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


def _agent(bedrock=None):
    return VendorEvalAgent(
        vault_bucket="vault",
        s3=FakeS3(dict(EVAL_KEYS)),
        bedrock_client=bedrock or FakeBedrockClient(),
        metrics_client=FakeMetrics(),
    )


# --- list ------------------------------------------------------------------
def test_list_all_sorted_newest_first():
    out = _agent().handle({"op": "list_evaluations"})
    assert out["status"] == "ok"
    dates = [e["last_verified"] for e in out["evaluations"]]
    assert dates == sorted(dates, reverse=True)
    assert out["evaluations"][0]["id"] == "vendor-eval-cloud-ai-platform"  # 2026-05-23


def test_list_derives_title_from_h1():
    out = _agent().handle({"op": "list_evaluations"})
    cloud = next(e for e in out["evaluations"] if e["id"] == "vendor-eval-cloud-ai-platform")
    assert cloud["title"] == "Cloud AI Platform Comparison"


def test_list_filters_by_category():
    out = _agent().handle({"op": "list_evaluations", "category": "llm-provider"})
    assert {e["id"] for e in out["evaluations"]} == {
        "vendor-eval-llm-document-analysis", "vendor-eval-embedding-models"
    }


def test_list_flags_stale_entry():
    out = _agent().handle({"op": "list_evaluations"})
    old = next(e for e in out["evaluations"] if e["id"] == "vendor-eval-old")
    fresh = next(e for e in out["evaluations"] if e["id"] == "vendor-eval-cloud-ai-platform")
    assert old["stale"] is True
    assert fresh["stale"] is False


# --- get -------------------------------------------------------------------
def test_get_evaluation():
    out = _agent().handle({"op": "get_evaluation", "evaluation_id": "vendor-eval-embedding-models"})
    assert out["status"] == "ok"
    assert out["evaluation"]["title"] == "Embedding Model Comparison"
    assert "Recommendation" in out["evaluation"]["body_markdown"]
    assert out["evaluation"]["stale"] is False


def test_get_unknown_not_found():
    out = _agent().handle({"op": "get_evaluation", "evaluation_id": "nope"})
    assert out["status"] == "not_found"


# --- flag_stale ------------------------------------------------------------
def test_flag_stale_single():
    out = _agent().handle({"op": "flag_stale", "evaluation_id": "vendor-eval-old"})
    assert out["status"] == "ok" and out["stale"] is True and out["age_days"] > 90


def test_flag_stale_all():
    out = _agent().handle({"op": "flag_stale"})
    assert out["status"] == "ok"
    assert [s["id"] for s in out["stale"]] == ["vendor-eval-old"]


# --- build_comparison ------------------------------------------------------
def test_build_comparison_table_and_insights():
    fake = FakeBedrockClient()
    out = _agent(bedrock=fake).handle(
        {
            "op": "build_comparison",
            "evaluation_ids": ["vendor-eval-llm-document-analysis", "vendor-eval-embedding-models"],
        }
    )
    assert out["status"] == "ok"
    assert out["comparison_id"].startswith("cmp-")
    md = out["comparison_markdown"]
    # Columns are the two evaluation titles; criteria union appears as rows.
    assert "LLM Provider Comparison — Document Analysis" in md
    assert "Embedding Model Comparison" in md
    assert "| accuracy |" in md and "| retrieval-quality |" in md
    assert "| cost |" in md  # shared criterion
    assert "GPT-4o" in md  # vendors_compared rendered
    # Insights parsed from the (faked) Sonnet bullet list.
    assert len(out["insights"]) == 3
    assert fake.calls == 1


def test_build_comparison_criteria_subset():
    out = _agent().handle(
        {
            "op": "build_comparison",
            "evaluation_ids": [
                "vendor-eval-llm-document-analysis", "vendor-eval-cloud-ai-platform",
            ],
            "criteria": ["cost"],
        }
    )
    md = out["comparison_markdown"]
    assert "| cost |" in md
    assert "| accuracy |" not in md  # not in the requested subset


def test_build_comparison_rejects_too_few():
    out = _agent().handle(
        {"op": "build_comparison", "evaluation_ids": ["vendor-eval-old"]}
    )
    assert out["status"] == "error"


def test_build_comparison_rejects_too_many():
    out = _agent().handle({"op": "build_comparison", "evaluation_ids": list(
        ["vendor-eval-llm-document-analysis", "vendor-eval-embedding-models",
         "vendor-eval-cloud-ai-platform", "vendor-eval-old", "vendor-eval-extra"]
    )})
    assert out["status"] == "error"


def test_build_comparison_insights_fallback_on_llm_error():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("bedrock down")

    out = _agent(bedrock=Boom()).handle(
        {
            "op": "build_comparison",
            "evaluation_ids": ["vendor-eval-llm-document-analysis", "vendor-eval-old"],
        }
    )
    assert out["status"] == "ok"
    assert out["insights"]  # deterministic fallback
    # The stale entry is called out by the fallback.
    assert any("re-verify" in i.lower() for i in out["insights"])
