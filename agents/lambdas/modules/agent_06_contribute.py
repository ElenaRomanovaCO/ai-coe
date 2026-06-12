"""AGENT-06 — Knowledge Contribution (Module 5), Sonnet 4.6 tier.

Lets a consultant submit a new asset (case study, pattern, lesson learned), runs
**AI-assisted anonymization + tag suggestion** (one Sonnet call) and a **duplicate check**
(vector similarity, composing AGENT-03), holds it in a curator queue, and on approval writes
the finished asset into the live Asset Library path where the ReEmbed pipeline indexes it.

**Pending submissions live in the SESSIONS bucket** (``contributions/{pending_id}.json``), NOT
``vault/pending/`` as the spec sketched: un-reviewed, un-anonymized content must never reach the
vault, where ReEmbed would index it into the searchable KB before curation (the
``curated-content-in-vault`` principle — only reviewed content enters the vault). ``approve``
writes the final markdown to ``vault/assets/{industry}/{ai_stage}/{slug}.md`` and marks the
pending record approved (no S3 delete — the module-agents role has Get/Put only, so this also
needs **no new IAM**).

Operations (on ``op``):
  - ``submit_asset``       — persist a submission + run anonymization/tags/duplicates (FR-064/066)
  - ``run_anonymization``  — (re)flag identifying spans + propose an anonymized body (FR-066)
  - ``suggest_tags``       — topical tags + likely duplicates (FR-066)
  - ``list_pending``       — curator queue (FR-065)
  - ``get_pending``        — one submission with its analysis
  - ``approve_asset``      — write the final asset to the live vault path (FR-065)
  - ``reject_asset``       — mark a submission rejected
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import UTC, datetime
from typing import Any

import yaml
from botocore.exceptions import ClientError

from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .agent_03_asset_library import AssetLibraryAgent, _slug
from .base import ModuleAgent

AGENT_ID = "AGENT-06"
CONTRIBUTE_ROUTE = "/modules/contribute"
PENDING_PREFIX = "contributions/"
ASSET_PREFIX = "assets/"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}

ANALYZE_SYSTEM = """You review a knowledge contribution before it enters a shared consulting \
library. Two jobs:

1. ANONYMIZE: find text that could identify a specific real client, person, or company, and \
propose a neutral replacement. Flag company names, individual people's names, identifiable \
project/product names, and locations specific enough to pin down a client. Do NOT flag generic \
technical terms, public tool/vendor names, public regulation names, or industries.
2. TAG: suggest 3-6 lowercase topical tags.

Return ONLY a JSON object:
{
  "flagged_spans": [
    {"span": "<verbatim text from the body>",
     "suggested_replacement": "<neutral text>", "reason": "<short why>"}
  ],
  "suggested_anonymized_body": "<the body with every replacement applied; otherwise identical>",
  "tags": ["<tag>", ...]
}

