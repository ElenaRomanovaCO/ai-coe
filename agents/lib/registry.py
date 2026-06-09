"""Module registry — the single source of truth for which modules exist.

Backed by ``vault/modules.json`` (AD-03), validated against these Pydantic
models at load. The JSON Schema written to ``vault/_schema/modules.schema.json``
is generated from these models so the two never drift.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class ModuleEntry(BaseModel):
    id: str = Field(description='e.g. "module-2"')
    name: str = Field(description='e.g. "Asset Library"')
    wave: int = Field(ge=1, le=7)
    purpose: str = Field(description="one-line summary")
    when_to_use: list[str] = Field(default_factory=list, description="bullet examples")
    example_queries: list[str] = Field(
        default_factory=list, description="example user phrases that should route here"
    )
    agent_id: str = Field(description='e.g. "AGENT-03"')
    model_tier: Literal["haiku-4-5", "sonnet-4-6", "opus-4-7"]
    worker_ids: list[str] = Field(default_factory=list)
    enabled: bool = False
    # Optional dedicated UI route. When set, the orchestrator routes the user to
    # this page (a "navigate" UIAction) instead of running the module inline in
    # chat — for guided, multi-step modules (e.g. the maturity assessment).
    ui_route: str | None = None


class ModuleRegistry(BaseModel):
    version: int = 1
    modules: list[ModuleEntry] = Field(default_factory=list)

    def enabled_modules(self) -> list[ModuleEntry]:
        return [m for m in self.modules if m.enabled]

    def by_id(self, module_id: str) -> ModuleEntry | None:
        return next((m for m in self.modules if m.id == module_id), None)


def load_registry(source: str | bytes | dict | Path) -> ModuleRegistry:
    """Validate and load a registry from a path, JSON string/bytes, or dict."""
    if isinstance(source, Path):
        return ModuleRegistry.model_validate_json(source.read_text(encoding="utf-8"))
    if isinstance(source, dict):
        return ModuleRegistry.model_validate(source)
    return ModuleRegistry.model_validate_json(source)


def json_schema() -> dict:
    return ModuleRegistry.model_json_schema()


def write_json_schema(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_schema(), indent=2) + "\n", encoding="utf-8")
    return path
