from types import SimpleNamespace

from agents.orchestrator.models import ChatRequest, ChatResponse
from agents.orchestrator.server import Orchestrator, format_sse


def test_format_sse_frame():
    frame = format_sse({"event": "token", "data": {"text": "hi"}})
    assert frame == 'event: token\ndata: {"text":"hi"}\n\n'


def test_format_sse_defaults():
    frame = format_sse({})
    assert frame == "event: message\ndata: {}\n\n"


class FakeSessions:
    def __init__(self):
        self.appended = None

    def load(self, display_name, session_id):
        return {"turns": [], "display_name": display_name, "session_id": session_id}

    def to_converse_messages(self, doc, max_turns=20):
        return []

    def append_turn(self, doc, *, request_id, user_message, response):
        self.appended = response


class FakeAgent:
    def stream(self, request, history):
        yield {"event": "token", "data": {"text": "Hi"}}
        yield {
            "event": "done",
            "data": ChatResponse(assistant_message="Hi").model_dump(),
        }


class FakeCache:
    def __init__(self):
        self.refreshed = False

    def is_stale(self, max_age, now=None):
        return False  # fresh — refresh_if_stale should be a no-op

    def refresh(self):  # pragma: no cover - not reached when fresh
        self.refreshed = True
        return {}


def test_stream_chat_emits_frames_and_persists():
    sessions = FakeSessions()
    cache = FakeCache()
    # Call stream_chat without running __init__ (no S3/refresh-loop needed for this unit).
    orch = SimpleNamespace(
        agent=FakeAgent(), sessions=sessions, cache=cache, refresh_max_age=60
    )
    req = ChatRequest(display_name="A", session_id="s1", request_id="r1", message="hi")

    frames = list(Orchestrator.stream_chat(orch, req))

    assert any(f.startswith("event: token") for f in frames)
    assert any(f.startswith("event: done") for f in frames)
    # The completed turn was persisted with the final assistant message.
    assert sessions.appended is not None
    assert sessions.appended.assistant_message == "Hi"
