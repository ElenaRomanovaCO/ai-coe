"""Structured invocation logging.

Every agent/tool invocation emits exactly one JSON line to stdout, which
CloudWatch Logs captures. The shape is fixed (see ai_docs design + task 00) so
that metric filters and downstream tooling can rely on it.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from typing import Any, Literal

Outcome = Literal["success", "schema_failure", "llm_error", "timeout", "refused"]

_REQUIRED = ("ts", "request_id", "agent_id", "outcome")


def _now_iso() -> str:
    # Millisecond precision, Z suffix — e.g. 2026-06-03T14:23:45.123Z
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def hash_display_name(display_name: str | None) -> str | None:
    """Hash a display name for logging — never log the raw name (PII)."""
    if not display_name:
        return None
    return "sha256:" + hashlib.sha256(display_name.encode("utf-8")).hexdigest()


def build_record(
    *,
    request_id: str,
    agent_id: str,
    outcome: Outcome,
    session_id: str | None = None,
    display_name: str | None = None,
    tool_name: str | None = None,
    model_id: str | None = None,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost_usd: float = 0.0,
    latency_ms: int | None = None,
    parent_agent: str | None = None,
    depth: int = 0,
) -> dict[str, Any]:
    """Build the structured log record without emitting it (useful for tests)."""
    return {
        "ts": _now_iso(),
        "request_id": request_id,
        "session_id": session_id,
        "display_name_hash": hash_display_name(display_name),
        "agent_id": agent_id,
        "tool_name": tool_name,
        "model_id": model_id,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "outcome": outcome,
        "trace": {"parent_agent": parent_agent, "depth": depth},
    }


def log_invocation(**fields: Any) -> dict[str, Any]:
    """Emit one structured JSON log line and return the record.

    Accepts the same keyword arguments as :func:`build_record`.
    """
    record = build_record(**fields)
    missing = [k for k in _REQUIRED if record.get(k) in (None, "")]
    if missing:
        raise ValueError(f"log_invocation missing required fields: {missing}")
    print(json.dumps(record, separators=(",", ":")), file=sys.stdout, flush=True)
    return record
