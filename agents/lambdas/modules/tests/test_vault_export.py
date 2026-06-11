from agents.lambdas.modules.vault_export import export_frontmatter


def test_always_emits_content_type_and_generated():
    fm = export_frontmatter("ideation", {})
    assert fm.startswith("---\ncontent_type: ideation\ngenerated: true\n")
    assert fm.endswith("---\n")


def test_renders_scalars_lists_and_nested_dict():
    fm = export_frontmatter(
        "assessment",
        {
            "id": "assess-1",
            "stage": 3,
            "tags": ["a", "b"],
            "dimension_scores": {"data_readiness": 2, "governance": 4},
        },
    )
    assert "id: assess-1" in fm
    assert "stage: 3" in fm
    assert "tags: [a, b]" in fm
    assert "dimension_scores:\n  data_readiness: 2\n  governance: 4" in fm


def test_skips_none_fields():
    fm = export_frontmatter("ideation", {"id": "x", "missing": None})
    assert "missing" not in fm


def test_quotes_values_with_yaml_specials():
    fm = export_frontmatter("assessment", {"title": "Bank: Stage 2", "industry": "retail"})
    assert 'title: "Bank: Stage 2"' in fm
    assert "industry: retail" in fm  # plain value stays unquoted
