"""``list_modules`` — filtered registry browse (FR-007).

Filters the cached registry by wave and/or a free-text keyword (matched across
name, purpose, when_to_use, and example_queries) and returns compact summaries.
"""

from __future__ import annotations

from agents.lib.registry import ModuleEntry, ModuleRegistry

from ..models import ModuleSummary


def _matches_keyword(module: ModuleEntry, keyword: str) -> bool:
    needle = keyword.lower()
    haystacks = [module.name, module.purpose, *module.when_to_use, *module.example_queries]
    return any(needle in h.lower() for h in haystacks)


def list_modules(
    wave: int | None = None,
    keyword: str | None = None,
    *,
    registry: ModuleRegistry,
) -> list[ModuleSummary]:
    modules = registry.modules
    if wave is not None:
        modules = [m for m in modules if m.wave == wave]
    if keyword:
        modules = [m for m in modules if _matches_keyword(m, keyword)]
    return [
        ModuleSummary(
            id=m.id, name=m.name, wave=m.wave, purpose=m.purpose, enabled=m.enabled
        )
        for m in modules
    ]
