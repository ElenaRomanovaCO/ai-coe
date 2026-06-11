"""AGENT-17 — AI Project Health Monitor (Module 18), Sonnet 4.6 tier.

Tracks active AI engagements: a consultant registers an engagement, posts free-text
updates over time, and each update is analyzed against best-practice patterns to flag
risks, deviations, and anti-patterns with remediation. A portfolio view rolls every
engagement up to a colour-banded risk score, and the Personal Dashboard's Active
Engagements card reads the same ``list_portfolio``.

**State model** mirrors AGENT-02: the structured source of truth is a per-engagement
JSON in the **sessions** bucket (read back by ``get`` / ``list_portfolio``); a
human-readable markdown mirror is written to the **vault** (``meta.md`` / per-update /
``health.md``) and tagged ``generated: true`` via the shared
:func:`~agents.lambdas.modules.vault_export.export_frontmatter` helper, so the ReEmbed
pipeline flags those vectors and chat KB search scopes them out (see
``vault/decisions/runtime-vault-writers.md``). Engagement data is client-specific, so
keeping it out of curated search matters.

**analyze_update** is the one LLM step: it embeds the update, vector-searches the
*curated* assets (``content_type=asset``) for relevant best-practice references, then
asks Sonnet to produce flags + a 0-100 risk score grounded in those references. A
deterministic heuristic is the fallback when Bedrock errors.

Operations (on ``op``):
  - ``list``     — portfolio of the caller's engagements (default)
  - ``register`` — create an engagement
  - ``update``   — post an update → analyze → persist (returns the analysis)
  - ``get``      — one engagement: meta + update timeline + flags + health
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .agent_03_asset_library import _slug, _split_frontmatter
from .base import ModuleAgent
from .vault_export import export_frontmatter

AGENT_ID = "AGENT-17"
ENGAGEMENTS_PREFIX = "engagements/"
ASSET_LIBRARY_ROUTE = "/modules/asset-library"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}

UPDATE_TYPES = ("status", "architecture", "scope-change", "blocker", "decision")
_SEVERITY = ("low", "medium", "high")

ANALYZE_SYSTEM = """You are an AI delivery risk analyst. Given a single engagement update \
and a set of best-practice references retrieved from the knowledge base, assess the update \
for risks, deviations from best practice, and anti-patterns.

Return ONLY a JSON object:
{
  "flags": [
    {"severity": "low|medium|high",
     "description": "<the risk/deviation, specific to this update>",
     "remediation": "<a concrete next step>",
     "reference_ids": ["<id of a provided reference that supports this>", ...]}
  ],
  "risk_score": <integer 0-100>,
  "summary": "<one sentence overall health read>"
}

