"""Session persistence in S3 (AD-04) — no database.

State is a single JSON object per session at
``sessions/{display_name}/{session_id}.json`` in the sessions bucket. Each turn
appends a record; the orchestrator loads prior turns as Converse history on the
next request. ``display_name`` is slugified for the key (safe path segment) while
the raw value is kept inside the document for display.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import ClientError

from .models import ChatResponse

_SLUG_UNSAFE = re.compile(r"[^a-zA-Z0-9._-]+")
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def slugify_display_name(display_name: str) -> str:
    """Make a display name safe to embed in an S3 key. Empty -> 'anon'."""
    slug = _SLUG_UNSAFE.sub("-", display_name.strip()).strip("-").lower()
    return slug or "anon"


class SessionStore:
    def __init__(self, *, bucket: str, region: str = "us-east-1", s3: Any = None) -> None:
        self.bucket = bucket
        self.region = region
        self._s3 = s3

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    def _key(self, display_name: str, session_id: str) -> str:
        return f"sessions/{slugify_display_name(display_name)}/{session_id}.json"

    def load(self, display_name: str, session_id: str) -> dict:
        """Return the session document, or a fresh one if none exists yet."""
        try:
            resp = self.s3.get_object(
                Bucket=self.bucket, Key=self._key(display_name, session_id)
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] in _NOT_FOUND:
                return {
                    "session_id": session_id,
                    "display_name": display_name,
                    "created_at": _now_iso(),
                    "updated_at": _now_iso(),
                    "turns": [],
                }
            raise
        return json.loads(resp["Body"].read())

    def to_converse_messages(self, doc: dict, *, max_turns: int = 20) -> list[dict]:
        """Convert stored turns into Converse ``messages`` (most recent ``max_turns``)."""
        messages: list[dict] = []
        for turn in doc.get("turns", [])[-max_turns:]:
            messages.append({"role": "user", "content": [{"text": turn["user_message"]}]})
            messages.append(
                {"role": "assistant", "content": [{"text": turn["assistant_message"]}]}
            )
        return messages

    def append_turn(
        self,
        doc: dict,
        *,
        request_id: str,
        user_message: str,
        response: ChatResponse,
    ) -> dict:
        """Append one turn and persist the whole document. Returns the updated doc."""
        doc.setdefault("turns", []).append(
            {
                "request_id": request_id,
                "ts": _now_iso(),
                "user_message": user_message,
                "assistant_message": response.assistant_message,
                "citations": [c.model_dump() for c in response.citations],
                "invoked_modules": response.invoked_modules,
                "ui_actions": [a.model_dump() for a in response.ui_actions],
            }
        )
        doc["updated_at"] = _now_iso()
        self.s3.put_object(
            Bucket=self.bucket,
            Key=self._key(doc["display_name"], doc["session_id"]),
            Body=json.dumps(doc, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )
        return doc
