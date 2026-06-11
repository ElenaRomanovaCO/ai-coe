"""ReEmbed Lambda: S3 object change -> chunk -> embed -> upsert to S3 Vectors.

Triggered by EventBridge for ``s3:ObjectCreated:*`` and ``s3:ObjectRemoved:*``
on the vault bucket. Only ``.md`` objects are processed. Content is hashed
(SHA-256) and the hash is stored in vector metadata so unchanged files are
skipped on redundant events.

The work is done by :class:`ReEmbedder`, which takes injectable AWS clients so
the routing/dedup logic is unit-testable without AWS. ``handler`` is the Lambda
entry point that wires real clients from environment variables.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.parse
from datetime import UTC, datetime
from typing import Any

try:
    from .chunker import chunk_markdown  # package import (local tests)
except ImportError:  # pragma: no cover - flat layout in the Lambda zip
    from chunker import chunk_markdown

EMBED_DIMENSIONS = 1024
_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_ID_LINE = re.compile(r"^id:\s*(.+?)\s*$", re.MULTILINE)
# Runtime-generated vault artifacts (assessments, governance reviews, ideations, …)
# carry `generated: true` in frontmatter; we flag their vectors so chat's
# search_knowledge_base can scope them out of curated KB results. The "generated"
# key is shared (as a literal) with vault_export.py + search_knowledge_base.py.
_GENERATED_LINE = re.compile(r"^generated:\s*true\s*$", re.IGNORECASE | re.MULTILINE)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _frontmatter_id(text: str) -> str | None:
    fm = _FRONTMATTER.match(text)
    if not fm:
        return None
    m = _ID_LINE.search(fm.group(1))
    return m.group(1).strip().strip("\"'") if m else None


def _frontmatter_generated(text: str) -> bool:
    """True if the file's frontmatter marks it a runtime-generated artifact."""
    fm = _FRONTMATTER.match(text)
    return bool(fm and _GENERATED_LINE.search(fm.group(1)))


def _content_type(key: str) -> str:
    """Derive a coarse content type from the key's leading path segment."""
    parts = [p for p in key.split("/") if p]
    if len(parts) >= 2 and parts[0] == "vault":
        return parts[1]
    return parts[0] if parts else "content"


def extract_records(event: dict) -> list[tuple[str, str, str]]:
    """Normalize an EventBridge S3 event into (bucket, key, kind) tuples.

    kind is "created" or "removed". Supports both the EventBridge S3 detail
    shape and the classic S3 notification ``Records`` shape.
    """
    out: list[tuple[str, str, str]] = []

    detail = event.get("detail")
    if detail and "bucket" in detail and "object" in detail:
        bucket = detail["bucket"]["name"]
        key = urllib.parse.unquote_plus(detail["object"]["key"])
        detail_type = event.get("detail-type", "")
        kind = "removed" if ("Removed" in detail_type or "Deleted" in detail_type) else "created"
        out.append((bucket, key, kind))
        return out

    for rec in event.get("Records", []):
        s3 = rec.get("s3", {})
        bucket = s3.get("bucket", {}).get("name")
        key = urllib.parse.unquote_plus(s3.get("object", {}).get("key", ""))
        if not bucket or not key:
            continue
        kind = "removed" if rec.get("eventName", "").startswith("ObjectRemoved") else "created"
        out.append((bucket, key, kind))
    return out


