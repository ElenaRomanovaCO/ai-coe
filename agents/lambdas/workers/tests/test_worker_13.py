from agents.lambdas.workers.worker_13_applicability_checker import ApplicabilityCheckerWorker

from .conftest import FakeMetrics

EU_AI_ACT = {
    "id": "reg-eu-ai-act",
    "name": "EU Artificial Intelligence Act",
    "frontmatter": {
        "geo": "eu",
        "industry_scope": ["cross-industry", "healthcare", "financial-services"],
    },
    "body": """# EU Artificial Intelligence Act

The EU's horizontal AI regulation, structured around risk tiers.

## Risk tiers

The Act sorts systems into unacceptable, high, limited, and minimal risk.

## High-risk obligations

Medical devices and clinical diagnostic systems are high-risk and carry the heaviest
duties: documentation, human oversight, and conformity assessment.

## Limited-risk transparency

Chatbots and other conversational assistants must disclose that the user is
interacting with AI.

## What this means for engagements

Classify each use case by tier early.
""",
}


def check(use_case, industry="healthcare", geography="EU", reg=EU_AI_ACT):
    return ApplicabilityCheckerWorker(metrics_client=FakeMetrics()).handle(
        {
            "regulation": reg,
            "use_case_description": use_case,
            "industry": industry,
            "geography": geography,
        }
    )


def test_regulation_applies_on_geo_and_industry():
    out = check("clinical imaging classifier")
    assert out["status"] == "ok"
    assert out["regulation_applies"] is True
    assert "applies" in out["overall"].lower()


def test_clauses_returned_for_every_heading():
    out = check("clinical imaging classifier")
    clauses = {a["clause"] for a in out["applicability"]}
    assert {"Risk tiers", "High-risk obligations", "Limited-risk transparency"} <= clauses


def test_generic_clauses_always_apply():
    out = check("clinical imaging classifier")
    risk_tiers = next(a for a in out["applicability"] if a["clause"] == "Risk tiers")
    assert risk_tiers["applies"] is True
    assert "Foundational" in risk_tiers["reason"]


def test_clinical_use_case_matches_high_risk_clause():
    # "clinical imaging" and "high-risk medical/clinical" share the health domain group.
    out = check("clinical imaging classifier")
    high_risk = next(a for a in out["applicability"] if a["clause"] == "High-risk obligations")
    assert high_risk["applies"] is True


def test_unrelated_clause_marked_not_applicable():
    # A clinical imaging tool is not a conversational assistant — transparency clause N/A.
    out = check("clinical imaging classifier")
    limited = next(a for a in out["applicability"] if a["clause"] == "Limited-risk transparency")
    assert limited["applies"] is False
    assert "No direct connection" in limited["reason"]


def test_chatbot_use_case_flips_transparency_clause():
    out = check("customer service chatbot assistant")
    limited = next(a for a in out["applicability"] if a["clause"] == "Limited-risk transparency")
    assert limited["applies"] is True


def test_off_scope_regulation_has_limited_applicability():
    reg = {
        "id": "reg-hipaa-ai",
        "name": "HIPAA",
        "frontmatter": {"geo": "us-federal", "industry_scope": ["healthcare"]},
        "body": "# HIPAA\n\nIntro.\n\n## Audit & access\n\nLog access to PHI.\n",
    }
    out = check("credit scoring model", industry="financial-services", geography="EU", reg=reg)
    assert out["regulation_applies"] is False
    assert "limited applicability" in out["overall"].lower()
