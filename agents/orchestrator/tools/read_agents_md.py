"""``read_agents_md`` — return the cached behavior rules (FR-005).

The orchestrator folds agents.md into its system prompt every turn, but exposing
it as a tool lets the model re-read the rules mid-conversation if it needs to.
Reads from the in-memory cache (refreshed every 60s), never from S3 directly.
"""

from __future__ import annotations

from typing import Any


def read_agents_md(*, cache: Any) -> str:
    return cache.agents_md
