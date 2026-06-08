"""AGENT-03 — Asset Library (Module 2), Haiku 4.5 tier.

Read-mostly Layer 2 agent. Operations are mechanical S3 reads; ``search`` embeds
the query with Titan and queries S3 Vectors (no chat-LLM loop needed for a
retrieval module). Three operations, dispatched from :meth:`handle` on ``op``:

  - ``list_assets``  — enumerate + filter the vault's assets
  - ``get_asset``    — one asset's rendered body + frontmatter
  - ``search``       — semantic search over content_type=asset

All AWS clients are injectable so the agent is unit-testable without AWS.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import yaml
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

from agents.lib import models as lib_models

from .base import ModuleAgent

AGENT_ID = "AGENT-03"
ASSET_PREFIX = "assets/"
META_PREFIX = "assets/_metadata/"
_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_SLUG_UNSAFE = re.compile(r"[^a-zA-Z0-9._-]+")
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}


def _slug(display_name: str) -> str:
    s = _SLUG_UNSAFE.sub("-", (display_name or "").strip()).strip("-").lower()
    return s or "anon"


# --- wire models -----------------------------------------------------------
class AssetSummary(BaseModel):
    id: str
    title: str
    type: str
    industry: str
    ai_stage: int
    tags: list[str] = Field(default_factory=list)
    file_path: str
    updated_at: str = ""


class AssetDetail(BaseModel):
    summary: AssetSummary
    body_markdown: str
    frontmatter: dict


def _split_frontmatter(text: str) -> tuple[dict, str]:
    m = _FRONTMATTER.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    return (fm if isinstance(fm, dict) else {}), text[m.end() :]


def _summary_from_frontmatter(fm: dict, key: str) -> AssetSummary:
    return AssetSummary(
        id=str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md")),
        title=str(fm.get("title", "")),
        type=str(fm.get("type", "")),
        industry=str(fm.get("industry", "")),
        ai_stage=int(fm.get("ai_stage", 0) or 0),
        tags=[str(t) for t in (fm.get("tags") or [])],
        file_path=key,
        updated_at=str(fm.get("updated_at", "")),
    )


class AssetLibraryAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.HAIKU_4_5

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        sessions_bucket: str | None = None,
        vector_bucket: str = "aicoe-content-vectors",
        index_name: str = "aicoe-content",
        embed_model: str = lib_models.TITAN_EMBED_V2,
        region: str = lib_models.REGION,
        s3: Any = None,
        s3vectors: Any = None,
        bedrock: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.vector_bucket = vector_bucket
        self.index_name = index_name
        self.embed_model = embed_model
        self.region = region
        self._s3 = s3
        self._s3vectors = s3vectors
        self._bedrock = bedrock

    # --- lazy clients ------------------------------------------------------
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

    @property
    def bedrock(self) -> Any:
        if self._bedrock is None:
            import boto3

            self._bedrock = boto3.client("bedrock-runtime", region_name=self.region)
        return self._bedrock

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        # The orchestrator builds ``args`` from the LLM, so be liberal in what we
        # accept: ``id`` is a common alias for ``asset_id``. Op is inferred for
        # reads when absent (asset_id -> get, query -> search, else browse). Writes
        # always require an explicit op (never inferred).
        if "asset_id" not in args and args.get("id"):
            args = {**args, "asset_id": args["id"]}
        op = args.get("op")

        writes = {
            "save_asset": self._save_asset,
            "rate_asset": self._rate_asset,
            "flag_asset": self._flag_asset,
        }
        if op in writes:
            return self.run_tool(op, lambda _u, _fn=writes[op]: _fn(args))

        if op == "get_asset" or (op is None and args.get("asset_id")):
            return self.run_tool("get_asset", lambda _u: self._get_asset(args))
        if op == "search" or (op is None and args.get("query")):
            return self.run_tool("search_vector_index", lambda _u: self._search(args))
        return self.run_tool("list_assets", lambda _u: self._list_assets(args))

    # --- JSON state helpers (user profiles + asset metadata sidecars) ------
    def _user_key(self, display_name: str) -> str:
        return f"users/{_slug(display_name)}.json"

    def _meta_key(self, asset_id: str) -> str:
        return f"{META_PREFIX}{asset_id}.json"

    def _read_json(self, bucket: str, key: str, default: dict) -> dict:
        try:
            raw = self.s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _NOT_FOUND:
                return dict(default)
            raise
        except (KeyError, FileNotFoundError):  # fake clients / missing key
            return dict(default)
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return dict(default)

    def _write_json(self, bucket: str, key: str, obj: dict) -> None:
        self.s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(obj, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    def _default_meta(self, asset_id: str) -> dict:
        return {
            "asset_id": asset_id,
            "rating_count": 0,
            "rating_sum": 0,
            "flag_count": 0,
            "saved_count": 0,
        }

    def _default_profile(self, display_name: str) -> dict:
        return {"display_name": display_name, "saved": [], "ratings": {}, "flags": []}

    @staticmethod
    def _aggregates(meta: dict) -> dict:
        count = int(meta.get("rating_count", 0))
        total = int(meta.get("rating_sum", 0))
        return {
            "average_rating": round(total / count, 2) if count else None,
            "rating_count": count,
            "flag_count": int(meta.get("flag_count", 0)),
            "saved_count": int(meta.get("saved_count", 0)),
        }

    # --- S3 helpers --------------------------------------------------------
    def _list_keys(self) -> list[str]:
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": ASSET_PREFIX}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            for obj in resp.get("Contents", []):
                key = obj["Key"]
                # Skip the metadata sidecars and non-markdown.
                if key.endswith(".md") and "/_metadata/" not in key:
                    keys.append(key)
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
        return keys

    def _read(self, key: str) -> str:
        return self.s3.get_object(Bucket=self.vault_bucket, Key=key)["Body"].read().decode("utf-8")

    # --- operations --------------------------------------------------------
    def _list_assets(self, args: dict[str, Any]) -> dict[str, Any]:
        industry = args.get("industry")
        ai_stage = args.get("ai_stage")
        asset_type = args.get("asset_type")
        want_tags = {str(t).lower() for t in (args.get("tags") or [])}
        query = (args.get("query") or "").strip().lower()
        limit = int(args.get("limit", 50))

        summaries: list[AssetSummary] = []
        for key in self._list_keys():
            fm, _ = _split_frontmatter(self._read(key))
            s = _summary_from_frontmatter(fm, key)
            if industry and s.industry != industry:
                continue
            if ai_stage is not None and s.ai_stage != int(ai_stage):
                continue
            if asset_type and s.type != asset_type:
                continue
            if want_tags and not want_tags.issubset({t.lower() for t in s.tags}):
                continue
            if query:
                haystack = f"{s.title} {s.type} {' '.join(s.tags)}".lower()
                if query not in haystack:
                    continue
            summaries.append(s)

        summaries.sort(key=lambda x: (x.industry, x.ai_stage, x.title))
        return {"status": "ok", "assets": [s.model_dump() for s in summaries[:limit]]}

    def _get_asset(self, args: dict[str, Any]) -> dict[str, Any]:
        asset_id = args.get("asset_id")
        if not asset_id:
            return {"status": "error", "message": "asset_id is required."}

        keys = self._list_keys()
        # Fast path: slug == id convention (basename match), then verify.
        basename = f"/{asset_id}.md"
        candidates = [k for k in keys if k.endswith(basename)] or keys
        for key in candidates:
            fm, body = _split_frontmatter(self._read(key))
            if str(fm.get("id")) == str(asset_id) or key.endswith(basename):
                detail = AssetDetail(
                    summary=_summary_from_frontmatter(fm, key),
                    body_markdown=body.strip(),
                    frontmatter=fm,
                )
                resolved_id = detail.summary.id
                meta = self._read_json(
                    self.vault_bucket, self._meta_key(resolved_id), self._default_meta(resolved_id)
                )
                out: dict[str, Any] = {
                    "status": "ok",
                    "asset": detail.model_dump(),
                    "aggregates": self._aggregates(meta),
                }
                display_name = args.get("display_name")
                if display_name:
                    profile = self._read_json(
                        self.sessions_bucket,
                        self._user_key(display_name),
                        self._default_profile(display_name),
                    )
                    out["user"] = {
                        "saved": resolved_id in profile.get("saved", []),
                        "rating": profile.get("ratings", {}).get(resolved_id),
                        "flagged": resolved_id in profile.get("flags", []),
                    }
                return out
        return {"status": "not_found", "asset_id": asset_id, "message": "No such asset."}

    # --- write operations (read-modify-write; demo-grade, no locking) ------
    def _require(self, args: dict[str, Any], *keys: str) -> str | None:
        for k in keys:
            if not args.get(k):
                return f"{k} is required."
        return None

    def _save_asset(self, args: dict[str, Any]) -> dict[str, Any]:
        err = self._require(args, "asset_id", "display_name")
        if err:
            return {"status": "error", "message": err}
        asset_id = args["asset_id"]
        want_saved = bool(args.get("saved", True))

        profile = self._read_json(
            self.sessions_bucket,
            self._user_key(args["display_name"]),
            self._default_profile(args["display_name"]),
        )
        saved = set(profile.get("saved", []))
        meta_key = self._meta_key(asset_id)
        meta = self._read_json(self.vault_bucket, meta_key, self._default_meta(asset_id))

        changed = False
        if want_saved and asset_id not in saved:
            saved.add(asset_id)
            meta["saved_count"] = int(meta.get("saved_count", 0)) + 1
            changed = True
        elif not want_saved and asset_id in saved:
            saved.discard(asset_id)
            meta["saved_count"] = max(0, int(meta.get("saved_count", 0)) - 1)
            changed = True

        if changed:
            profile["saved"] = sorted(saved)
            self._write_json(self.sessions_bucket, self._user_key(args["display_name"]), profile)
            self._write_json(self.vault_bucket, meta_key, meta)
        return {"status": "ok", "asset_id": asset_id, "saved": want_saved, **self._aggregates(meta)}

    def _rate_asset(self, args: dict[str, Any]) -> dict[str, Any]:
        err = self._require(args, "asset_id", "display_name")
        if err:
            return {"status": "error", "message": err}
        try:
            rating = int(args["rating"])
        except (KeyError, TypeError, ValueError):
            return {"status": "error", "message": "rating (1-5) is required."}
        if not 1 <= rating <= 5:
            return {"status": "error", "message": "rating must be between 1 and 5."}
        asset_id = args["asset_id"]

        profile = self._read_json(
            self.sessions_bucket,
            self._user_key(args["display_name"]),
            self._default_profile(args["display_name"]),
        )
        meta_key = self._meta_key(asset_id)
        meta = self._read_json(self.vault_bucket, meta_key, self._default_meta(asset_id))

        ratings = profile.get("ratings", {})
        prev = ratings.get(asset_id)
        if prev is None:
            meta["rating_count"] = int(meta.get("rating_count", 0)) + 1
            meta["rating_sum"] = int(meta.get("rating_sum", 0)) + rating
        else:
            meta["rating_sum"] = int(meta.get("rating_sum", 0)) + (rating - int(prev))
        ratings[asset_id] = rating
        profile["ratings"] = ratings

        self._write_json(self.sessions_bucket, self._user_key(args["display_name"]), profile)
        self._write_json(self.vault_bucket, meta_key, meta)
        return {"status": "ok", "asset_id": asset_id, "rating": rating, **self._aggregates(meta)}

    def _flag_asset(self, args: dict[str, Any]) -> dict[str, Any]:
        err = self._require(args, "asset_id", "display_name")
        if err:
            return {"status": "error", "message": err}
        asset_id = args["asset_id"]

        profile = self._read_json(
            self.sessions_bucket,
            self._user_key(args["display_name"]),
            self._default_profile(args["display_name"]),
        )
        meta_key = self._meta_key(asset_id)
        meta = self._read_json(self.vault_bucket, meta_key, self._default_meta(asset_id))

        flags = set(profile.get("flags", []))
        if asset_id not in flags:  # one flag per user (idempotent)
            flags.add(asset_id)
            meta["flag_count"] = int(meta.get("flag_count", 0)) + 1
            profile["flags"] = sorted(flags)
            self._write_json(self.sessions_bucket, self._user_key(args["display_name"]), profile)
            self._write_json(self.vault_bucket, meta_key, meta)
        return {"status": "ok", "asset_id": asset_id, "flagged": True, **self._aggregates(meta)}

    def _embed(self, text: str) -> list[float]:
        resp = self.bedrock.invoke_model(
            modelId=self.embed_model,
            body=json.dumps(
                {"inputText": text, "dimensions": lib_models.EMBED_DIMENSIONS, "normalize": True}
            ),
        )
        return json.loads(resp["body"].read())["embedding"]

    def _search(self, args: dict[str, Any]) -> dict[str, Any]:
        query = (args.get("query") or "").strip()
        if not query:
            return {"status": "error", "message": "query is required."}
        top_k = int(args.get("top_k", 10))

        resp = self.s3vectors.query_vectors(
            vectorBucketName=self.vector_bucket,
            indexName=self.index_name,
            queryVector={"float32": self._embed(query)},
            topK=max(top_k * 3, top_k),  # over-fetch; filter to assets, dedup by file
            returnMetadata=True,
        )

        seen: set[str] = set()
        summaries: list[AssetSummary] = []
        for v in resp.get("vectors", []):
            meta = v.get("metadata", {}) or {}
            if meta.get("content_type") != "assets":
                continue
            key = meta.get("file_path") or v.get("key", "").split("#", 1)[0]
            if not key or key in seen:
                continue
            seen.add(key)
            fm, _ = _split_frontmatter(self._read(key))
            summaries.append(_summary_from_frontmatter(fm, key))
            if len(summaries) >= top_k:
                break
        return {"status": "ok", "assets": [s.model_dump() for s in summaries]}