class ReEmbedder:
    def __init__(
        self,
        *,
        vector_bucket: str,
        index_name: str,
        embed_model: str,
        s3: Any = None,
        bedrock: Any = None,
        s3vectors: Any = None,
        region: str = "us-east-1",
    ) -> None:
        self.vector_bucket = vector_bucket
        self.index_name = index_name
        self.embed_model = embed_model
        self.region = region
        self._s3 = s3
        self._bedrock = bedrock
        self._s3vectors = s3vectors

    # --- lazy clients ------------------------------------------------------
    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    @property
    def bedrock(self) -> Any:
        if self._bedrock is None:
            import boto3

            self._bedrock = boto3.client("bedrock-runtime", region_name=self.region)
        return self._bedrock

    @property
    def s3vectors(self) -> Any:
        if self._s3vectors is None:
            import boto3

            self._s3vectors = boto3.client("s3vectors", region_name=self.region)
        return self._s3vectors

    # --- public API --------------------------------------------------------
    def process_event(self, event: dict) -> list[dict]:
        results: list[dict] = []
        for bucket, key, kind in extract_records(event):
            if not key.endswith(".md"):
                results.append({"key": key, "action": "skipped_non_md"})
                continue
            if kind == "removed":
                self._delete(key)
                results.append({"key": key, "action": "deleted"})
            else:
                results.append(self._upsert(bucket, key))
        return results

    # --- internals ---------------------------------------------------------
    def _get_object_bytes(self, bucket: str, key: str) -> bytes:
        return self.s3.get_object(Bucket=bucket, Key=key)["Body"].read()

    def _embed(self, text: str) -> list[float]:
        resp = self.bedrock.invoke_model(
            modelId=self.embed_model,
            body=json.dumps({"inputText": text, "dimensions": EMBED_DIMENSIONS, "normalize": True}),
        )
        payload = json.loads(resp["body"].read())
        return payload["embedding"]

    def _existing_hash(self, key: str) -> str | None:
        """Return the stored content hash for a file (from its first chunk), if any."""
        try:
            resp = self.s3vectors.get_vectors(
                vectorBucketName=self.vector_bucket,
                indexName=self.index_name,
                keys=[f"{key}#0"],
                returnMetadata=True,
            )
        except Exception:  # noqa: BLE001 — missing key/index -> treat as changed
            return None
        for v in resp.get("vectors", []):
            return v.get("metadata", {}).get("content_hash")
        return None

    def _upsert(self, bucket: str, key: str) -> dict:
        body = self._get_object_bytes(bucket, key)
        content_hash = hashlib.sha256(body).hexdigest()
        if self._existing_hash(key) == content_hash:
            return {"key": key, "action": "unchanged"}

        text = body.decode("utf-8")
        fm_id = _frontmatter_id(text)
        ctype = _content_type(key)
        # True only for runtime-generated artifacts; omitted otherwise so curated
        # content carries no flag (and the None-filter below keeps metadata small).
        generated = _frontmatter_generated(text) or None
        updated_at = _now_iso()
        chunks = chunk_markdown(text)

        vectors = []
        for ch in chunks:
            embedding = self._embed(ch.text)
            metadata = {
                "file_path": key,
                "content_type": ctype,
                "generated": generated,
                "frontmatter_id": fm_id,
                "chunk_index": ch.index,
                "updated_at": updated_at,
                "content_hash": content_hash,
                "heading_path": " > ".join(ch.heading_path),
            }
            # S3 Vectors rejects null metadata values; omit absent fields
            # (e.g. frontmatter_id when a file has no YAML frontmatter).
            metadata = {k: v for k, v in metadata.items() if v is not None}
            vectors.append(
                {
                    "key": f"{key}#{ch.index}",
                    "data": {"float32": embedding},
                    "metadata": metadata,
                }
            )

        # Replace any stale chunks (file may have fewer chunks than before),
        # then write the fresh set.
        self._delete(key)
        if vectors:
            self.s3vectors.put_vectors(
                vectorBucketName=self.vector_bucket,
                indexName=self.index_name,
                vectors=vectors,
            )
        return {"key": key, "action": "embedded", "chunks": len(vectors)}

    def _delete(self, key: str) -> None:
        """Delete all chunk vectors for a file. Best-effort across chunk indices."""
        # We don't know how many chunks existed; delete a generous range. S3
        # Vectors ignores keys that don't exist.
        keys = [f"{key}#{i}" for i in range(256)]
        try:
            self.s3vectors.delete_vectors(
                vectorBucketName=self.vector_bucket,
                indexName=self.index_name,
                keys=keys,
            )
        except Exception:  # noqa: BLE001 — nothing to delete is fine
            pass


def handler(event: dict, context: Any = None) -> dict:
    embedder = ReEmbedder(
        vector_bucket=os.environ["VECTOR_BUCKET"],
        index_name=os.environ.get("VECTOR_INDEX", "aicoe-content"),
        embed_model=os.environ.get("EMBED_MODEL", "amazon.titan-embed-text-v2:0"),
        region=os.environ.get("AWS_REGION", "us-east-1"),
    )
    results = embedder.process_event(event)
    print(json.dumps({"event": "reembed", "results": results}, separators=(",", ":")))
    return {"ok": True, "results": results}
