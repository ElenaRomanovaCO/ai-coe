"""HTTP server for AGENT-01 (thin FastAPI wrapper, SSE streaming).

One real endpoint, ``POST /chat``: accepts a :class:`ChatRequest`, loads the
session's prior turns from S3, streams the orchestrator's events back as
Server-Sent Events, and persists the completed turn. ``GET /healthz`` is the
health check.

This same app runs in two places (see ``vault/decisions/poc-runtime.md``):

  - **POC: a streaming Lambda** via the Lambda Web Adapter (Function URL,
    ``InvokeMode=RESPONSE_STREAM``) — ~$0 idle. The config cache is refreshed
    per-invocation (``refresh_if_stale``) because Lambda freezes the environment
    between requests, so a background thread can't be relied on to tick.
  - **Scale-up: Fargate** (always warm) — the background refresh daemon ticks
    every 60s. Kept here for that path and for local dev.

Buffering is disabled on the response so first-token latency (NFR-001) isn't
swallowed by the adapter.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator

from .agent_01_chat import ChatOrchestrator
from .cache import build_default_cache
from .models import ChatRequest
from .refresh import DEFAULT_INTERVAL_SECONDS, refresh_if_stale, start_refresh_loop
from .sessions import SessionStore


def _on_lambda() -> bool:
    """True when running inside the Lambda execution environment."""
    return bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("AWS_LWA_INVOKE_MODE"))


def format_sse(event: dict) -> str:
    """Render one orchestrator event as an SSE frame (pure; unit-tested)."""
    name = event.get("event", "message")
    data = json.dumps(event.get("data", {}), separators=(",", ":"))
    return f"event: {name}\ndata: {data}\n\n"


class Orchestrator:
    """Holds the long-lived singletons (cache, agent, session store) for the server."""

    def __init__(
        self,
        *,
        vault_bucket: str,
        sessions_bucket: str,
        region: str = "us-east-1",
        refresh_interval: float = DEFAULT_INTERVAL_SECONDS,
        use_daemon: bool | None = None,
    ) -> None:
        self.cache = build_default_cache(vault_bucket=vault_bucket, region=region)
        self.cache.load_or_raise()
        self.refresh_max_age = refresh_interval
        # On always-on hosts (local/Fargate) run the daemon; on Lambda rely on the
        # per-invocation stale check (the daemon can't tick while frozen).
        self.use_daemon = (not _on_lambda()) if use_daemon is None else use_daemon
        if self.use_daemon:
            start_refresh_loop(self.cache, interval=refresh_interval)
        self.agent = ChatOrchestrator(cache=self.cache)
        self.sessions = SessionStore(bucket=sessions_bucket, region=region)

    def stream_chat(self, request: ChatRequest) -> Iterator[str]:
        """Yield SSE frames for one chat turn, persisting the turn on completion."""
        # Per-invocation hot-reload (no-op when the daemon already keeps it fresh).
        refresh_if_stale(self.cache, max_age=self.refresh_max_age)
        doc = self.sessions.load(request.display_name, request.session_id)
        history = self.sessions.to_converse_messages(doc)
        final = None
        for event in self.agent.stream(request, history):
            if event.get("event") == "done":
                final = event["data"]
            yield format_sse(event)
        if final is not None:
            try:
                from .models import ChatResponse

                self.sessions.append_turn(
                    doc,
                    request_id=request.request_id,
                    user_message=request.message,
                    response=ChatResponse.model_validate(final),
                )
            except Exception as exc:  # noqa: BLE001 — persistence must not break the response
                print(json.dumps({"event": "session_persist_error", "error": str(exc)}))


def create_app(orchestrator: Orchestrator | None = None):
    """Build the FastAPI app. ``orchestrator`` is injectable for testing."""
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse

    app = FastAPI(title="AI CoE Chat Orchestrator (AGENT-01)")
    state: dict[str, Orchestrator | None] = {"orch": orchestrator}

    def _orch() -> Orchestrator:
        if state["orch"] is None:
            state["orch"] = Orchestrator(
                vault_bucket=os.environ["VAULT_BUCKET"],
                sessions_bucket=os.environ["SESSIONS_BUCKET"],
                region=os.environ.get("AWS_REGION", "us-east-1"),
            )
        return state["orch"]

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok", "agent": "AGENT-01"}

    @app.post("/chat")
    def chat(request: ChatRequest) -> StreamingResponse:
        return StreamingResponse(
            _orch().stream_chat(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # don't let any proxy buffer the stream
            },
        )

    return app


def __getattr__(name: str):
    """Lazily build the ASGI app on first access (``uvicorn server:app``).

    Defined as a module-level hook (PEP 562) so importing this module for its pure
    helpers (e.g. format_sse) in the test suite never imports FastAPI, which is a
    runtime-only dependency.
    """
    if name == "app":
        return create_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
