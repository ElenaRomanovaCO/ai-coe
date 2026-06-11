from agents.lambdas.workers.worker_10_item_classifier import ItemClassifierWorker

from .conftest import FakeMetrics

ITEM = {
    "frontmatter": {
        "id": "feed-x",
        "category": "model-release",
        "industries": ["healthcare", "cross-industry"],
        "tags": ["summarization", "grounding"],
        "radar_status": "trial",
    },
    "body": "# X\n\nBody.\n",
}


def classify(args):
    return ItemClassifierWorker(metrics_client=FakeMetrics()).handle(args)


def test_echoes_classification():
    out = classify({"item": ITEM, "user_profile": {}})
    assert out["status"] == "ok"
    assert out["category"] == "model-release"
    assert out["industries"] == ["healthcare", "cross-industry"]


def test_direct_industry_match_scores_higher_than_no_match():
    matched = classify({"item": ITEM, "user_profile": {"industries": ["healthcare"]}})
    unmatched = classify({"item": ITEM, "user_profile": {"industries": ["energy"]}})
    assert matched["relevance_score"] > unmatched["relevance_score"]
    assert matched["matched"]["industries"] == ["healthcare"]


def test_cross_industry_item_relevant_without_direct_match():
    # The item is also tagged cross-industry, so an energy-focused user still gets a bump.
    out = classify({"item": ITEM, "user_profile": {"industries": ["energy"]}})
    # base 0.30 + cross-industry 0.15 + trial 0.07 = 0.52
    assert out["relevance_score"] > 0.30
    assert out["matched"]["industries"] == []


def test_tech_focus_tags_add_relevance():
    base = classify({"item": ITEM, "user_profile": {"industries": ["healthcare"]}})
    with_tags = classify(
        {"item": ITEM, "user_profile": {"industries": ["healthcare"], "tech_focus": ["grounding"]}}
    )
    assert with_tags["relevance_score"] > base["relevance_score"]
    assert with_tags["matched"]["tags"] == ["grounding"]


def test_radar_weight_orders_adopt_above_hold():
    adopt = classify({"frontmatter": {**ITEM["frontmatter"], "radar_status": "adopt"}})
    hold = classify({"frontmatter": {**ITEM["frontmatter"], "radar_status": "hold"}})
    assert adopt["relevance_score"] > hold["relevance_score"]


def test_score_is_clamped_to_unit_interval():
    out = classify(
        {
            "item": ITEM,
            "user_profile": {
                "industries": ["healthcare"],
                "tech_focus": ["summarization", "grounding", "a", "b", "c"],
            },
        }
    )
    assert 0.0 <= out["relevance_score"] <= 1.0


def test_empty_profile_is_neutral_baseline():
    out = classify({"frontmatter": {"category": "research", "industries": [], "tags": []}})
    assert out["status"] == "ok"
    # base 0.30 + no-radar 0.05 = 0.35
    assert out["relevance_score"] == 0.35
