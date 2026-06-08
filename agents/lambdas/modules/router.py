"""Module-agents Lambda entry point + static dispatch registry.

The orchestrator's ``invoke_module`` tool sends ``{"agent_id": "...", "args": {...}}``
to this one Lambda (AD-01: 26 module agents, one function). Routing is an explicit
dict from ``agent_id`` to a zero-arg factory that builds the agent — no Strands, per
``vault/decisions/module-agent-routing.md``. Adding a module = one REGISTRY entry +
one :class:`ModuleAgent` subclass.

Unknown / not-yet-built agents return the same ``not_implemented`` shape the
orchestrator already emits for disabled modules, so the chat path degrades
identically whether the registry entry is missing here or disabled in modules.json.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from .agent_03_asset_library import AssetLibraryAgent
from .base import ModuleAgent

# agent_id -> factory. Later module tasks append one line here.
REGISTRY: dict[str, Callable[[], ModuleAgent]] = {
    "AGENT-03": AssetLibraryAgent,
}


def _log(event: str, **fields: Any) -> None:
    ts = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    print(json.dumps({"ts": ts, "event": event, **fields}, separators=(",", ":")), file=sys.stdout)


def route(event: dict[str, Any]) -> dict[str, Any]:
    """Dispatch one ``{agent_id, args}`` event to its agent. Pure (testable)."""
    agent_id = event.get("agent_id")
    args = event.get("args") or {}
    if not isinstance(args, dict):
        return {"status": "error", "agent_id": agent_id, "message": "args must be an object."}

    factory = REGISTRY.get(agent_id or "")
    if factory is None:
        return {
            "status": "not_implemented",
            "agent_id": agent_id,
            "message": f"Agent '{agent_id}' is not available in this Lambda.",
        }

    try:
        return factory().handle(args)
    except Exception as exc:  # noqa: BLE001 — never surface a raw stack to the caller
        _log("module_agent_error", agent_id=agent_id, error=f"{type(exc).__name__}: {exc}")
        return {
            "status": "error",
            "agent_id": agent_id,
            "message": "The module agent failed to process the request.",
        }


def handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Lambda entry point."""
    result = route(event)
    _log("module_agent_invoke", agent_id=event.get("agent_id"), status=result.get("status"))
    return result