If nothing needs anonymizing, return an empty flagged_spans list and the body unchanged."""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _norm(s: Any) -> str:
    return str(s or "").strip()


class ContributeAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.SONNET_4_6

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        sessions_bucket: str | None = None,
        region: str = lib_models.REGION,
        s3: Any = None,
        bedrock: Any = None,
        bedrock_client: BedrockClient | None = None,
        asset_agent: AssetLibraryAgent | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.region = region
        self._s3 = s3
        self._bedrock = bedrock
        self.bedrock_client = bedrock_client or BedrockClient(client=bedrock)
        self._asset_agent = asset_agent

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    @property
    def assets(self) -> AssetLibraryAgent:
        # Compose AGENT-03 for the duplicate vector search (shared clients).
        if self._asset_agent is None:
            self._asset_agent = AssetLibraryAgent(
                vault_bucket=self.vault_bucket,
                sessions_bucket=self.sessions_bucket,
                region=self.region,
                s3=self._s3,
                bedrock=self._bedrock,
                metrics_client=self.metrics_client,
            )
        return self._asset_agent

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        if "pending_id" not in args and args.get("id"):
            args = {**args, "pending_id": args["id"]}
        op = args.get("op")
        dispatch = {
            "submit_asset": self._submit,
            "run_anonymization": self._run_anonymization,
            "suggest_tags": self._suggest_tags,
            "list_pending": self._list_pending,
            "get_pending": self._get_pending,
            "approve_asset": self._approve,
            "reject_asset": self._reject,
        }
        fn = dispatch.get(op or "")
        if fn is None:
            if args.get("pending_id"):
                return self.run_tool("get_pending", lambda _u: self._get_pending(args))
            return {"status": "error", "message": f"Unknown op '{op}'."}
        return self.run_tool(op, lambda _u, _fn=fn: _fn(args))

    # --- state I/O (sessions) ----------------------------------------------
    def _key(self, pending_id: str) -> str:
        return f"{PENDING_PREFIX}{pending_id}.json"

    def _read(self, pending_id: str) -> dict | None:
        try:
            raw = self.s3.get_object(Bucket=self.sessions_bucket, Key=self._key(pending_id))[
                "Body"
            ].read()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _NOT_FOUND:
                return None
            raise
        except (KeyError, FileNotFoundError):
            return None
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return None

    def _write(self, record: dict) -> None:
        self.s3.put_object(
            Bucket=self.sessions_bucket,
            Key=self._key(record["pending_id"]),
            Body=json.dumps(record, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    # --- operations --------------------------------------------------------
    def _submit(self, args: dict[str, Any]) -> dict[str, Any]:
        for k in ("display_name", "title", "body_markdown"):
            if not _norm(args.get(k)):
                return {"status": "error", "message": f"{k} is required."}
        pending_id = "contrib-" + uuid.uuid4().hex[:12]
        body = str(args.get("body_markdown"))
        title = _norm(args.get("title"))
        record = {
            "pending_id": pending_id,
            "review_status": "pending",
            "display_name": _norm(args.get("display_name")),
            "title": title,
            "type": _norm(args.get("type")),
            "industry": _norm(args.get("industry")),
            "ai_stage": int(args.get("ai_stage") or 0),
            "body_markdown": body,
            "contributor_notes": _norm(args.get("contributor_notes")),
            "created_at": _now_iso(),
        }
        analysis = self._analyze(title, body)
        record["anonymization"] = {
            "flagged_spans": analysis["flagged_spans"],
            "suggested_anonymized_body": analysis["suggested_anonymized_body"],
        }
        duplicates = self._duplicates(title, body)
        record["tag_suggestions"] = {"tags": analysis["tags"], "duplicates": duplicates}
        self._write(record)
        return {"status": "ok", **record}

    def _run_anonymization(self, args: dict[str, Any]) -> dict[str, Any]:
        record, body, title = self._resolve_body(args)
        if body is None:
            return {"status": "error", "message": "pending_id or body_markdown is required."}
        analysis = self._analyze(title, body)
        anon = {
            "flagged_spans": analysis["flagged_spans"],
            "suggested_anonymized_body": analysis["suggested_anonymized_body"],
        }
        if record is not None:
            record["anonymization"] = anon
            self._write(record)
        return {"status": "ok", **anon}

    def _suggest_tags(self, args: dict[str, Any]) -> dict[str, Any]:
        record, body, title = self._resolve_body(args)
        if body is None:
            return {"status": "error", "message": "pending_id or body_markdown is required."}
        analysis = self._analyze(title, body)
        duplicates = self._duplicates(title, body)
        result = {"tags": analysis["tags"], "duplicates": duplicates}
        if record is not None:
            record["tag_suggestions"] = result
            self._write(record)
        return {"status": "ok", **result}

    def _list_pending(self, args: dict[str, Any]) -> dict[str, Any]:
        status_filter = _norm(args.get("status")) or "pending"
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=PENDING_PREFIX)
        out = []
        for o in resp.get("Contents", []):
            if not o["Key"].endswith(".json"):
                continue
            rec = self._read(o["Key"].rsplit("/", 1)[-1].removesuffix(".json"))
            if not rec:
                continue
            if status_filter != "all" and rec.get("review_status") != status_filter:
                continue
            out.append(
                {
                    "pending_id": rec["pending_id"],
                    "title": rec.get("title", ""),
                    "display_name": rec.get("display_name", ""),
                    "type": rec.get("type", ""),
                    "industry": rec.get("industry", ""),
                    "review_status": rec.get("review_status", ""),
                    "created_at": rec.get("created_at", ""),
                    "flag_count": len((rec.get("anonymization") or {}).get("flagged_spans", [])),
                }
            )
        out.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return {"status": "ok", "pending": out}

    def _get_pending(self, args: dict[str, Any]) -> dict[str, Any]:
        pending_id = _norm(args.get("pending_id"))
        if not pending_id:
            return {"status": "error", "message": "pending_id is required."}
        rec = self._read(pending_id)
        if rec is None:
            return {"status": "not_found", "pending_id": pending_id}
        return {"status": "ok", **rec}

    def _approve(self, args: dict[str, Any]) -> dict[str, Any]:
        pending_id = _norm(args.get("pending_id"))
        if not pending_id:
            return {"status": "error", "message": "pending_id is required."}
        rec = self._read(pending_id)
        if rec is None:
            return {"status": "not_found", "pending_id": pending_id}
        if rec.get("review_status") == "approved":
            return {"status": "error", "message": "Already approved."}

        final_body = _norm(args.get("final_body")) or rec.get("body_markdown", "")
        fm = dict(args.get("final_frontmatter") or {})
        industry = _norm(fm.get("industry") or rec.get("industry")) or "cross-industry"
        ai_stage = int(fm.get("ai_stage") or rec.get("ai_stage") or 0)
        asset_id = _norm(fm.get("id")) or _slug(rec.get("title", pending_id))
        # Fill required AssetFrontmatter fields if the curator left them out.
        fm.setdefault("id", asset_id)
        fm.setdefault("title", rec.get("title", ""))
        fm.setdefault("type", rec.get("type", "solution-pattern"))
        fm["industry"] = industry
        fm["ai_stage"] = ai_stage
        fm.setdefault("use_case_type", fm.get("use_case_type") or [])
        fm.setdefault("tags", fm.get("tags") or [])
        fm.setdefault("contributor", rec.get("display_name", "demo"))
        fm["updated_at"] = _now_iso()[:10]

        target_path = _norm(args.get("target_path")) or (
            f"{ASSET_PREFIX}{_slug(industry)}/{ai_stage}/{_slug(asset_id)}.md"
        )
        if not target_path.startswith(ASSET_PREFIX) or ".." in target_path:
            return {"status": "error", "message": "target_path must be under assets/."}

        fm_yaml = yaml.safe_dump(fm, sort_keys=False).strip()
        document = f"---\n{fm_yaml}\n---\n\n{final_body.strip()}\n"
        self.s3.put_object(
            Bucket=self.vault_bucket,
            Key=target_path,
            Body=document.encode("utf-8"),
            ContentType="text/markdown",
        )
        rec["review_status"] = "approved"
        rec["approved"] = {
            "asset_id": fm["id"],
            "file_path": target_path,
            "approved_at": _now_iso(),
        }
        self._write(rec)
        return {
            "status": "ok",
            "pending_id": pending_id,
            "asset_id": fm["id"],
            "file_path": target_path,
        }

    def _reject(self, args: dict[str, Any]) -> dict[str, Any]:
        pending_id = _norm(args.get("pending_id"))
        if not pending_id:
            return {"status": "error", "message": "pending_id is required."}
        rec = self._read(pending_id)
        if rec is None:
            return {"status": "not_found", "pending_id": pending_id}
        rec["review_status"] = "rejected"
        rec["rejection_reason"] = _norm(args.get("reason"))
        self._write(rec)
        return {"status": "ok", "pending_id": pending_id, "rejected": True}

    # --- helpers -----------------------------------------------------------
    def _resolve_body(self, args: dict[str, Any]) -> tuple[dict | None, str | None, str]:
        if args.get("pending_id"):
            rec = self._read(_norm(args.get("pending_id")))
            if rec is not None:
                return rec, rec.get("body_markdown", ""), rec.get("title", "")
        body = args.get("body_markdown")
        if body is not None:
            return None, str(body), _norm(args.get("title"))
        return None, None, ""

    def _analyze(self, title: str, body: str) -> dict[str, Any]:
        user_text = f"Title: {title}\n\nBody:\n{body}\n\nReturn the JSON."
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
                    system=ANALYZE_SYSTEM,
                    max_tokens=2000,
                    usage=usage,
                )
            data = _parse_json_object(_extract_text(resp.get("output", {}).get("message", {})))
            if data:
                spans = []
                for s in data.get("flagged_spans") or []:
                    span = _norm(s.get("span"))
                    if not span:
                        continue
                    spans.append(
                        {
                            "span": span,
                            "offset": body.find(span),
                            "suggested_replacement": _norm(s.get("suggested_replacement")),
                            "reason": _norm(s.get("reason")),
                        }
                    )
                anon_body = _norm(data.get("suggested_anonymized_body")) or body
                return {
                    "flagged_spans": spans,
                    "suggested_anonymized_body": anon_body,
                    "tags": [str(t).lower() for t in (data.get("tags") or []) if _norm(t)],
                }
        except Exception:  # noqa: BLE001 — degrade to a no-op analysis
            pass
        return {"flagged_spans": [], "suggested_anonymized_body": body, "tags": []}

    def _duplicates(self, title: str, body: str) -> list[dict]:
        query = f"{title}\n{body}".strip()[:1000]
        try:
            res = self.assets.handle({"op": "search", "query": query, "top_k": 3})
        except Exception:  # noqa: BLE001 — duplicates are advisory
            return []
        return res.get("assets", []) if res.get("status") == "ok" else []


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
