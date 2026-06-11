"""AGENT-27 — Agentic Skills & Plugin Exchange (Module 28), Haiku 4.5 tier.

A **read-only catalog**, structurally identical to the Asset Library (AGENT-03): the
operations are mechanical S3 reads, and ``search`` embeds the query with Titan and
queries S3 Vectors. No chat-LLM loop. Entries are reusable agentic-dev artifacts —
Claude Code skills / slash-commands / MCP servers, Claude Cowork setups, GitHub Copilot
configs, Kiro configs, and cross-tool prompt-packs — each with install steps.

Every entry carries ``content_type: exchange`` (and lives under ``exchange/``), so the
ReEmbed pipeline stamps that on its vectors and ``search`` filters on it — the exchange
never pollutes asset/content search, and vice versa.

Operations (dispatched from :meth:`handle` on ``op``):
  - ``list``   — enumerate + filter by tool/category (default)
  - ``get``    — one entry's body + install + frontmatter
  - ``search`` — semantic search over content_type=exchange

Publish/contribute (a user write path) is out of scope; when it lands it becomes a
runtime-vault-writer and must follow ``vault/decisions/runtime-vault-writers.md``.
"""

from __future__ import annotations

import json
import os
from typing import Any

from pydantic import BaseModel, Field

from agents.lib import models as lib_models

from .agent_03_asset_library import _split_frontmatter
from .base import ModuleAgent

AGENT_ID = "AGENT-27"
EXCHANGE_PREFIX = "exchange/"
EXCHANGE_CONTENT_TYPE = "exchange"


class ExchangeEntry(BaseModel):
    id: str
    name: str
    tool: str
    category: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    install: str = ""
    source_url: str = ""
    body_markdown: str = ""  # populated on get only
    file_path: str = ""


def _summary_from_frontmatter(fm: dict, key: str) -> ExchangeEntry:
    return ExchangeEntry(
        id=str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md")),
        name=str(fm.get("name", "")),
        tool=str(fm.get("tool", "")),
        category=str(fm.get("category", "")),
        summary=str(fm.get("summary", "")),
        tags=[str(t) for t in (fm.get("tags") or [])],
        install=str(fm.get("install", "")),
        source_url=str(fm.get("source_url", "")),
        file_path=key,
    )


class ExchangeAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.HAIKU_4_5

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
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
        # Liberal aliasing: ``id`` is a common alias for ``entry_id``. Op inferred for
        # reads when absent (entry_id -> get, query -> search, else list).
        if "entry_id" not in args and args.get("id"):
            args = {**args, "entry_id": args["id"]}
        op = args.get("op")
        if op == "get" or (op is None and args.get("entry_id")):
            return self.run_tool("get_entry", lambda _u: self._get(args))
        if op == "search" or (op is None and args.get("query")):
            return self.run_tool("search_exchange", lambda _u: self._search(args))
        return self.run_tool("list_exchange", lambda _u: self._list(args))

    # --- S3 helpers --------------------------------------------------------
    def _list_keys(self) -> list[str]:
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": EXCHANGE_PREFIX}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            keys.extend(o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(".md"))
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
        return keys

    def _read(self, key: str) -> str:
        return self.s3.get_object(Bucket=self.vault_bucket, Key=key)["Body"].read().decode("utf-8")

    # --- operations --------------------------------------------------------
    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        tool = (args.get("tool") or "").strip().lower()
        category = (args.get("category") or "").strip().lower()
        query = (args.get("query") or "").strip().lower()

        entries: list[ExchangeEntry] = []
        for key in self._list_keys():
            fm, _ = _split_frontmatter(self._read(key))
            e = _summary_from_frontmatter(fm, key)
            if tool and e.tool.lower() != tool:
                continue
            if category and e.category.lower() != category:
                continue
            if query:
                hay = f"{e.name} {e.summary} {' '.join(e.tags)}".lower()
                if query not in hay:
                    continue
            entries.append(e)

        entries.sort(key=lambda e: (e.tool, e.category, e.name))
        return {"status": "ok", "entries": [e.model_dump() for e in entries]}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        entry_id = args.get("entry_id")
        if not entry_id:
            return {"status": "error", "message": "entry_id is required."}
        keys = self._list_keys()
        basename = f"/{entry_id}.md"
        candidates = [k for k in keys if k.endswith(basename)] or keys
        for key in candidates:
            fm, body = _split_frontmatter(self._read(key))
            if str(fm.get("id")) == str(entry_id) or key.endswith(basename):
                entry = _summary_from_frontmatter(fm, key)
                entry.body_markdown = body.strip()
                return {"status": "ok", "entry": entry.model_dump(), "frontmatter": fm}
        return {"status": "not_found", "entry_id": entry_id, "message": "No such entry."}

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
            topK=max(top_k * 3, top_k),  # over-fetch; filter to exchange, dedup by file
            returnMetadata=True,
        )
        seen: set[str] = set()
        entries: list[ExchangeEntry] = []
        for v in resp.get("vectors", []):
            meta = v.get("metadata", {}) or {}
            if meta.get("content_type") != EXCHANGE_CONTENT_TYPE:
                continue
            key = meta.get("file_path") or v.get("key", "").split("#", 1)[0]
            if not key or key in seen:
                continue
            seen.add(key)
            fm, _ = _split_frontmatter(self._read(key))
            entries.append(_summary_from_frontmatter(fm, key))
            if len(entries) >= top_k:
                break
        return {"status": "ok", "entries": [e.model_dump() for e in entries]}
