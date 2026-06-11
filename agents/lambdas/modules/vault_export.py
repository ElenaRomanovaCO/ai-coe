"""Frontmatter for runtime-*generated* vault artifacts.

Some module agents write a markdown artifact **into the vault** at request time —
assessment results (AGENT-02), governance reviews (AGENT-05), use-case ideations
(AGENT-12), and the upcoming Decision Log / Retrospective / Benchmark writers. Those
files are picked up by the ReEmbed pipeline and indexed alongside *curated* knowledge,
so without a marker chat's ``search_knowledge_base`` cannot tell a user's generated
artifact apart from curated content (and they share folders — ``assessments/`` holds
both a seeded demo sample and real user runs).

Every runtime vault export MUST carry this frontmatter so the pipeline tags its
vectors ``generated: true`` and chat search scopes them out of curated results. See
``vault/decisions/runtime-vault-writers.md`` for the full convention (incl. the
vault-vs-sessions rule and the deferred multi-tenant scoping).

Transient state, in-progress JSON, and binary deliverables (e.g. kit zips) go to the
**sessions** bucket instead — never indexed, so they don't need this.
"""

from __future__ import annotations

from typing import Any

# Frontmatter key + S3 Vectors metadata key. Kept as a literal here and in
# reembed/handler.py + search_knowledge_base.py (the reembed Lambda stays free of
# agents.lib imports); change all three together.
GENERATED_KEY = "generated"


def _scalar(value: Any) -> str:
    """Render a scalar as safe single-line YAML (quote only when needed)."""
    s = str(value)
    if s == "":
        return '""'
    if any(c in s for c in ':#\n"') or s[0] in "[{>|*&!%@`":
        return '"' + s.replace('"', '\\"').replace("\n", " ") + '"'
    return s


def export_frontmatter(content_type: str, fields: dict[str, Any]) -> str:
    """Build a YAML frontmatter block for a generated vault artifact.

    Always emits ``content_type`` (a human/UI label for the artifact kind) and
    ``generated: true`` (the load-bearing flag the index + search rely on), then the
    given ``fields`` in order (None values skipped; lists rendered inline; one level
    of dict rendered as a nested mapping). Returns the block including the trailing
    ``---`` and newline, ready to prepend to the markdown body.
    """
    lines = ["---", f"content_type: {content_type}", f"{GENERATED_KEY}: true"]
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            lines.append(f"{key}: [{', '.join(_scalar(v) for v in value)}]")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            lines.extend(f"  {k}: {_scalar(v)}" for k, v in value.items())
        else:
            lines.append(f"{key}: {_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"
