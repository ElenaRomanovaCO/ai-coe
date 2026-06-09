"""AGENT-16 — Personal Dashboard (Module 17), Haiku 4.5 tier.

Read-only aggregator for the post-login landing page. Composes AGENT-03
(:class:`AssetLibraryAgent`) for asset summaries/search and adds the user's
profile, recent chats, and a recommender. Operations dispatched from
:meth:`handle` on ``op``:

  - ``summary`` (default) — the full DashboardSummary (FR-014)
  - ``read_profile``      — the raw user profile
  - ``recommend``         — top-k recommended assets (FR-015)
  - ``list_recent_chats`` — recent sessions with a first-message snippet

Recommender: centroid of the *stored* embeddings of the user's saved assets
(S3 Vectors GetVectors), queried back against content_type=asset excluding what's
already saved. With no activity it falls back to the most-tagged assets. No Titan
call needed — it reuses embeddings the ReEmbed pipeline already produced.
"""

from __future__ import annotations

import json
from typing import Any

from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

from agents.lib import models as lib_models

from .agent_03_asset_library import AssetLibraryAgent, AssetSummary, _slug
from .base import ModuleAgent

AGENT_ID = "AGENT-16"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}


class ChatSession(BaseModel):
    session_id: str
    snippet: str = ""
    updated_at: str = ""
    message_count: int = 0


class DashboardSummary(BaseModel):
    saved_assets: list[AssetSummary] = Field(default_factory=list)
    recent_chats: list[ChatSession] = Field(default_factory=list)
    # Placeholders until Module 18 (engagements) / Module 20 (learning) exist.
    active_engagements: list[dict] = Field(default_factory=list)
    learning_progress: list[dict] = Field(default_factory=list)
    recommendations: list[AssetSummary] = Field(default_factory=list)
    last_session_id: str | None = None


def _read_json(s3: Any, bucket: str, key: str, default: dict) -> dict:
    try:
        raw = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in _NOT_FOUND:
            return dict(default)
        raise
    except (KeyError, FileNotFoundError):
        return dict(default)
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return dict(default)


def _centroid(vectors: list[list[float]]) -> list[float]:
    n = len(vectors)
    dim = len(vectors[0])
    out = [0.0] * dim
    for v in vectors:
        for i in range(dim):
            out[i] += v[i]
    return [x / n for x in out]


class DashboardAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.HAIKU_4_5

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        sessions_bucket: str | None = None,
        vector_bucket: str = "aicoe-content-vectors",
        index_name: str = "aicoe-content",
        region: str = lib_models.REGION,
        s3: Any = None,
        s3vectors: Any = None,
        bedrock: Any = None,
        asset_agent: AssetLibraryAgent | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        import os

        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.vector_bucket = vector_bucket
        self.index_name = index_name
        self.region = region
        self._s3 = s3
        self._s3vectors = s3vectors
        # Reuse AGENT-03 for all asset reads/search (composition, not duplication).
        self.assets = asset_agent or AssetLibraryAgent(
            vault_bucket=vault_bucket,
            sessions_bucket=self.sessions_bucket,
            vector_bucket=vector_bucket,
            index_name=index_name,
            region=region,
            s3=s3,
            s3vectors=s3vectors,
            bedrock=bedrock,
        )

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    @property
    def s3vectors(self) -> Any:
        if self._s3vectors is None:
            import boto3

            self._s3vectors = boto3.client("s3vectors", region_name=self.region)
        return self._s3vectors

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = args.get("display_name")
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        op = args.get("op")
        if op == "read_profile":
            return self.run_tool("read_profile", lambda _u: self._read_profile_op(display_name))
        if op == "recommend":
            top_k = int(args.get("top_k", 5))
            return self.run_tool("recommend", lambda _u: self._recommend_op(display_name, top_k))
        if op == "list_recent_chats":
            limit = int(args.get("limit", 5))
            return self.run_tool(
                "list_recent_chats", lambda _u: self._recent_chats_op(display_name, limit)
            )
        return self.run_tool("summary", lambda _u: self._summary(display_name))

    # --- profile / assets --------------------------------------------------
    def _profile(self, display_name: str) -> dict:
        default = {"display_name": display_name, "saved": [], "ratings": {}, "flags": []}
        key = f"users/{_slug(display_name)}.json"
        return _read_json(self.s3, self.sessions_bucket, key, default)

    def _all_summaries(self) -> dict[str, AssetSummary]:
        result = self.assets.handle({"op": "list_assets", "limit": 1000})
        return {a["id"]: AssetSummary(**a) for a in result.get("assets", [])}

    def _read_profile_op(self, display_name: str) -> dict:
        return {"status": "ok", "profile": self._profile(display_name)}

    # --- recommender -------------------------------------------------------
    def _saved_embeddings(self, file_paths: list[str]) -> list[list[float]]:
        if not file_paths:
            return []
        keys = [f"{p}#0" for p in file_paths]
        try:
            resp = self.s3vectors.get_vectors(
                vectorBucketName=self.vector_bucket,
                indexName=self.index_name,
                keys=keys,
                returnData=True,
            )
        except Exception:  # noqa: BLE001 — recommender is best-effort
            return []
        out: list[list[float]] = []
        for v in resp.get("vectors", []):
            data = v.get("data", {}).get("float32")
            if data:
                out.append(data)
        return out

    def _recommend(self, display_name: str, top_k: int) -> list[AssetSummary]:
        summaries = self._all_summaries()
        saved_ids = [i for i in self._profile(display_name).get("saved", []) if i in summaries]

        # Cold start: no saved activity -> most-tagged assets as a sensible default.
        if not saved_ids:
            ranked = sorted(summaries.values(), key=lambda s: (-len(s.tags), s.title))
            return ranked[:top_k]

        saved_paths = {summaries[i].file_path for i in saved_ids}
        embeddings = self._saved_embeddings(sorted(saved_paths))
        if not embeddings:
            ranked = sorted(summaries.values(), key=lambda s: (-len(s.tags), s.title))
            return [s for s in ranked if s.file_path not in saved_paths][:top_k]

        resp = self.s3vectors.query_vectors(
            vectorBucketName=self.vector_bucket,
            indexName=self.index_name,
            queryVector={"float32": _centroid(embeddings)},
            topK=top_k + len(saved_paths) + 5,  # over-fetch to absorb exclusions
            returnMetadata=True,
        )
        by_path = {s.file_path: s for s in summaries.values()}
        recs: list[AssetSummary] = []
        seen: set[str] = set()
        for v in resp.get("vectors", []):
            meta = v.get("metadata", {}) or {}
            if meta.get("content_type") != "assets":
                continue
            path = meta.get("file_path") or v.get("key", "").split("#", 1)[0]
            if path in saved_paths or path in seen or path not in by_path:
                continue
            seen.add(path)
            recs.append(by_path[path])
            if len(recs) >= top_k:
                break
        return recs

    def _recommend_op(self, display_name: str, top_k: int) -> dict:
        recs = self._recommend(display_name, top_k)
        return {"status": "ok", "assets": [s.model_dump() for s in recs]}

    # --- recent chats ------------------------------------------------------
    def _recent_chats(self, display_name: str, limit: int) -> list[ChatSession]:
        prefix = f"sessions/{_slug(display_name)}/"
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.sessions_bucket, "Prefix": prefix}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            keys += [o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(".json")]
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")

        chats: list[ChatSession] = []
        for key in keys:
            doc = _read_json(self.s3, self.sessions_bucket, key, {})
            if not doc:
                continue
            turns = doc.get("turns", [])
            snippet = (turns[0].get("user_message", "") if turns else "")[:140]
            sid = str(doc.get("session_id") or key.rsplit("/", 1)[-1].removesuffix(".json"))
            chats.append(
                ChatSession(
                    session_id=sid,
                    snippet=snippet,
                    updated_at=str(doc.get("updated_at", "")),
                    message_count=len(turns),
                )
            )
        chats.sort(key=lambda c: c.updated_at, reverse=True)
        return chats[:limit]

    def _recent_chats_op(self, display_name: str, limit: int) -> dict:
        chats = self._recent_chats(display_name, limit)
        return {"status": "ok", "chats": [c.model_dump() for c in chats]}

    # --- full summary ------------------------------------------------------
    def _summary(self, display_name: str) -> dict:
        summaries = self._all_summaries()
        saved_ids = [i for i in self._profile(display_name).get("saved", []) if i in summaries]
        recent = self._recent_chats(display_name, 5)
        summary = DashboardSummary(
            saved_assets=[summaries[i] for i in saved_ids][:10],
            recent_chats=recent,
            active_engagements=[],
            learning_progress=[],
            recommendations=self._recommend(display_name, 5),
            last_session_id=recent[0].session_id if recent else None,
        )
        return {"status": "ok", **summary.model_dump()}
