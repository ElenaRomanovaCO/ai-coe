"""AGENT-15 — Engagement Retrospective Tracker (Module 16), Sonnet 4.6 tier.

At engagement close a consultant files a structured retro (use cases attempted,
patterns used, what worked, what failed, tool recommendations, stage reassessment).
AGENT-15 saves the retro and uses Sonnet to extract 2-4 **reusable insights**, each
written to the knowledge base and linked back to the retro and the assets it relates to.

Two storage tiers, by audience:
  - The **retro** (``retros/{display_name}/{retro_id}.md``) is engagement-specific, so it
    is tagged ``generated: true`` via the shared
    :func:`~agents.lambdas.modules.vault_export.export_frontmatter` helper and scoped out
    of curated chat KB search (``vault/decisions/runtime-vault-writers.md``).
  - The **insights** (``insights/{insight_id}.md``) are the whole point: reusable,
    generic knowledge. They are written WITHOUT the generated flag, under the
    ``insights/`` folder, which the orchestrator maps to the ``insight`` content type — so
    they ARE retrievable by chat ``search_knowledge_base`` (FR-055).

Structured state lives in the sessions bucket (read back by ``get`` / ``list``), mirroring
AGENT-02. ``extract_insights`` is the one LLM call, with a deterministic fallback.

Operations (on ``op``):
  - ``write``  — save a retro + extract insights (default when ``engagement_id`` present)
  - ``get``    — one retro + its insights
  - ``list``   — the caller's retros
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import ClientError
from pydantic import BaseModel

from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .agent_03_asset_library import _slug
from .base import ModuleAgent
from .vault_export import _scalar, export_frontmatter

AGENT_ID = "AGENT-15"
RETROS_PREFIX = "retros/"
INSIGHTS_PREFIX = "insights/"
ASSET_LIBRARY_ROUTE = "/modules/asset-library"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}

_INSIGHT_TYPES = ("pattern", "tooling", "process", "risk", "people", "general")

EXTRACT_SYSTEM = """You extract reusable, generic insights from an engagement \
retrospective so they can be reused across future engagements. Given the retro fields, \
produce 2-4 insights.

Return ONLY a JSON object:
{
  "insights": [
    {"type": "pattern|tooling|process|risk|people|general",
     "statement": "<the reusable lesson, generic — no client names>",
     "evidence": "<the specific retro detail that supports it>",
     "asset_id": "<an id from patterns_used this relates to, or empty>"}
  ]
}