Rules: ground flags in the update text and the provided references; do not invent \
references. A clean status update may have zero flags and a low score. Scope-change and \
blocker updates usually carry more risk. Be specific and practical."""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _band(risk: int) -> str:
    if risk >= 67:
        return "red"
    if risk >= 34:
        return "amber"
    return "green"


# --- wire models -----------------------------------------------------------
class HealthFlag(BaseModel):
    severity: Literal["low", "medium", "high"] = "medium"
    description: str = ""
    remediation: str = ""
    references: list[dict] = Field(default_factory=list)  # [{id, title, url}]


class ProjectHealthAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.SONNET_4_6

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
        bedrock_client: BedrockClient | None = None,
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
        self.bedrock_client = bedrock_client or BedrockClient(client=bedrock)

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
        if "engagement_id" not in args and args.get("id"):
            args = {**args, "engagement_id": args["id"]}
        op = args.get("op")
        if op == "register":
            return self.run_tool("register_engagement", lambda _u: self._register(args))
        if op == "update" or op == "post_update":
            return self.run_tool("post_update", lambda _u: self._post_update(args))
        if op == "get" or (op is None and args.get("engagement_id")):
            return self.run_tool("get_engagement", lambda _u: self._get(args))
        return self.run_tool("list_portfolio", lambda _u: self._list(args))

    # --- state I/O ---------------------------------------------------------
    def _state_key(self, display_name: str, engagement_id: str) -> str:
        return f"{ENGAGEMENTS_PREFIX}{_slug(display_name)}/{engagement_id}.json"

    def _read_json(self, bucket: str, key: str) -> dict | None:
        try:
            raw = self.s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _NOT_FOUND:
                return None
            raise
        except (KeyError, FileNotFoundError):
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None

    def _save_state(self, state: dict) -> None:
        self.s3.put_object(
            Bucket=self.sessions_bucket,
            Key=self._state_key(state["display_name"], state["engagement_id"]),
            Body=json.dumps(state, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    def _find_state(self, engagement_id: str) -> dict | None:
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=ENGAGEMENTS_PREFIX)
        suffix = f"/{engagement_id}.json"
        for o in resp.get("Contents", []):
            if o["Key"].endswith(suffix):
                return self._read_json(self.sessions_bucket, o["Key"])
        return None

    # --- operations --------------------------------------------------------
    def _register(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        name = _norm(args.get("name"))
        if not display_name or not name:
            return {"status": "error", "message": "display_name and name are required."}
        engagement_id = "eng-" + uuid.uuid4().hex[:12]
        created_at = _now_iso()
        state = {
            "engagement_id": engagement_id,
            "display_name": display_name,
            "name": name,
            "industry": _norm(args.get("industry")),
            "ai_stage": int(args.get("ai_stage", 0) or 0),
            "use_cases": [_norm(u) for u in (args.get("use_cases") or []) if _norm(u)],
            "start_date": _norm(args.get("start_date")),
            "created_at": created_at,
            "risk_score": 0,
            "band": "green",
            "updates": [],
        }
        self._save_state(state)
        self._write_meta(state)
        self._write_health(state)
        return {"status": "ok", "engagement": self._summary(state)}

    def _post_update(self, args: dict[str, Any]) -> dict[str, Any]:
        engagement_id = _norm(args.get("engagement_id"))
        update_text = _norm(args.get("update_text"))
        if not engagement_id or not update_text:
            return {"status": "error", "message": "engagement_id and update_text are required."}
        state = self._find_state(engagement_id)
        if state is None:
            return {"status": "not_found", "engagement_id": engagement_id}
        update_type = _norm(args.get("update_type")).lower()
        if update_type not in UPDATE_TYPES:
            update_type = "status"

        analysis = self._analyze(update_text, update_type)
        ts = _now_iso()
        update = {
            "ts": ts,
            "update_type": update_type,
            "text": update_text,
            "risk_score": analysis["risk_score"],
            "summary": analysis.get("summary", ""),
            "flags": analysis["flags"],
        }
        state["updates"].append(update)
        # Portfolio risk = the latest update's score (current health).
        state["risk_score"] = analysis["risk_score"]
        state["band"] = _band(analysis["risk_score"])
        self._save_state(state)
        self._write_update(state, update)
        self._write_health(state)
        return {
            "status": "ok",
            "engagement_id": engagement_id,
            "risk_score": analysis["risk_score"],
            "band": state["band"],
            "flags": analysis["flags"],
            "summary": analysis.get("summary", ""),
        }

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        engagement_id = _norm(args.get("engagement_id"))
        if not engagement_id:
            return {"status": "error", "message": "engagement_id is required."}
        state = self._find_state(engagement_id)
        if state is None:
            return {"status": "not_found", "engagement_id": engagement_id}
        return {
            "status": "ok",
            "engagement": {
                **self._summary(state),
                "use_cases": state.get("use_cases", []),
                "start_date": state.get("start_date", ""),
                "created_at": state.get("created_at", ""),
                "updates": list(reversed(state.get("updates", []))),  # newest first
            },
        }

    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        prefix = f"{ENGAGEMENTS_PREFIX}{_slug(display_name)}/"
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=prefix)
        out: list[dict] = []
        for o in resp.get("Contents", []):
            if not o["Key"].endswith(".json"):
                continue
            state = self._read_json(self.sessions_bucket, o["Key"])
            if state:
                out.append(self._summary(state))
        # Riskiest first, then most recently updated.
        out.sort(key=lambda e: (e["risk_score"], e["last_update"]), reverse=True)
        return {"status": "ok", "engagements": out}

    @staticmethod
    def _summary(state: dict) -> dict[str, Any]:
        updates = state.get("updates", [])
        return {
            "engagement_id": state["engagement_id"],
            "name": state.get("name", ""),
            "industry": state.get("industry", ""),
            "ai_stage": int(state.get("ai_stage", 0) or 0),
            "risk_score": int(state.get("risk_score", 0) or 0),
            "band": state.get("band", "green"),
            "update_count": len(updates),
            "last_update": updates[-1]["ts"] if updates else state.get("created_at", ""),
            "open_flags": sum(len(u.get("flags", [])) for u in updates),
        }

    # --- analyze (vector grounding + Sonnet; deterministic fallback) -------
    def _analyze(self, update_text: str, update_type: str) -> dict[str, Any]:
        references = self._retrieve_patterns(update_text)
        try:
            return self._analyze_llm(update_text, update_type, references)
        except Exception:  # noqa: BLE001 — degrade to the deterministic heuristic
            return self._analyze_fallback(update_text, update_type, references)

    def _retrieve_patterns(self, text: str, top_k: int = 4) -> list[dict]:
        """Best-practice references: curated assets only (content_type=asset)."""
        try:
            resp = self.s3vectors.query_vectors(
                vectorBucketName=self.vector_bucket,
                indexName=self.index_name,
                queryVector={"float32": self._embed(text)},
                topK=max(top_k * 3, top_k),
                returnMetadata=True,
            )
        except Exception:  # noqa: BLE001 — references are best-effort
            return []
        seen: set[str] = set()
        refs: list[dict] = []
        for v in resp.get("vectors", []):
            meta = v.get("metadata", {}) or {}
            if meta.get("content_type") != "assets":
                continue
            key = meta.get("file_path") or v.get("key", "").split("#", 1)[0]
            if not key or key in seen:
                continue
            seen.add(key)
            try:
                fm, _ = _split_frontmatter(self._read(key))
            except Exception:  # noqa: BLE001
                continue
            aid = str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md"))
            refs.append({"id": aid, "title": str(fm.get("title", "")), "file_path": key})
            if len(refs) >= top_k:
                break
        return refs

    def _analyze_llm(
        self, update_text: str, update_type: str, references: list[dict]
    ) -> dict[str, Any]:
        ref_md = "\n".join(f"- {r['id']}: {r['title']}" for r in references) or "- (none)"
        user_text = (
            f"Update type: {update_type}\n\n"
            f"Update text:\n{update_text}\n\n"
            f"Best-practice references (id: title):\n{ref_md}\n\n"
            f"Return the JSON assessment."
        )
        with instrumented(
            agent_id=self.agent_id,
            tool_name="bedrock:converse",
            model_id=self.model_id,
            metrics_client=self.metrics_client,
        ) as usage:
            resp = self.bedrock_client.converse(
                model_id=self.model_id,
                messages=[{"role": "user", "content": [{"text": user_text}]}],
                system=ANALYZE_SYSTEM,
                max_tokens=900,
                usage=usage,
            )
        data = _parse_json_object(_extract_text(resp.get("output", {}).get("message", {})))
        if not data:
            raise ValueError("unparseable analysis")
        return {
            "flags": _normalize_flags(data.get("flags"), references),
            "risk_score": _clamp_score(data.get("risk_score")),
            "summary": _norm(data.get("summary")),
        }

    def _analyze_fallback(
        self, update_text: str, update_type: str, references: list[dict]
    ) -> dict[str, Any]:
        # Heuristic: update type drives a baseline risk; blocker/scope-change raise a flag.
        base = {"blocker": 70, "scope-change": 55, "architecture": 40,
                "decision": 30, "status": 20}.get(update_type, 25)
        flags: list[dict] = []
        if update_type in ("blocker", "scope-change"):
            ref = references[0] if references else None
            flags.append(
                HealthFlag(
                    severity="high" if update_type == "blocker" else "medium",
                    description=f"{update_type.replace('-', ' ').title()} reported — "
                    "review delivery plan and re-baseline scope/risk.",
                    remediation="Confirm impact with the client and update the engagement plan.",
                    references=[ref] if ref else [],
                ).model_dump()
            )
        return {
            "flags": flags,
            "risk_score": base,
            "summary": f"Automated read: {update_type} update logged.",
        }

    def _embed(self, text: str) -> list[float]:
        resp = self.bedrock.invoke_model(
            modelId=self.embed_model,
            body=json.dumps(
                {"inputText": text, "dimensions": lib_models.EMBED_DIMENSIONS, "normalize": True}
            ),
        )
        return json.loads(resp["body"].read())["embedding"]

    # --- vault markdown mirror (generated artifacts) -----------------------
    def _read(self, key: str) -> str:
        return self.s3.get_object(Bucket=self.vault_bucket, Key=key)["Body"].read().decode("utf-8")

    def _eng_dir(self, state: dict) -> str:
        return f"{ENGAGEMENTS_PREFIX}{_slug(state['display_name'])}/{state['engagement_id']}"

    def _put_vault(self, key: str, body: str) -> None:
        self.s3.put_object(
            Bucket=self.vault_bucket, Key=key, Body=body.encode("utf-8"),
            ContentType="text/markdown",
        )

    def _write_meta(self, state: dict) -> None:
        fm = export_frontmatter(
            "engagement",
            {
                "engagement_id": state["engagement_id"],
                "title": state["name"],
                "display_name": state["display_name"],
                "industry": state.get("industry", ""),
                "ai_stage": state.get("ai_stage", 0),
                "use_cases": state.get("use_cases", []),
                "start_date": state.get("start_date", ""),
                "created_at": state.get("created_at", ""),
            },
        )
        uc = "\n".join(f"- {u}" for u in state.get("use_cases", [])) or "- (none)"
        body = (
            f"{fm}\n# Engagement — {state['name']}\n\n"
            f"Industry: {state.get('industry') or 'n/a'} · Stage {state.get('ai_stage', 0)}\n\n"
            f"## Use cases\n\n{uc}\n"
        )
        self._put_vault(f"{self._eng_dir(state)}/meta.md", body)

    def _write_update(self, state: dict, update: dict) -> None:
        fm = export_frontmatter(
            "engagement-update",
            {
                "engagement_id": state["engagement_id"],
                "title": f"{state['name']} — {update['update_type']} update",
                "display_name": state["display_name"],
                "update_type": update["update_type"],
                "risk_score": update["risk_score"],
                "created_at": update["ts"],
            },
        )
        flags_md = "\n".join(
            f"- **[{f.get('severity')}]** {f.get('description')}  \n"
            f"  _Remediation:_ {f.get('remediation')}"
            for f in update.get("flags", [])
        ) or "- (no flags)"
        ts_key = update["ts"].replace(":", "-")
        body = (
            f"{fm}\n# {update['update_type'].title()} update\n\n{update['text']}\n\n"
            f"## Analysis (risk {update['risk_score']}/100)\n\n"
            f"{update.get('summary') or ''}\n\n### Flags\n\n{flags_md}\n"
        )
        self._put_vault(f"{self._eng_dir(state)}/updates/{ts_key}.md", body)

    def _write_health(self, state: dict) -> None:
        fm = export_frontmatter(
            "engagement-health",
            {
                "engagement_id": state["engagement_id"],
                "title": f"{state['name']} — health",
                "display_name": state["display_name"],
                "risk_score": state.get("risk_score", 0),
                "band": state.get("band", "green"),
                "updated_at": _now_iso(),
            },
        )
        body = (
            f"{fm}\n# Health — {state['name']}\n\n"
            f"Current risk: **{state.get('risk_score', 0)}/100** ({state.get('band', 'green')}).\n"
        )
        self._put_vault(f"{self._eng_dir(state)}/health.md", body)


# --- module-level helpers --------------------------------------------------
def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()


def _parse_json_object(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t).strip()
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end > start:
        t = t[start : end + 1]
    try:
        data = json.loads(t)
    except (json.JSONDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _clamp_score(value: Any) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return 30


def _normalize_flags(raw: Any, references: list[dict]) -> list[dict]:
    by_id = {r["id"]: r for r in references}
    out: list[dict] = []
    for item in raw or []:
        if not isinstance(item, dict) or not _norm(item.get("description")):
            continue
        sev = _norm(item.get("severity")).lower()
        ref_ids = item.get("reference_ids") or item.get("references") or []
        refs = [by_id[str(i)] for i in ref_ids if str(i) in by_id]
        out.append(
            HealthFlag(
                severity=sev if sev in _SEVERITY else "medium",
                description=_norm(item.get("description")),
                remediation=_norm(item.get("remediation")),
                references=refs,
            ).model_dump()
        )
    return out
