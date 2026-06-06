"""Tests for vault frontmatter schemas and the parse/validate helpers."""

from __future__ import annotations

import pytest

from agents.lib.schemas import (
    AssetFrontmatter,
    FrontmatterError,
    ToolFrontmatter,
    content_type_for_path,
    parse_frontmatter,
    validate_frontmatter,
)


def test_content_type_for_path_maps_folder():
    label, schema = content_type_for_path("assets/healthcare/2/x.md")
    assert label == "asset"
    assert schema is AssetFrontmatter


def test_content_type_for_path_untyped_returns_none():
    assert content_type_for_path("agents.md") is None
    assert content_type_for_path("modules.json") is None


def test_parse_frontmatter_extracts_mapping():
    text = "---\nid: a\ntitle: T\n---\n\nbody\n"
    assert parse_frontmatter(text) == {"id": "a", "title": "T"}


def test_parse_frontmatter_requires_block():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("no frontmatter here")


def test_validate_asset_ok():
    data = {
        "id": "ref-arch-x",
        "title": "X",
        "type": "reference-architecture",
        "industry": "healthcare",
        "ai_stage": 2,
        "use_case_type": ["rag"],
        "tags": ["x"],
        "updated_at": "2026-05-01",
    }
    model = validate_frontmatter(AssetFrontmatter, data)
    assert model.contributor == "demo"


def test_validate_tool_rejects_bad_category():
    data = {
        "id": "t",
        "name": "T",
        "category": "not-a-category",
        "stack": ["python"],
        "ai_stage_fit": [1, 2],
        "cost_model": "open-source",
        "limitations": [],
        "tags": [],
    }
    with pytest.raises(Exception):  # noqa: B017,PT011 — pydantic ValidationError
        validate_frontmatter(ToolFrontmatter, data)
