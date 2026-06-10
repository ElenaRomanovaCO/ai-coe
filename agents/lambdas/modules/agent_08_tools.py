"""AGENT-08 — Skills & Tools Repository (Module 7), Haiku 4.5 tier.

Read-only Layer 2 agent over the curated tools in ``vault/tools/`` — the same shape
as AGENT-03 (Asset Library): mechanical S3 reads for browse/detail, and a Titan +
S3 Vectors pass for context recommendations (no chat-LLM loop needed for a directory
module). Three operations, dispatched from :meth:`handle` on ``op``:

  - ``list_tools``                   — enumerate + filter the tool corpus
  - ``get_tool``                     — one tool's rendered body + frontmatter
  - ``recommend_tools_for_context``  — semantic search (content_type=tools) + filters

Ratings/save/flag are intentionally out of scope (the task defers tool ratings to the
Asset Library metadata-sidecar pattern), so this agent is purely read-only. All AWS
clients are injectable so the agent is unit-testable without AWS.
"""

from __future__ import annotations

import json
import os
from typing import Any

from pydantic import BaseModel, Field

from agents.lib import models as lib_models

from .agent_03_asset_library import _split_frontmatter
from .base import ModuleAgent

AGENT_ID = "AGENT-08"
TOOLS_PREFIX = "tools/"
TOOLS_ROUTE = "/modules/tools-repo"


class ToolSummary(BaseModel):
    id: str
    name: str
    category: str
    stack: list[str] = Field(default_factory=list)
    ai_stage_fit: list[int] = Field(default_factory=list)
    cost_model: str = ""
    tags: list[str] = Field(default_factory=list)
    file_path: str


class ToolDetail(BaseModel):
    summary: ToolSummary
    body_markdown: str
    frontmatter: dict


def _as_int_list(value: Any) -> list[int]:
    out: list[int] = []
    for v in value or []:
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            continue
    return out


def _summary_from_frontmatter(fm: dict, key: str) -> ToolSummary:
    return ToolSummary(
        id=str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md")),
        name=str(fm.get("name", "")),
        category=str(fm.get("category", "")),
        stack=[str(s) for s in (fm.get("stack") or [])],
        ai_stage_fit=_as_int_list(fm.get("ai_stage_fit")),
        cost_model=str(fm.get("cost_model", "")),
        tags=[str(t) for t in (fm.get("tags") or [])],
        file_path=key,
    )


class ToolsRepoAgent(ModuleAgent):
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
        # Be liberal: ``id`` aliases ``tool_id``. Op is inferred for reads when absent
        # (tool_id -> get, query -> recommend, else list).
        if "tool_id" not in args and args.get("id"):
            args = {**args, "tool_id": args["id"]}
        op = args.get("op")

        if op == "get_tool" or (op is None and args.get("tool_id")):
            return self.run_tool("get_tool", lambda _u: self._get_tool(args))
        if op in ("recommend", "recommend_tools_for_context") or (
            op is None and args.get("query")
        ):
            return self.run_tool("recommend_tools_for_context", lambda _u: self._recommend(args))
        return self.run_tool("list_tools", lambda _u: self._list_tools(args))

    # --- S3 helpers --------------------------------------------------------
    def _list_keys(self) -> list[str]:
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": TOOLS_PREFIX}
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
    def _list_tools(self, args: dict[str, Any]) -> dict[str, Any]:
        category = (args.get("category") or "").strip().lower()
        cost = (args.get("cost") or args.get("cost_model") or "").strip().lower()
        stack = (args.get("stack") or "").strip().lower()
        stage = args.get("stage")
        stage_int = int(stage) if stage is not None and str(stage).strip() != "" else None
        want_tags = {str(t).lower() for t in (args.get("tags") or [])}
        query = (args.get("query") or "").strip().lower()
        limit = int(args.get("limit", 50))

        summaries: list[ToolSummary] = []
        for key in self._list_keys():
            fm, _ = _split_frontmatter(self._read(key))
            s = _summary_from_frontmatter(fm, key)
            if category and s.category.lower() != category:
                continue
            if cost and s.cost_model.lower() != cost:
                continue
            if stack and stack not in {x.lower() for x in s.stack}:
                continue
            if stage_int is not None and stage_int not in s.ai_stage_fit:
                continue
            if want_tags and not want_tags.issubset({t.lower() for t in s.tags}):
                continue
            if query:
                haystack = f"{s.name} {s.category} {' '.join(s.stack)} {' '.join(s.tags)}".lower()
                if query not in haystack:
                    continue
            summaries.append(s)

        summaries.sort(key=lambda x: (x.category, x.name))
        return {"status": "ok", "tools": [s.model_dump() for s in summaries[:limit]]}

    def _get_tool(self, args: dict[str, Any]) -> dict[str, Any]:
        tool_id = args.get("tool_id")
        if not tool_id:
            return {"status": "error", "message": "tool_id is required."}

        keys = self._list_keys()
        basename = f"/{tool_id}.md"
        candidates = [k for k in keys if k.endswith(basename)] or keys
        for key in candidates:
            fm, body = _split_frontmatter(self._read(key))
            if str(fm.get("id")) == str(tool_id) or key.endswith(basename):
                detail = ToolDetail(
                    summary=_summary_from_frontmatter(fm, key),
                    body_markdown=body.strip(),
                    frontmatter=fm,
                )
                return {"status": "ok", "tool": detail.model_dump()}
        return {"status": "not_found", "tool_id": tool_id, "message": "No such tool."}

    def _embed(self, text: str) -> list[float]:
        resp = self.bedrock.invoke_model(
            modelId=self.embed_model,
            body=json.dumps(
                {"inputText": text, "dimensions": lib_models.EMBED_DIMENSIONS, "normalize": True}
            ),
        )
        return json.loads(resp["body"].read())["embedding"]

    def _recommend(self, args: dict[str, Any]) -> dict[str, Any]:
        query = (args.get("query") or "").strip()
        if not query:
            return {"status": "error", "message": "query is required."}
        top_k = int(args.get("top_k", 10))
        # Optional context filters applied on top of the semantic results.
        category = (args.get("category") or "").strip().lower()
        cost = (args.get("cost") or args.get("cost_model") or "").strip().lower()
        stage = args.get("stage")
        stage_int = int(stage) if stage is not None and str(stage).strip() != "" else None

        resp = self.s3vectors.query_vectors(
            vectorBucketName=self.vector_bucket,
            indexName=self.index_name,
            queryVector={"float32": self._embed(query)},
            topK=max(top_k * 3, top_k),  # over-fetch; filter to tools, dedup by file
            returnMetadata=True,
        )

        seen: set[str] = set()
        summaries: list[ToolSummary] = []
        for v in resp.get("vectors", []):
            meta = v.get("metadata", {}) or {}
            if meta.get("content_type") != "tools":
                continue
            key = meta.get("file_path") or v.get("key", "").split("#", 1)[0]
            if not key or key in seen:
                continue
            seen.add(key)
            fm, _ = _split_frontmatter(self._read(key))
            s = _summary_from_frontmatter(fm, key)
            if category and s.category.lower() != category:
                continue
            if cost and s.cost_model.lower() != cost:
                continue
            if stage_int is not None and stage_int not in s.ai_stage_fit:
                continue
            summaries.append(s)
            if len(summaries) >= top_k:
                break
        return {"status": "ok", "tools": [s.model_dump() for s in summaries]}
