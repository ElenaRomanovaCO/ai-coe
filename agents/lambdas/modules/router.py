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

from .agent_02_assessment import AssessmentAgent
from .agent_03_asset_library import AssetLibraryAgent
from .agent_04_kit_builder import KitBuilderAgent
from .agent_05_governance import GovernanceAgent
from .agent_08_tools import ToolsRepoAgent
from .agent_09_qa import QaAgent
from .agent_11_prompts import PromptStudioAgent
from .agent_12_ideation import IdeationAgent
from .agent_13_vendor_eval import VendorEvalAgent
from .agent_16_dashboard import DashboardAgent
from .agent_17_health import ProjectHealthAgent
from .agent_18_decisions import DecisionsAgent
from .agent_20_ethics import EthicsAgent
from .agent_23_feed import FeedAgent
from .agent_24_compliance import ComplianceAgent
from .agent_25_asset_qa import AssetQAAgent
from .agent_27_exchange import ExchangeAgent
from .base import ModuleAgent

# agent_id -> factory. Later module tasks append one line here.
REGISTRY: dict[str, Callable[[], ModuleAgent]] = {
    "AGENT-02": AssessmentAgent,
    "AGENT-03": AssetLibraryAgent,
    "AGENT-04": KitBuilderAgent,
    "AGENT-05": GovernanceAgent,
    "AGENT-08": ToolsRepoAgent,
    "AGENT-09": QaAgent,
    "AGENT-11": PromptStudioAgent,
    "AGENT-12": IdeationAgent,
    "AGENT-13": VendorEvalAgent,
    "AGENT-16": DashboardAgent,
    "AGENT-17": ProjectHealthAgent,
    "AGENT-18": DecisionsAgent,
    "AGENT-20": EthicsAgent,
    "AGENT-23": FeedAgent,
    "AGENT-24": ComplianceAgent,
    "AGENT-25": AssetQAAgent,
    "AGENT-27": ExchangeAgent,
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
