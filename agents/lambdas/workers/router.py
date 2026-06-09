"""Workers Lambda entry point + static dispatch registry.

Module agents send ``{"worker_id": "...", "args": {...}}`` to ``aicoe-workers-lambda``;
this dispatches to the worker. Same no-Strands pattern as the module router (see
``vault/decisions/worker-pattern.md``). Adding a worker = one REGISTRY line + one
:class:`Worker` subclass.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from .base import Worker
from .worker_01_question_picker import QuestionPickerWorker
from .worker_02_scorer import ScorerWorker
from .worker_03_recommender import RecommenderWorker

REGISTRY: dict[str, Callable[[], Worker]] = {
    "WORKER-01": QuestionPickerWorker,
    "WORKER-02": ScorerWorker,
    "WORKER-03": RecommenderWorker,
}


def _log(event: str, **fields: Any) -> None:
    ts = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    print(json.dumps({"ts": ts, "event": event, **fields}, separators=(",", ":")), file=sys.stdout)


def route(event: dict[str, Any]) -> dict[str, Any]:
    worker_id = event.get("worker_id")
    args = event.get("args") or {}
    if not isinstance(args, dict):
        return {"status": "error", "worker_id": worker_id, "message": "args must be an object."}

    factory = REGISTRY.get(worker_id or "")
    if factory is None:
        return {
            "status": "not_implemented",
            "worker_id": worker_id,
            "message": f"Worker '{worker_id}' is not available in this Lambda.",
        }
    try:
        return factory().handle(args)
    except Exception as exc:  # noqa: BLE001 — never surface a raw stack
        _log("worker_error", worker_id=worker_id, error=f"{type(exc).__name__}: {exc}")
        return {
            "status": "error",
            "worker_id": worker_id,
            "message": "The worker failed to process the request.",
        }


def handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    result = route(event)
    _log("worker_invoke", worker_id=event.get("worker_id"), status=result.get("status"))
    return result
