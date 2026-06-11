"""AGENT-18 — Decision Log (Module 19), Haiku 4.5 tier.

Lets a consultant log engagement decisions (decision, context, alternatives,
rationale, outcome, tags), search across all logged decisions, and — when viewing
one — see similar past decisions via vector similarity.

Decisions are **runtime-generated vault artifacts**: each is written to
``vault/decisions/{display_name}/{decision_id}.md`` and tagged ``generated: true``
via the shared :func:`~agents.lambdas.modules.vault_export.export_frontmatter` helper
(see ``vault/decisions/runtime-vault-writers.md``). That flag is what keeps user
decision logs out of curated chat KB search **and** is the discriminator that lets
``get_similar`` tell them apart from the curated architecture-decision docs that live
in the *same* ``decisions/`` folder — ``get_similar`` matches vectors with
``content_type == "decisions"`` AND ``generated`` truthy.

Operations (on ``op``):
  - ``write``   — persist a decision (Haiku suggests tags) → record (default when a
    ``decision`` is supplied)
  - ``search``  — keyword / tag / industry filter across logged decisions (default)
  - ``get``     — one decision by id
  - ``similar`` — vector-similar logged decisions to a given one
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .agent_03_asset_library import _slug, _split_frontmatter
from .base import ModuleAgent
from .vault_export import export_frontmatter

AGENT_ID = "AGENT-18"
DECISIONS_PREFIX = "decisions/"
DECISIONS_ROUTE = "/modules/decisions"
# Folder-derived content_type the ReEmbed pipeline stamps on decisions/ vectors.
DECISION_DIR_TYPE = "decisions"

TAG_SYSTEM = """You suggest 3-6 short, lowercase, hyphenated topic tags for an \
engagement decision, to make it findable later. Return ONLY a JSON array of strings \
(e.g. ["vector-db", "healthcare", "rag"]). No prose. Prefer technology, domain, and \
decision-type tags grounded in the text; do not invent specifics not present."""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _norm_tags(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for v in values or []:
        t = _norm(v).lower().replace(" ", "-")
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


class DecisionsAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.HAIKU_4_5

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        region: str = lib_models.REGION,
        vector_bucket: str = "aicoe-content-vectors",
        index_name: str = "aicoe-content",
        embed_model: str = lib_models.TITAN_EMBED_V2,
        s3: Any = None,
        bedrock: Any = None,
        bedrock_client: BedrockClient | None = None,
        s3vectors: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.region = region
        self.vector_bucket = vector_bucket
        self.index_name = index_name
        self.embed_model = embed_model
        self._s3 = s3
        self._bedrock = bedrock
        self._s3vectors = s3vectors
        self.bedrock_client = bedrock_client or BedrockClient(client=bedrock)

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

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        if "decision_id" not in args and args.get("id"):
            args = {**args, "decision_id": args["id"]}
        op = args.get("op")
        if op == "write" or (op is None and args.get("decision")):
            return self.run_tool("write_decision", lambda _u: self._write(args))
        if op == "similar":
            return self.run_tool("get_similar", lambda _u: self._similar(args))
        if op == "get" or (op is None and args.get("decision_id")):
            return self.run_tool("get_decision", lambda _u: self._get(args))
        return self.run_tool("search_decisions", lambda _u: self._search(args))

    # --- vault I/O ---------------------------------------------------------
    def _read(self, key: str) -> str:
        return self.s3.get_object(Bucket=self.vault_bucket, Key=key)["Body"].read().decode("utf-8")

    def _all_decisions(self) -> list[tuple[dict, str]]:
        """(frontmatter, key) for every *logged* decision (generated artifacts only).

        Skips the curated architecture-decision docs that share ``decisions/`` — they
        carry no ``generated`` flag.
        """
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": DECISIONS_PREFIX}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            keys.extend(o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(".md"))
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")

        out: list[tuple[dict, str]] = []
        for key in keys:
            fm, _ = _split_frontmatter(self._read(key))
            if fm.get("generated"):  # logged decision, not a curated arch-doc
                out.append((fm, key))
        return out

    @staticmethod
    def _summary(fm: dict, key: str) -> dict[str, Any]:
        return {
            "decision_id": str(fm.get("decision_id") or key.rsplit("/", 1)[-1].removesuffix(".md")),
            "decision": str(fm.get("decision", "")),
            "tags": [str(t) for t in (fm.get("tags") or [])],
            "engagement_id": fm.get("engagement_id"),
            "outcome": fm.get("outcome"),
            "created_at": str(fm.get("created_at", "")),
            "file_path": key,
        }

    @staticmethod
    def _full(fm: dict, key: str) -> dict[str, Any]:
        return {
            **DecisionsAgent._summary(fm, key),
            "context": str(fm.get("context", "")),
            "alternatives": [str(a) for a in (fm.get("alternatives") or [])],
            "rationale": str(fm.get("rationale", "")),
            "updated_at": str(fm.get("updated_at", "")),
        }

    def _load(self, decision_id: str) -> tuple[dict, str] | None:
        for fm, key in self._all_decisions():
            if self._summary(fm, key)["decision_id"] == str(decision_id):
                return fm, key
        return None

    # --- operations --------------------------------------------------------
    def _write(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        decision = _norm(args.get("decision"))
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        if not decision:
            return {"status": "error", "message": "decision is required."}

        context = _norm(args.get("context"))
        alternatives = [_norm(a) for a in (args.get("alternatives") or []) if _norm(a)]
        rationale = _norm(args.get("rationale"))
        outcome = _norm(args.get("outcome")) or None
        engagement_id = _norm(args.get("engagement_id")) or None
        user_tags = _norm_tags(args.get("tags"))
        tags = _norm_tags([*user_tags, *self._suggest_tags(decision, context, rationale)])

        decision_id = "dec-" + uuid.uuid4().hex[:12]
        created_at = _now_iso()
        record = {
            "decision_id": decision_id,
            "decision": decision,
            "context": context,
            "alternatives": alternatives,
            "rationale": rationale,
            "outcome": outcome,
            "tags": tags,
            "engagement_id": engagement_id,
            "created_at": created_at,
            "updated_at": created_at,
        }
        key = f"{DECISIONS_PREFIX}{_slug(display_name)}/{decision_id}.md"
        self.s3.put_object(
            Bucket=self.vault_bucket,
            Key=key,
            Body=self._render(record).encode("utf-8"),
            ContentType="text/markdown",
        )
        return {"status": "ok", "decision": {**record, "file_path": key}, "vault_file_path": key}

    def _search(self, args: dict[str, Any]) -> dict[str, Any]:
        query = _norm(args.get("query")).lower()
        tags = set(_norm_tags(args.get("tags")))
        industry = _norm(args.get("industry")).lower()
        out: list[dict[str, Any]] = []
        for fm, key in self._all_decisions():
            full = self._full(fm, key)
            hay = " ".join(
                [full["decision"], full["context"], full["rationale"], " ".join(full["tags"])]
            ).lower()
            if query and query not in hay:
                continue
            if tags and not (tags & set(full["tags"])):
                continue
            if industry and industry not in hay:
                continue
            out.append(self._summary(fm, key))
        out.sort(key=lambda d: d["created_at"], reverse=True)
        return {"status": "ok", "decisions": out}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        decision_id = _norm(args.get("decision_id"))
        if not decision_id:
            return {"status": "error", "message": "decision_id is required."}
        loaded = self._load(decision_id)
        if loaded is None:
            return {"status": "not_found", "decision_id": decision_id}
        fm, key = loaded
        return {"status": "ok", "decision": self._full(fm, key)}

    def _similar(self, args: dict[str, Any]) -> dict[str, Any]:
        decision_id = _norm(args.get("decision_id"))
        if not decision_id:
            return {"status": "error", "message": "decision_id is required."}
        loaded = self._load(decision_id)
        if loaded is None:
            return {"status": "not_found", "decision_id": decision_id}
        fm, key = loaded
        top_k = int(args.get("top_k", 5))
        full = self._full(fm, key)
        query_text = " ".join(
            [full["decision"], full["context"], full["rationale"], " ".join(full["tags"])]
        ).strip()

        resp = self.s3vectors.query_vectors(
            vectorBucketName=self.vector_bucket,
            indexName=self.index_name,
            queryVector={"float32": self._embed(query_text)},
            topK=max(top_k * 4, top_k),  # over-fetch; filter to logged decisions, dedup
            returnMetadata=True,
        )
        seen: set[str] = set()
        similar: list[dict[str, Any]] = []
        for v in resp.get("vectors", []):
            meta = v.get("metadata", {}) or {}
            # Only other LOGGED decisions: same folder type + generated flag, never self.
            if meta.get("content_type") != DECISION_DIR_TYPE or not meta.get("generated"):
                continue
            other_key = meta.get("file_path") or v.get("key", "").split("#", 1)[0]
            if not other_key or other_key == key or other_key in seen:
                continue
            seen.add(other_key)
            try:
                ofm, _ = _split_frontmatter(self._read(other_key))
            except Exception:  # noqa: BLE001 — skip an unreadable hit
                continue
            similar.append(self._summary(ofm, other_key))
            if len(similar) >= top_k:
                break
        return {"status": "ok", "decision_id": decision_id, "similar": similar}

    # --- LLM tag suggestion (the one model call; degrades gracefully) ------
    def _suggest_tags(self, decision: str, context: str, rationale: str) -> list[str]:
        user_text = f"Decision: {decision}\nContext: {context}\nRationale: {rationale}"
        try:
            with instrumented(
                agent_id=self.agent_id,
                tool_name="bedrock:converse",
                model_id=self.model_id,
                metrics_client=self.metrics_client,
            ) as usage:
                resp = self.bedrock_client.converse(
                    model_id=self.model_id,
                    messages=[{"role": "user", "content": [{"text": user_text}]}],
                    system=TAG_SYSTEM,
                    max_tokens=120,
                    usage=usage,
                )
            text = _extract_text(resp.get("output", {}).get("message", {}))
            return _parse_tag_list(text)
        except Exception:  # noqa: BLE001 — tags are a convenience; user tags still apply
            return []

    def _embed(self, text: str) -> list[float]:
        resp = self.bedrock.invoke_model(
            modelId=self.embed_model,
            body=json.dumps(
                {"inputText": text, "dimensions": lib_models.EMBED_DIMENSIONS, "normalize": True}
            ),
        )
        return json.loads(resp["body"].read())["embedding"]

    # --- markdown rendering ------------------------------------------------
    def _render(self, r: dict[str, Any]) -> str:
        frontmatter = export_frontmatter(
            "decision",
            {
                "decision_id": r["decision_id"],
                "decision": r["decision"],
                "context": r["context"],
                "alternatives": r["alternatives"],
                "rationale": r["rationale"],
                "outcome": r["outcome"],
                "tags": r["tags"],
                "engagement_id": r["engagement_id"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            },
        )
        alts = "\n".join(f"- {a}" for a in r["alternatives"]) or "- (none)"
        body = (
            f"{frontmatter}\n"
            f"# Decision — {r['decision']}\n\n"
            f"## Context\n\n{r['context'] or '(none)'}\n\n"
            f"## Alternatives considered\n\n{alts}\n\n"
            f"## Rationale\n\n{r['rationale'] or '(none)'}\n\n"
            f"## Outcome\n\n{r['outcome'] or '(pending)'}\n"
        )
        return body


def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()


def _parse_tag_list(text: str) -> list[str]:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t).strip()
    start, end = t.find("["), t.rfind("]")
    if start != -1 and end > start:
        t = t[start : end + 1]
    try:
        data = json.loads(t)
    except (json.JSONDecodeError, ValueError):
        return []
    return [str(x) for x in data if str(x).strip()] if isinstance(data, list) else []
