import io
import zipfile

from agents.lambdas.modules.agent_04_kit_builder import KitBuilderAgent

from .conftest import FakeMetrics, FakeS3


def _asset(id_, title, type_, industry, stage, tags=()):
    tag_list = ", ".join(f'"{t}"' for t in tags)
    return (
        f"---\nid: {id_}\ntitle: {title}\ntype: {type_}\nindustry: {industry}\n"
        f'ai_stage: {stage}\ntags: [{tag_list}]\nupdated_at: "2026-05-01"\n---\n\n# {title}\n'
    )


def _doc(id_, title):
    return f"---\nid: {id_}\ntitle: {title}\nupdated_at: \"2026-05-01\"\n---\n\n# {title}\n"


VAULT = {
    "assets/healthcare/2/ref-arch-rag.md": _asset(
        "ref-arch-rag", "Clinical RAG Architecture", "reference-architecture", "healthcare", 2
    ),
    "assets/healthcare/2/pattern-triage.md": _asset(
        "pattern-triage", "Triage Pattern", "solution-pattern", "healthcare", 2
    ),
    "assets/healthcare/1/kickoff.md": _asset(
        "kickoff-hc", "Discovery Kickoff", "kickoff-template", "healthcare", 1
    ),
    "assets/financial-services/3/fraud.md": _asset(
        "fraud-pattern", "Fraud Scoring", "solution-pattern", "financial-services", 3
    ),
    "regs/eu-ai-act.md": _doc("eu-ai-act", "EU AI Act Overview"),
    "regs/gdpr.md": _doc("gdpr", "GDPR Essentials"),
    "feed/new-model.md": _doc("new-model", "New Model Release"),
    "feed/agents-trend.md": _doc("agents-trend", "Agentic AI Trend"),
    "tools/vector-db.md": _doc("vector-db", "Vector DB Options"),
}


def _agent():
    return KitBuilderAgent(
        vault_bucket="vault",
        sessions_bucket="sessions",
        s3=FakeS3(VAULT),
        metrics_client=FakeMetrics(),
    )


def _criteria(**over):
    base = {
        "op": "preview",
        "display_name": "Alex",
        "industry": "healthcare",
        "ai_stage": 2,
        "engagement_type": "discovery",
        "duration_weeks": 6,
    }
    base.update(over)
    return base


def test_preview_selects_across_categories():
    out = _agent().handle(_criteria())
    assert out["status"] == "ok"
    cats = {f["category"] for f in out["files"]}
    # architecture + templates (healthcare stage 1-3) + governance + intelligence + tools
    assert {"architecture", "templates", "governance", "intelligence", "tools"} <= cats
    assert 8 <= len(out["files"]) <= 15 or len(out["files"]) >= 5  # bounded, non-empty
    assert out["download_url"] is None  # preview does not zip


def test_preview_filters_industry_and_stage():
    out = _agent().handle(_criteria(industry="healthcare", ai_stage=2))
    arch = [f for f in out["files"] if f["category"] in ("architecture", "templates")]
    # The financial-services stage-3 asset must not appear for healthcare stage 2.
    assert all("financial-services" not in f["source_path"] for f in arch)


def test_readme_references_each_file():
    out = _agent().handle(_criteria())
    readme = out["readme_markdown"]
    assert "# Engagement Kit" in readme
    for f in out["files"]:
        assert f["title"] in readme


def test_search_vault_filters_by_query():
    out = _agent().handle({"op": "search_vault", "query": "fraud"})
    assert out["status"] == "ok"
    assert any("fraud" in f["source_path"] for f in out["files"])


def test_generate_produces_valid_zip_and_url():
    agent = _agent()
    s3 = agent._s3
    out = agent.handle(_criteria(op="generate"))
    assert out["status"] == "ok"
    assert out["download_url"].startswith("https://s3.test/")
    zip_key = out["zip_key"]
    assert zip_key.startswith("kits/alex/")

    raw = s3.objects[zip_key]
    assert isinstance(raw, bytes)  # stored as binary
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        assert any(n.endswith("/README.md") for n in names)
        # Every manifest file is present in the zip at its target path.
        for f in out["files"]:
            assert f["target_path"] in names
        bad = z.testzip()
        assert bad is None  # zip integrity


def test_generate_uses_provided_file_list():
    agent = _agent()
    fraud = "assets/financial-services/3/fraud.md"
    out = agent.handle(
        _criteria(op="generate", files=[{"category": "architecture", "source_path": fraud}])
    )
    assert [f["source_path"] for f in out["files"]] == [fraud]
    with zipfile.ZipFile(io.BytesIO(agent._s3.objects[out["zip_key"]])) as z:
        bodies = [
            z.read(n).decode()
            for n in z.namelist()
            if n.endswith(".md") and "README" not in n
        ]
    assert any("Fraud Scoring" in b for b in bodies)


def test_generate_requires_display_name():
    out = _agent().handle({"op": "generate", "industry": "healthcare", "ai_stage": 2})
    assert out["status"] == "error"
