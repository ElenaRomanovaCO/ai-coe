"""Instrumentation base for all agents.

Provides a single primitive — :func:`instrumented` — that wraps any unit of work
(a tool call, a model call) and guarantees exactly one structured log line plus
the standard CloudWatch metric set are emitted, with timing and outcome derived
automatically. :class:`BaseAgent` is the thin Strands-compatible base that module
agents and workers subclass.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from . import metrics
from .cost_cap import OpusCapExceeded
from .logging import Outcome, log_invocation


@dataclass
class Usage:
    """Mutable handle the instrumented block fills in as work happens."""

    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    model_id: str | None = None


def classify_outcome(exc: BaseException) -> Outcome:
    if isinstance(exc, OpusCapExceeded):
        return "refused"
    if isinstance(exc, TimeoutError):
        return "timeout"
    haystack = f"{type(exc).__name__} {exc}".lower()
    if "validation" in haystack or "schema" in haystack:
        return "schema_failure"
    return "llm_error"


def new_request_id() -> str:
    return "req_" + uuid.uuid4().hex[:12]


@contextmanager
def instrumented(
    *,
    agent_id: str,
    tool_name: str,
    request_id: str | None = None,
    session_id: str | None = None,
    display_name: str | None = None,
    model_id: str | None = None,
    parent_agent: str | None = None,
    depth: int = 0,
    metrics_client: Any = None,
    emit_metrics: bool = True,
) -> Iterator[Usage]:
    """Wrap a unit of work; emit one log line + metrics on exit (success or error)."""
    usage = Usage(model_id=model_id)
    request_id = request_id or new_request_id()
    start = time.perf_counter()
    outcome: Outcome = "success"
    try:
        yield usage
    except BaseException as exc:  # noqa: BLE001 — re-raised after recording
        outcome = classify_outcome(exc)
        raise
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        resolved_model = usage.model_id or model_id
        log_invocation(
            request_id=request_id,
            agent_id=agent_id,
            outcome=outcome,
            session_id=session_id,
            display_name=display_name,
            tool_name=tool_name,
            model_id=resolved_model,
            tokens_in=usage.tokens_in,
            tokens_out=usage.tokens_out,
            cost_usd=usage.cost_usd,
            latency_ms=latency_ms,
            parent_agent=parent_agent,
            depth=depth,
        )
        if emit_metrics:
            try:
                metrics.record_invocation(
                    agent_id=agent_id,
                    outcome=outcome,
                    latency_ms=latency_ms,
                    tokens_in=usage.tokens_in,
                    tokens_out=usage.tokens_out,
                    model_id=resolved_model or "unknown",
                    cost_usd=usage.cost_usd,
                    client=metrics_client,
                )
            except Exception:  # noqa: BLE001 — metrics must never break a request
                pass


class BaseAgent:
    """Common base for agents. Subclasses declare ``agent_id`` and ``model_id``."""

    agent_id: str = "AGENT-00"
    model_id: str | None = None

    def __init__(
        self,
        *,
        agent_id: str | None = None,
        model_id: str | None = None,
        session_id: str | None = None,
        display_name: str | None = None,
        metrics_client: Any = None,
    ) -> None:
        if agent_id is not None:
            self.agent_id = agent_id
        if model_id is not None:
            self.model_id = model_id
        self.session_id = session_id
        self.display_name = display_name
        self.metrics_client = metrics_client

    def run_tool(
        self,
        tool_name: str,
        fn: Callable[[Usage], Any],
        *,
        request_id: str | None = None,
        parent_agent: str | None = None,
        depth: int = 0,
    ) -> Any:
        """Run ``fn(usage)`` fully instrumented. ``fn`` may set token/cost fields on ``usage``."""
        with instrumented(
            agent_id=self.agent_id,
            tool_name=tool_name,
            request_id=request_id,
            session_id=self.session_id,
            display_name=self.display_name,
            model_id=self.model_id,
            parent_agent=parent_agent,
            depth=depth,
            metrics_client=self.metrics_client,
        ) as usage:
            return fn(usage)