Rules: insights must be GENERIC and reusable (no company/client names, no PII). Ground \
each in the retro text. Prefer concrete, actionable lessons. Tie an insight to a \
patterns_used asset id when relevant."""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _list_str(values: Any) -> list[str]:
    return [_norm(v) for v in (values or []) if _norm(v)]


class Insight(BaseModel):
    insight_id: str
    type: str = "general"
    statement: str = ""
    evidence: str = ""
    asset_link: str | None = None
    retro_id: str = ""
    file_path: str = ""


class RetrospectiveAgent(ModuleAgent):
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
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.region = region
        self._s3 = s3
        self.bedrock_client = bedrock_client or BedrockClient(client=bedrock)

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        if "retro_id" not in args and args.get("id"):
            args = {**args, "retro_id": args["id"]}
        op = args.get("op")
        if op == "write" or (op is None and args.get("engagement_id") and args.get("display_name")):
            return self.run_tool("write_retro", lambda _u: self._write(args))
        if op == "get" or (op is None and args.get("retro_id")):
            return self.run_tool("get_retro", lambda _u: self._get(args))
        return self.run_tool("list_retros", lambda _u: self._list(args))

    # --- state I/O ---------------------------------------------------------
    def _state_key(self, display_name: str, retro_id: str) -> str:
        return f"{RETROS_PREFIX}{_slug(display_name)}/{retro_id}.json"

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
            Key=self._state_key(state["display_name"], state["retro_id"]),
            Body=json.dumps(state, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    def _find_state(self, retro_id: str) -> dict | None:
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=RETROS_PREFIX)
        suffix = f"/{retro_id}.json"
        for o in resp.get("Contents", []):
            if o["Key"].endswith(suffix):
                return self._read_json(self.sessions_bucket, o["Key"])
        return None

    # --- operations --------------------------------------------------------
    def _write(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        engagement_id = _norm(args.get("engagement_id"))
        if not display_name or not engagement_id:
            return {"status": "error", "message": "display_name and engagement_id are required."}

        retro_id = "retro-" + uuid.uuid4().hex[:12]
        created_at = _now_iso()
        retro = {
            "retro_id": retro_id,
            "display_name": display_name,
            "engagement_id": engagement_id,
            "use_cases_attempted": _list_str(args.get("use_cases_attempted")),
            "patterns_used": _list_str(args.get("patterns_used")),
            "what_worked": _norm(args.get("what_worked")),
            "what_failed": _norm(args.get("what_failed")),
            "tools_recommended": _list_str(args.get("tools_recommended")),
            "tools_not_recommended": _list_str(args.get("tools_not_recommended")),
            "stage_reassessment": int(args.get("stage_reassessment", 0) or 0),
            "created_at": created_at,
        }

        insights = self._extract_insights(retro)
        # Persist each insight as a reusable KB entry (searchable; not generated-flagged).
        for ins in insights:
            self._write_insight(retro, ins)

        retro["insights"] = [i.model_dump() for i in insights]
        self._save_state(retro)
        self._write_retro_md(retro, insights)
        return {"status": "ok", "retro": self._public(retro), "insights": retro["insights"]}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        retro_id = _norm(args.get("retro_id"))
        if not retro_id:
            return {"status": "error", "message": "retro_id is required."}
        state = self._find_state(retro_id)
        if state is None:
            return {"status": "not_found", "retro_id": retro_id}
        return {"status": "ok", "retro": self._public(state), "insights": state.get("insights", [])}

    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        prefix = f"{RETROS_PREFIX}{_slug(display_name)}/"
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=prefix)
        out: list[dict] = []
        for o in resp.get("Contents", []):
            if not o["Key"].endswith(".json"):
                continue
            state = self._read_json(self.sessions_bucket, o["Key"])
            if state:
                out.append(
                    {
                        "retro_id": state["retro_id"],
                        "engagement_id": state.get("engagement_id", ""),
                        "stage_reassessment": state.get("stage_reassessment", 0),
                        "insight_count": len(state.get("insights", [])),
                        "created_at": state.get("created_at", ""),
                    }
                )
        out.sort(key=lambda r: r["created_at"], reverse=True)
        return {"status": "ok", "retros": out}

    @staticmethod
    def _public(state: dict) -> dict[str, Any]:
        return {
            "retro_id": state["retro_id"],
            "engagement_id": state.get("engagement_id", ""),
            "use_cases_attempted": state.get("use_cases_attempted", []),
            "patterns_used": state.get("patterns_used", []),
            "what_worked": state.get("what_worked", ""),
            "what_failed": state.get("what_failed", ""),
            "tools_recommended": state.get("tools_recommended", []),
            "tools_not_recommended": state.get("tools_not_recommended", []),
            "stage_reassessment": state.get("stage_reassessment", 0),
            "created_at": state.get("created_at", ""),
        }

    # --- insight extraction (the one LLM call; deterministic fallback) -----
    def _extract_insights(self, retro: dict) -> list[Insight]:
        try:
            raw = self._extract_llm(retro)
        except Exception:  # noqa: BLE001 — degrade to the deterministic fallback
            raw = self._extract_fallback(retro)
        patterns = set(retro.get("patterns_used", []))
        out: list[Insight] = []
        for item in raw[:4]:
            if not isinstance(item, dict) or not _norm(item.get("statement")):
                continue
            itype = _norm(item.get("type")).lower()
            asset = _norm(item.get("asset_id") or item.get("asset_link")) or None
            if asset and asset not in patterns:
                asset = None  # link_back_to_assets: only link real patterns_used assets
            out.append(
                Insight(
                    insight_id="insight-" + uuid.uuid4().hex[:12],
                    type=itype if itype in _INSIGHT_TYPES else "general",
                    statement=_norm(item.get("statement")),
                    evidence=_norm(item.get("evidence")),
                    asset_link=asset,
                    retro_id=retro["retro_id"],
                )
            )
        return out

    def _extract_llm(self, retro: dict) -> list[dict]:
        user_text = (
            f"Use cases attempted: {', '.join(retro['use_cases_attempted']) or '(none)'}\n"
            f"Patterns used (asset ids): {', '.join(retro['patterns_used']) or '(none)'}\n"
            f"What worked:\n{retro['what_worked'] or '(none)'}\n\n"
            f"What failed:\n{retro['what_failed'] or '(none)'}\n\n"
            f"Tools recommended: {', '.join(retro['tools_recommended']) or '(none)'}\n"
            f"Tools NOT recommended: {', '.join(retro['tools_not_recommended']) or '(none)'}\n"
            f"Stage reassessment: {retro['stage_reassessment']}\n\n"
            f"Extract the JSON insights."
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
                system=EXTRACT_SYSTEM,
                max_tokens=900,
                usage=usage,
            )
        data = _parse_json_object(_extract_text(resp.get("output", {}).get("message", {})))
        insights = data.get("insights") if isinstance(data, dict) else None
        if not isinstance(insights, list) or not insights:
            raise ValueError("no insights parsed")
        return insights

    def _extract_fallback(self, retro: dict) -> list[dict]:
        out: list[dict] = []
        if retro.get("what_worked"):
            out.append({
                "type": "pattern",
                "statement": "Approach that worked is worth reusing on similar engagements.",
                "evidence": retro["what_worked"],
                "asset_id": (retro.get("patterns_used") or [""])[0],
            })
        if retro.get("what_failed"):
            out.append({
                "type": "risk",
                "statement": "A failure mode to watch for and mitigate early next time.",
                "evidence": retro["what_failed"],
                "asset_id": "",
            })
        if retro.get("tools_not_recommended"):
            out.append({
                "type": "tooling",
                "statement": "Tooling to avoid (or scope carefully) for this kind of work.",
                "evidence": "Not recommended: " + ", ".join(retro["tools_not_recommended"]),
                "asset_id": "",
            })
        return out or [{
            "type": "general", "statement": "Engagement retrospective recorded.",
            "evidence": "", "asset_id": "",
        }]

    # --- vault writes ------------------------------------------------------
    def _write_insight(self, retro: dict, ins: Insight) -> None:
        """A reusable KB entry: content_type=insight (searchable), NOT generated-flagged."""
        title = ins.statement[:70]
        link = (
            f"\n## Related asset\n\n[{ins.asset_link}]({ASSET_LIBRARY_ROUTE}/{ins.asset_link})\n"
            if ins.asset_link
            else ""
        )
        body = (
            "---\n"
            f"id: {ins.insight_id}\n"
            "content_type: insight\n"
            f"type: {ins.type}\n"
            f"title: {_scalar(title)}\n"
            f"retro_id: {retro['retro_id']}\n"
            f"engagement_id: {_scalar(retro.get('engagement_id', ''))}\n"
            f"asset_link: {ins.asset_link or ''}\n"
            f"created_at: {retro['created_at']}\n"
            "---\n\n"
            f"# Insight — {ins.type}\n\n{ins.statement}\n\n"
            f"## Evidence\n\n{ins.evidence or '(from retrospective)'}\n{link}"
        )
        ins.file_path = f"{INSIGHTS_PREFIX}{ins.insight_id}.md"
        self.s3.put_object(
            Bucket=self.vault_bucket, Key=ins.file_path, Body=body.encode("utf-8"),
            ContentType="text/markdown",
        )

    def _write_retro_md(self, retro: dict, insights: list[Insight]) -> None:
        fm = export_frontmatter(
            "retro",
            {
                "retro_id": retro["retro_id"],
                "title": f"Retrospective — {retro['engagement_id']}",
                "display_name": retro["display_name"],
                "engagement_id": retro["engagement_id"],
                "stage_reassessment": retro["stage_reassessment"],
                "created_at": retro["created_at"],
            },
        )
        uc = "\n".join(f"- {u}" for u in retro["use_cases_attempted"]) or "- (none)"
        pat = "\n".join(f"- `{p}`" for p in retro["patterns_used"]) or "- (none)"
        ins_md = "\n".join(f"- **[{i.type}]** {i.statement}" for i in insights) or "- (none)"
        body = (
            f"{fm}\n# Retrospective\n\n"
            f"## Use cases attempted\n\n{uc}\n\n"
            f"## Patterns used\n\n{pat}\n\n"
            f"## What worked\n\n{retro['what_worked'] or '(none)'}\n\n"
            f"## What failed\n\n{retro['what_failed'] or '(none)'}\n\n"
            f"## Stage reassessment\n\nStage {retro['stage_reassessment']}\n\n"
            f"## Extracted insights\n\n{ins_md}\n"
        )
        self.s3.put_object(
            Bucket=self.vault_bucket,
            Key=f"{RETROS_PREFIX}{_slug(retro['display_name'])}/{retro['retro_id']}.md",
            Body=body.encode("utf-8"),
            ContentType="text/markdown",
        )


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
