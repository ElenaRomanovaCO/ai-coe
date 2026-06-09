"""Common base for Layer 3 workers — mirrors the module-agent contract.

A worker is a :class:`~agents.lib.base_agent.BaseAgent` with a single
``handle(args)`` entry point; the worker router dispatches on ``worker_id``.
"""

from __future__ import annotations

from typing import Any

from agents.lib.base_agent import BaseAgent


class Worker(BaseAgent):
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
