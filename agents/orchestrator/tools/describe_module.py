"""``describe_module`` — registry meta-query (FR-006).

Looks a module up in the cached registry and returns its full meta view. Never
invents data: unknown ids return a structured ``not_found`` dict the model can
relay verbatim.
"""

from __future__ import annotations

from agents.lib.registry import ModuleRegistry

from ..models import ModuleDescription


def describe_module(module_id: str, *, registry: ModuleRegistry) -> ModuleDescription | dict:
    module = registry.by_id(module_id)
    if module is None:
        return {
            "status": "not_found",
            "message": f"No module with id '{module_id}' exists in the registry.",
        }
    return ModuleDescription(
        id=module.id,
        name=module.name,
        wave=module.wave,
        purpose=module.purpose,
        when_to_use=module.when_to_use,
        example_queries=module.example_queries,
        agent_id=module.agent_id,
        enabled=module.enabled,
    )
