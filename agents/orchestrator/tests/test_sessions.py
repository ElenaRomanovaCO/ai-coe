import io
import json

from botocore.exceptions import ClientError

from agents.orchestrator.models import ChatResponse, Citation
from agents.orchestrator.sessions import SessionStore, slugify_display_name


class FakeS3:
    def __init__(self):
        self.objects: dict[tuple[str, str], bytes] = {}

    def get_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "missing"}}, "GetObject"
            )
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}

    def put_object(self, Bucket, Key, Body, **kwargs):
        self.objects[(Bucket, Key)] = Body


def test_slugify():
    assert slugify_display_name("Alex Smith") == "alex-smith"
    assert slugify_display_name("  ") == "anon"
    assert slugify_display_name("a/b\\c") == "a-b-c"


def test_load_missing_returns_fresh_doc():
    store = SessionStore(bucket="b", s3=FakeS3())
    doc = store.load("Alex", "s1")
    assert doc["turns"] == []
    assert doc["session_id"] == "s1"
    assert doc["display_name"] == "Alex"


def test_append_and_reload_roundtrip():
    s3 = FakeS3()
    store = SessionStore(bucket="b", s3=s3)
    doc = store.load("Alex Smith", "s1")
    resp = ChatResponse(
        assistant_message="hello",
        citations=[Citation(file_path="assets/a.md", chunk_index=0, content_type="asset")],
        invoked_modules=["module-1"],
    )
    store.append_turn(doc, request_id="r1", user_message="hi", response=resp)

    # Stored under the slugified key.
    assert ("b", "sessions/alex-smith/s1.json") in s3.objects
    reloaded = store.load("Alex Smith", "s1")
    assert len(reloaded["turns"]) == 1
    assert reloaded["turns"][0]["assistant_message"] == "hello"
    assert reloaded["turns"][0]["invoked_modules"] == ["module-1"]


def test_to_converse_messages_shape_and_truncation():
    s3 = FakeS3()
    store = SessionStore(bucket="b", s3=s3)
    doc = store.load("A", "s1")
    for i in range(25):
        store.append_turn(
            doc,
            request_id=f"r{i}",
            user_message=f"u{i}",
            response=ChatResponse(assistant_message=f"a{i}"),
        )
    messages = store.to_converse_messages(doc, max_turns=20)
    assert len(messages) == 40  # 20 turns * (user + assistant)
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    # Oldest 5 turns dropped; first retained user message is u5.
    assert messages[0]["content"][0]["text"] == "u5"


def test_stored_json_is_valid():
    s3 = FakeS3()
    store = SessionStore(bucket="b", s3=s3)
    doc = store.load("A", "s1")
    store.append_turn(
        doc, request_id="r", user_message="hi", response=ChatResponse(assistant_message="ok")
    )
    raw = s3.objects[("b", "sessions/a/s1.json")]
    assert json.loads(raw)["turns"][0]["user_message"] == "hi"
