"""AGENT-29 — AI SOW Generator (Module 30), Sonnet 4.6 tier.

Generates a draft Statement of Work from engagement context: a **deterministic skeleton**
(fixed section order; structured inputs — deliverables, milestones, pricing — placed
verbatim) plus **one** Sonnet call that drafts the prose sections (objectives narrative,
scope description, assumptions, acceptance criteria) grounded in the supplied inputs. A
deterministic skeleton-only assembly is the fallback when Bedrock fails.

SOWs are client-specific engagement documents, so they are persisted to the **sessions**
bucket (``sow/{display_name}/{id}.md`` + a ``.json`` state) and never to the vault — they
must not enter the searchable knowledge base. Export is a presigned GET of the markdown,
reusing the kit-builder artifact pattern (``vault/decisions`` n/a; see AGENT-04).

Operations (on ``op``):
  - ``generate`` — skeleton + Sonnet prose → assemble + persist → presigned URL (default)
  - ``get``      — one saved SOW (with a fresh presigned URL)
  - ``list``     — the caller's saved SOWs
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .agent_03_asset_library import _slug
from .base import ModuleAgent

AGENT_ID = "AGENT-29"
SOW_PREFIX = "sow/"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}

ENGAGEMENT_TYPES = ("assessment", "pilot", "build", "advisory")
PRICING_MODELS = ("fixed", "T&M", "milestone")

PROSE_SYSTEM = """You draft the prose sections of a Statement of Work, grounded ONLY in \
the structured inputs provided. Do not invent deliverables, dates, prices, or \
commitments beyond the inputs.

Return ONLY a JSON object:
{
  "objectives_narrative": "<1 short paragraph framing the engagement's objectives>",
  "scope_description": "<1 short paragraph describing the scope and approach>",
  "acceptance_criteria": ["<criterion tied to a deliverable>", ...],
  "assumptions_extra": ["<reasonable standard assumption not already listed>", ...]
}

