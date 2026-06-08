"""Common base for Layer 2 module agents.

A module agent is a :class:`~agents.lib.base_agent.BaseAgent` that exposes a
single ``handle(args)`` entry point. The router (``router.py``) dispatches on
``agent_id``; each agent then dispatches on an ``op`` key to its own operations.
This is the no-Strands routing contract (see
``vault/decisions/module-agent-routing.md``).
"""

from __future__ import annotations

from typing import Any

from agents.lib.base_agent import BaseAgent


class ModuleAgent(BaseAgent):
    """Base class for module agents invoked via ``{agent_id, args}``."""

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute one operation and return a JSON-serializable result.

        ``args`` carries an optional ``op`` selector plus operation parameters.
        Implementations should return ``{"status": "ok", ...}`` on success and a
        structured ``{"status": "error"|"not_found"|..., "message": ...}`` otherwise
        — never raise for expected conditions.
        """
        raise NotImplementedError
