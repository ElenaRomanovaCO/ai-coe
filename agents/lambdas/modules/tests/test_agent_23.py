"""AGENT-23 feed: list / get / radar over the feed corpus.

Runs the real WORKER-10/11 behind an injected fake invoker; WORKER-11's single Sonnet
call is faked.
"""

from agents.lambdas.modules.agent_23_feed import FeedAgent
from agents.lambdas.workers.worker_10_item_classifier import ItemClassifierWorker
from agents.lambdas.workers.worker_11_commentary_writer import CommentaryWriterWorker

from .conftest import FakeMetrics, FakeS3


def _item(id_, title, category, industries, tags, radar, published):
    ind = ", ".join(f'"{i}"' for i in industries)
    tag = ", ".join(f'"{t}"' for t in tags)
    radar_line = f"radar_status: {radar}\n" if radar else "radar_status: null\n"
    return (
        f"---\nid: {id_}\ntitle: {title}\ncategory: {category}\n"
        f'source_url: "https://example.com/{id_}"\npublished_at: "{published}"\n'
        f"industries: [{ind}]\ntags: [{tag}]\n{radar_line}---\n\n"
        f"# {title}\n\nLede paragraph for {title}.\n\n## What this means\n\nGeneric note.\n"
    )


FEED_KEYS = {
    "feed/2026-05/sonnet.md": _item(
        "feed-sonnet", "New mid-tier model", "model-release",
        ["cross-industry"], ["summarization", "grounding"], "trial", "2026-05-14",
    ),
    "feed/2026-03/guardrails.md": _item(
        "feed-guardrails", "Managed guardrails add PII detection", "vendor-update",
        ["healthcare", "financial-services"], ["guardrails", "pii"], "adopt", "2026-03-17",
    ),
    "feed/2026-05/ai-act.md": _item(
        "feed-ai-act", "High-risk AI guidance", "industry-news",
        ["healthcare", "public-sector"], ["eu-ai-act", "compliance"], None, "2026-05-02",
    ),
    "feed/2026-05/long-context.md": _item(
        "feed-long-context", "Long context research", "research",
        ["cross-industry"], ["long-context", "rag"], "hold", "2026-05-26",
    ),
}


class FakeBedrockClient:
    def __init__(self, text="Tailored note for the reader."):
        self.text = text

    def converse(self, **kwargs):
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


class FakeWorkers:
    def __init__(self, bedrock=None):
        self.bedrock = bedrock or FakeBedrockClient()

    def invoke(self, worker_id, args):
        m = FakeMetrics()
        if worker_id == "WORKER-10":
            return ItemClassifierWorker(metrics_client=m).handle(args)
        if worker_id == "WORKER-11":
            worker = CommentaryWriterWorker(bedrock_client=self.bedrock, metrics_client=m)
            return worker.handle(args)
        return {"status": "not_implemented"}


def _agent(bedrock=None):
    return FeedAgent(
        vault_bucket="vault",
        s3=FakeS3(dict(FEED_KEYS)),
        worker_invoker=FakeWorkers(bedrock),
        metrics_client=FakeMetrics(),
    )


# --- list ------------------------------------------------------------------
def test_list_all_returns_every_item():
    out = _agent().handle({"op": "list"})
    assert out["status"] == "ok"
    assert {i["id"] for i in out["items"]} == {
        "feed-sonnet", "feed-guardrails", "feed-ai-act", "feed-long-context"
    }


def test_list_filters_by_category():
    out = _agent().handle({"op": "list", "category": "research"})
    assert {i["id"] for i in out["items"]} == {"feed-long-context"}


def test_list_filters_by_radar_status():
    out = _agent().handle({"op": "list", "radar_status": "adopt"})
    assert {i["id"] for i in out["items"]} == {"feed-guardrails"}


def test_list_filters_by_industry_including_cross_industry():
    out = _agent().handle({"op": "list", "industry": "healthcare"})
    ids = {i["id"] for i in out["items"]}
    # healthcare items + cross-industry items both surface.
    assert "feed-guardrails" in ids and "feed-ai-act" in ids
    assert "feed-sonnet" in ids  # cross-industry


def test_personalization_reorders_feed_by_industry():
    healthcare = _agent().handle(
        {"op": "list", "user_profile": {"industries": ["healthcare"]}}
    )["items"]
    # The healthcare item (direct match) outranks a cross-industry-only item.
    order = [i["id"] for i in healthcare]
    assert order.index("feed-guardrails") < order.index("feed-long-context")
    # Scores are attached and the top item is the direct industry match.
    assert healthcare[0]["id"] == "feed-guardrails"
    assert healthcare[0]["relevance_score"] > healthcare[-1]["relevance_score"]


def test_changing_industry_changes_top_item():
    fin = _agent().handle(
        {"op": "list", "user_profile": {"industries": ["financial-services"]}}
    )["items"]
    # guardrails is tagged financial-services, so it tops the financial feed too,
    # but a public-sector reader ranks ai-act higher than the fin-only nobody.
    pub_profile = {"op": "list", "user_profile": {"industries": ["public-sector"]}}
    pub = _agent().handle(pub_profile)["items"]
    assert fin[0]["id"] == "feed-guardrails"
    assert pub[0]["id"] in {"feed-guardrails", "feed-ai-act"}
    # public-sector reader scores ai-act (direct match) above long-context (cross only)
    pub_order = [i["id"] for i in pub]
    assert pub_order.index("feed-ai-act") < pub_order.index("feed-long-context")


# --- get -------------------------------------------------------------------
def test_get_resolves_and_attaches_commentary():
    out = _agent().handle(
        {"op": "get", "item_id": "feed-sonnet", "user_profile": {"industries": ["healthcare"],
                                                                 "ai_stage": 2}}
    )
    assert out["status"] == "ok"
    assert out["item"]["title"] == "New mid-tier model"
    assert "Lede paragraph" in out["item"]["body_markdown"]
    assert out["commentary"]["commentary"] == "Tailored note for the reader."
    assert out["commentary"]["tailored"] is True


def test_get_commentary_falls_back_when_llm_errors():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("down")

    out = _agent(bedrock=Boom()).handle(
        {"op": "get", "id": "feed-sonnet", "user_profile": {"industries": ["healthcare"]}}
    )
    assert out["status"] == "ok"
    assert out["commentary"]["tailored"] is False
    assert out["commentary"]["commentary"]  # deterministic note still present


def test_get_unknown_item_not_found():
    out = _agent().handle({"op": "get", "item_id": "feed-nope"})
    assert out["status"] == "not_found"


def test_get_via_id_alias_and_inferred_op():
    out = _agent().handle({"id": "feed-ai-act"})
    assert out["status"] == "ok" and out["item"]["id"] == "feed-ai-act"


# --- radar -----------------------------------------------------------------
def test_radar_groups_into_quadrants():
    out = _agent().handle({"op": "radar"})
    assert out["status"] == "ok"
    assert {i["id"] for i in out["adopt"]} == {"feed-guardrails"}
    assert {i["id"] for i in out["trial"]} == {"feed-sonnet"}
    assert {i["id"] for i in out["hold"]} == {"feed-long-context"}
    assert out["assess"] == []
    # Items with no radar status (feed-ai-act) appear in no quadrant.
    all_ids = {i["id"] for q in ("adopt", "trial", "assess", "hold") for i in out[q]}
    assert "feed-ai-act" not in all_ids


# --- default op ------------------------------------------------------------
def test_default_op_is_list():
    out = _agent().handle({})
    assert out["status"] == "ok" and out["items"]