Keep it concise, professional, and specific to the inputs. No client names beyond what \
is given; no PII."""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _list_str(values: Any) -> list[str]:
    return [_norm(v) for v in (values or []) if _norm(v)]


class SowRequest(BaseModel):
    client_context: str = ""
    engagement_type: str = ""
    objectives: list[str] = Field(default_factory=list)
    scope_items: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    timeline_weeks: int = 0
    milestones: list[str] = Field(default_factory=list)
    pricing_model: str = ""
    assumptions: list[str] = Field(default_factory=list)
    display_name: str = ""


class SowGeneratorAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.SONNET_4_6

    def __init__(
        self,
        *,
        sessions_bucket: str | None = None,
        region: str = lib_models.REGION,
        s3: Any = None,
        bedrock: Any = None,
        bedrock_client: BedrockClient | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
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
        if "sow_id" not in args and args.get("id"):
            args = {**args, "sow_id": args["id"]}
        op = args.get("op")
        if op == "get" or (op is None and args.get("sow_id")):
            return self.run_tool("get_sow", lambda _u: self._get(args))
        if op == "list":
            return self.run_tool("list_sow", lambda _u: self._list(args))
        return self.run_tool("generate_sow", lambda _u: self._generate(args))

    # --- state I/O (sessions only) -----------------------------------------
    def _md_key(self, display_name: str, sow_id: str) -> str:
        return f"{SOW_PREFIX}{_slug(display_name)}/{sow_id}.md"

    def _state_key(self, display_name: str, sow_id: str) -> str:
        return f"{SOW_PREFIX}{_slug(display_name)}/{sow_id}.json"

    def _read_json(self, key: str) -> dict | None:
        try:
            raw = self.s3.get_object(Bucket=self.sessions_bucket, Key=key)["Body"].read()
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

    def _presign(self, key: str) -> str | None:
        try:
            return self.s3.generate_presigned_url(
                "get_object", Params={"Bucket": self.sessions_bucket, "Key": key}, ExpiresIn=3600
            )
        except Exception:  # noqa: BLE001 — export link is best-effort
            return None

    # --- operations --------------------------------------------------------
    def _generate(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        req = SowRequest.model_validate({**args, "display_name": display_name})

        prose = self._draft_prose(req)
        title, markdown, sections = self._assemble(req, prose)

        sow_id = "sow-" + uuid.uuid4().hex[:12]
        created_at = _now_iso()
        md_key = self._md_key(display_name, sow_id)
        self.s3.put_object(
            Bucket=self.sessions_bucket, Key=md_key, Body=markdown.encode("utf-8"),
            ContentType="text/markdown",
        )
        state = {
            "sow_id": sow_id,
            "display_name": display_name,
            "created_at": created_at,
            "title": title,
            "sections": sections,
            "md_key": md_key,
            "inputs": req.model_dump(),
            "markdown": markdown,
        }
        self.s3.put_object(
            Bucket=self.sessions_bucket, Key=self._state_key(display_name, sow_id),
            Body=json.dumps(state, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )
        return {
            "status": "ok", "sow_id": sow_id, "created_at": created_at, "title": title,
            "sections": sections, "markdown": markdown, "download_url": self._presign(md_key),
        }

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        sow_id = _norm(args.get("sow_id"))
        if not sow_id:
            return {"status": "error", "message": "sow_id is required."}
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=SOW_PREFIX)
        suffix = f"/{sow_id}.json"
        for o in resp.get("Contents", []):
            if o["Key"].endswith(suffix):
                state = self._read_json(o["Key"])
                if state:
                    return {
                        "status": "ok", "sow_id": state["sow_id"], "title": state.get("title", ""),
                        "sections": state.get("sections", []),
                        "markdown": state.get("markdown", ""),
                        "created_at": state.get("created_at", ""),
                        "inputs": state.get("inputs", {}),
                        "download_url": self._presign(state.get("md_key", "")),
                    }
        return {"status": "not_found", "sow_id": sow_id}

    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        prefix = f"{SOW_PREFIX}{_slug(display_name)}/"
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=prefix)
        out: list[dict] = []
        for o in resp.get("Contents", []):
            if not o["Key"].endswith(".json"):
                continue
            state = self._read_json(o["Key"])
            if state:
                out.append({
                    "sow_id": state["sow_id"],
                    "title": state.get("title", ""),
                    "engagement_type": state.get("inputs", {}).get("engagement_type", ""),
                    "created_at": state.get("created_at", ""),
                })
        out.sort(key=lambda s: s["created_at"], reverse=True)
        return {"status": "ok", "sows": out}

    # --- prose (the one LLM call; skeleton-only fallback) ------------------
    def _draft_prose(self, req: SowRequest) -> dict[str, Any]:
        user_text = (
            f"Client context: {req.client_context or '(none)'}\n"
            f"Engagement type: {req.engagement_type or '(unspecified)'}\n"
            f"Objectives: {', '.join(req.objectives) or '(none)'}\n"
            f"Scope items: {', '.join(req.scope_items) or '(none)'}\n"
            f"Deliverables: {', '.join(req.deliverables) or '(none)'}\n"
            f"Timeline: {req.timeline_weeks} weeks\n"
            f"Milestones: {', '.join(req.milestones) or '(none)'}\n"
            f"Pricing model: {req.pricing_model or '(unspecified)'}\n"
            f"Assumptions: {', '.join(req.assumptions) or '(none)'}\n\n"
            f"Draft the SOW prose JSON."
        )
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
                    system=PROSE_SYSTEM,
                    max_tokens=900,
                    usage=usage,
                )
            data = _parse_json_object(_extract_text(resp.get("output", {}).get("message", {})))
            if data:
                return {
                    "objectives_narrative": _norm(data.get("objectives_narrative")),
                    "scope_description": _norm(data.get("scope_description")),
                    "acceptance_criteria": _list_str(data.get("acceptance_criteria")),
                    "assumptions_extra": _list_str(data.get("assumptions_extra")),
                }
        except Exception:  # noqa: BLE001 — fall back to a skeleton-only SOW
            pass
        return {
            "objectives_narrative": "",
            "scope_description": "",
            "acceptance_criteria": [],
            "assumptions_extra": [],
        }

    # --- deterministic skeleton assembly -----------------------------------
    def _assemble(self, req: SowRequest, prose: dict[str, Any]) -> tuple[str, str, list[str]]:
        etype = (req.engagement_type or "engagement").title()
        ctx = req.client_context or "the client"
        title = f"Statement of Work — {etype}"

        def bullets(items: list[str]) -> str:
            return "\n".join(f"- {i}" for i in items) or "- (to be defined)"

        objectives_md = prose["objectives_narrative"] or (
            "This engagement will deliver the objectives below."
        )
        objectives_md += "\n\n" + bullets(req.objectives)

        scope_md = prose["scope_description"] or "The engagement covers the scope items below."
        scope_md += "\n\n### In scope\n\n" + bullets(req.scope_items)

        all_assumptions = req.assumptions + [
            a for a in prose["assumptions_extra"] if a not in req.assumptions
        ]
        acceptance = prose["acceptance_criteria"] or [
            f"Delivery and sign-off of: {d}" for d in req.deliverables
        ]

        sections = [
            "Objectives", "Scope", "Deliverables", "Timeline & Milestones",
            "Pricing", "Assumptions", "Acceptance Criteria",
        ]
        markdown = (
            f"# {title}\n\n_{ctx}_\n\n"
            f"## Objectives\n\n{objectives_md}\n\n"
            f"## Scope\n\n{scope_md}\n\n"
            f"## Deliverables\n\n{bullets(req.deliverables)}\n\n"
            f"## Timeline & Milestones\n\n"
            f"{req.timeline_weeks}-week engagement.\n\n{bullets(req.milestones)}\n\n"
            f"## Pricing\n\nPricing model: **{req.pricing_model or 'to be agreed'}**.\n\n"
            f"## Assumptions\n\n{bullets(all_assumptions)}\n\n"
            f"## Acceptance Criteria\n\n{bullets(acceptance)}\n"
        )
        return title, markdown, sections


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
