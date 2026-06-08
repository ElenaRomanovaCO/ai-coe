from .conftest import make_agent, vec


# --- list_assets -----------------------------------------------------------
def test_list_assets_returns_all():
    out = make_agent().handle({"op": "list_assets"})
    assert out["status"] == "ok"
    ids = {a["id"] for a in out["assets"]}
    assert ids == {
        "reference-arch-clinical-notes-rag",
        "solution-pattern-fraud-scoring-agent",
    }
    # Summary shape is fully populated from frontmatter.
    a = next(a for a in out["assets"] if a["industry"] == "healthcare")
    assert a["ai_stage"] == 2
    assert a["type"] == "reference-architecture"
    assert "rag" in a["tags"]
    assert a["file_path"].endswith("reference-arch-clinical-notes-rag.md")


def test_list_assets_filters_by_industry():
    out = make_agent().handle({"op": "list_assets", "industry": "healthcare"})
    assert [a["industry"] for a in out["assets"]] == ["healthcare"]


def test_list_assets_filters_by_stage_and_type():
    out = make_agent().handle({"ai_stage": 3, "asset_type": "solution-pattern"})
    assert len(out["assets"]) == 1
    assert out["assets"][0]["id"] == "solution-pattern-fraud-scoring-agent"


def test_list_assets_filters_by_tags_subset():
    out = make_agent().handle({"op": "list_assets", "tags": ["fraud"]})
    assert [a["id"] for a in out["assets"]] == ["solution-pattern-fraud-scoring-agent"]


def test_list_assets_query_substring():
    out = make_agent().handle({"op": "list_assets", "query": "clinical"})
    assert [a["id"] for a in out["assets"]] == ["reference-arch-clinical-notes-rag"]


# --- get_asset -------------------------------------------------------------
def test_get_asset_by_id():
    out = make_agent().handle(
        {"op": "get_asset", "asset_id": "solution-pattern-fraud-scoring-agent"}
    )
    assert out["status"] == "ok"
    assert out["asset"]["summary"]["industry"] == "financial-services"
    assert out["asset"]["body_markdown"].startswith("# Fraud Scoring Agent")
    assert out["asset"]["frontmatter"]["ai_stage"] == 3


def test_get_asset_infers_op_from_asset_id():
    # No explicit op: presence of asset_id routes to get_asset.
    out = make_agent().handle({"asset_id": "reference-arch-clinical-notes-rag"})
    assert out["status"] == "ok"
    assert out["asset"]["summary"]["title"].startswith("Reference Architecture")


def test_get_asset_not_found():
    out = make_agent().handle({"op": "get_asset", "asset_id": "does-not-exist"})
    assert out["status"] == "not_found"


def test_get_asset_requires_id():
    out = make_agent().handle({"op": "get_asset"})
    assert out["status"] == "error"


# --- search ----------------------------------------------------------------
def test_search_filters_to_assets_and_dedups():
    vectors = [
        vec("assets/healthcare/2/reference-arch-clinical-notes-rag.md"),
        vec("assets/healthcare/2/reference-arch-clinical-notes-rag.md"),  # dup chunk
        vec("tools/some-tool.md", content_type="tools"),  # non-asset, excluded
        vec("assets/financial-services/3/solution-pattern-fraud-scoring-agent.md"),
    ]
    out = make_agent(vectors=vectors).handle({"op": "search", "query": "clinical notes"})
    assert out["status"] == "ok"
    ids = [a["id"] for a in out["assets"]]
    assert ids == [
        "reference-arch-clinical-notes-rag",
        "solution-pattern-fraud-scoring-agent",
    ]


def test_search_infers_op_from_query():
    vectors = [vec("assets/healthcare/2/reference-arch-clinical-notes-rag.md")]
    out = make_agent(vectors=vectors).handle({"query": "rag"})
    assert out["status"] == "ok"
    assert out["assets"][0]["id"] == "reference-arch-clinical-notes-rag"


def test_search_requires_query():
    out = make_agent().handle({"op": "search"})
    assert out["status"] == "error"
