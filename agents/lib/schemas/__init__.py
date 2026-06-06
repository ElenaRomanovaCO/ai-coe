"""Per-content-type frontmatter schemas for the vault.

Every markdown file under ``vault/<type>/`` carries a YAML frontmatter block that
must validate against the matching model here. ``scripts/validate_vault.py`` (and
the pre-commit hook) use :func:`validate_frontmatter` to block malformed content
before it reaches S3, where the ReEmbed Lambda would index it as-is.

The folder's first path segment selects the schema (see ``CONTENT_TYPE_BY_FOLDER``
and :func:`content_type_for_path`).
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal

import yaml
from pydantic import BaseModel


class AssetFrontmatter(BaseModel):
    id: str
    title: str
    type: Literal[
        "reference-architecture",
        "solution-pattern",
        "kickoff-template",
        "discovery-questionnaire",
        "workshop-agenda",
        "roi-template",
        "risk-checklist",
    ]
    industry: Literal[
        "financial-services",
        "healthcare",
        "retail",
        "manufacturing",
        "energy",
        "public-sector",
        "technology",
        "professional-services",
        "cross-industry",
    ]
    ai_stage: int
    use_case_type: list[str]
    tags: list[str]
    contributor: str = "demo"
    updated_at: str


class ToolFrontmatter(BaseModel):
    id: str
    name: str
    category: Literal[
        "framework",
        "vector-db",
        "llm-provider",
        "orchestration",
        "evals",
        "guardrails",
        "deployment",
    ]
    stack: list[str]
    ai_stage_fit: list[int]
    cost_model: Literal["open-source", "free-tier", "usage-based", "subscription", "enterprise"]
    limitations: list[str]
    tags: list[str]


class VendorEvalFrontmatter(BaseModel):
    id: str
    category: Literal["llm-provider", "vector-db", "cloud-ai-platform", "orchestration-framework"]
    vendors_compared: list[str]
    criteria: list[str]
    last_verified: str


class RegulationFrontmatter(BaseModel):
    id: str
    name: str
    geo: Literal["eu", "us-federal", "us-state-ca", "us-state-ny", "uk", "canada", "global"]
    industry_scope: list[str]
    status: Literal["proposed", "enacted", "in-effect", "superseded"]
    effective_date: str | None = None
    risk_tier: str | None = None
    tags: list[str]


class FeedItemFrontmatter(BaseModel):
    id: str
    title: str
    category: Literal["model-release", "tool-launch", "research", "vendor-update", "industry-news"]
    source_url: str
    published_at: str
    industries: list[str]
    tags: list[str]
    radar_status: Literal["adopt", "trial", "assess", "hold"] | None = None


class PromptFrontmatter(BaseModel):
    id: str
    title: str
    use_case: str
    model_targets: list[str]
    variables: list[str]
    version: int = 1
    parent_id: str | None = None


class SampleDocFrontmatter(BaseModel):
    """Light schema for demo-continuity samples (assessments, kits, decisions).

    These are illustrative rather than typed content surfaces, so they only need a
    stable id/title plus a kind tag and an ISO date.
    """

    id: str
    title: str
    kind: Literal["assessment", "kit", "decision"]
    owner: str = "demo"
    updated_at: str


# First path segment under vault/ -> (content type label, schema).
CONTENT_TYPE_BY_FOLDER: dict[str, tuple[str, type[BaseModel]]] = {
    "assets": ("asset", AssetFrontmatter),
    "tools": ("tool", ToolFrontmatter),
    "vendors": ("vendor", VendorEvalFrontmatter),
    "regs": ("regulation", RegulationFrontmatter),
    "feed": ("feed", FeedItemFrontmatter),
    "prompts": ("prompt", PromptFrontmatter),
    "assessments": ("assessment", SampleDocFrontmatter),
    "kits": ("kit", SampleDocFrontmatter),
    "decisions": ("decision", SampleDocFrontmatter),
}


class FrontmatterError(ValueError):
    """Raised when a vault file's frontmatter is missing or invalid."""


def content_type_for_path(path: str) -> tuple[str, type[BaseModel]] | None:
    """Return (label, schema) for a vault-relative path, or None if untyped.

    ``path`` is relative to the vault root (e.g. ``assets/healthcare/2/x.md``).
    Top-level files (``agents.md``, ``modules.json``) and ``_schema/`` are untyped.
    """
    parts = PurePosixPath(path).parts
    if not parts:
        return None
    return CONTENT_TYPE_BY_FOLDER.get(parts[0])


def parse_frontmatter(text: str) -> dict:
    """Extract and parse the leading ``--- ... ---`` YAML block as a dict."""
    if not text.startswith("---"):
        raise FrontmatterError("file does not start with a '---' frontmatter block")
    end = text.find("\n---", 3)
    if end == -1:
        raise FrontmatterError("unterminated frontmatter block (no closing '---')")
    raw = text[3:end]
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:  # noqa: TRY003
        raise FrontmatterError(f"invalid YAML in frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise FrontmatterError("frontmatter did not parse to a mapping")
    return data


def validate_frontmatter(content_type_schema: type[BaseModel], data: dict) -> BaseModel:
    return content_type_schema.model_validate(data)
