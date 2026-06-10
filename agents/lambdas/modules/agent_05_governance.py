"""AGENT-05 — Governance & Risk Checker (Module 4), Sonnet 4.6 tier.

Given an engagement context (industry, geography, data types, AI use-case type),
produces a pre-delivery risk checklist with regulation links and an executive
summary, and saves the review to the vault.

**Orchestration is mechanical**, not an LLM tool-loop (decision
``vault/decisions/agent-05-orchestration.md``): the two deterministic workers run in
a fixed pipeline — WORKER-04 (regulation_finder) → WORKER-05 (checklist_generator) —
exactly like AGENT-02 sequences its workers. The Sonnet model is used for **one
thing only**: writing the 3-4 sentence executive summary from the already-built
checklist. The LLM never decides the checklist or touches the risk logic, so the
determinism guardrail is satisfied and the risk output stays fully testable. If the
summary call fails, a deterministic fallback summary is used.

No Bedrock guardrail is applied (the module-agents role lacks ``ApplyGuardrail`` —
see ``vault/decisions/asset-panel-no-guardrail.md``); the summary prompt is grounded
in the deterministic checklist, so the risk is low.

Operations (on ``op``):
  - ``check`` — run the pipeline, save the review, return the result (default)
  - ``get``   — fetch a saved review by ``review_id``
  - ``list``  — list a user's reviews
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import ClientError

from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .base import ModuleAgent
from .worker_client import WorkerInvoker

AGENT_ID = "AGENT-05"
GOVERNANCE_ROUTE = "/modules/governance"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}
_SLUG_UNSAFE = re.compile(r"[^a-zA-Z0-9._-]+")
_REVIEW_PREFIX = "reviews/governance/"


def _slug(name: str) -> str:
    s = _SLUG_UNSAFE.sub("-", (name or "").strip()).strip("-").lower()
    return s or "anon"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


SUMMARY_SYSTEM = """You write a concise executive summary for a pre-delivery AI \
governance review. You are given the engagement context and a checklist of risk/control \
items that has already been compiled deterministically. Write 3-4 sentences that a \
delivery lead can read at a glance: what regimes apply, the most critical actions, and \
the overall risk posture. Do not invent regulations or items beyond those provided. Be \
direct and plain-spoken; no preamble, no bullet points."""


class GovernanceAgent(ModuleAgent):
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
        worker_invoker: WorkerInvoker | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.region = region
        self._s3 = s3
        self.bedrock_client = bedrock_client or BedrockClient(client=bedrock)
        self.workers = worker_invoker or WorkerInvoker(region=region)

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        op = args.get("op", "check")
        if op == "check":
            missing = [
                k for k in ("industry", "geography", "ai_use_case_type") if not args.get(k)
            ]
            if missing:
                return {"status": "error", "message": f"Missing required: {', '.join(missing)}."}
            return self.run_tool("governance_check", lambda _u: self._check(args))
        if op == "get":
            return self.run_tool("get_review", lambda _u: self._get(args.get("review_id")))
        if op == "list":
            return self.run_tool("list_reviews", lambda _u: self._list(args.get("display_name")))
        return {"status": "error", "message": f"Unknown op '{op}'."}

    # --- pipeline ----------------------------------------------------------
    def _check(self, args: dict[str, Any]) -> dict[str, Any]:
        data_types = list(args.get("data_types") or [])
        context = {
            "industry": args.get("industry", ""),
            "geography": args.get("geography", ""),
            "data_types": data_types,
            "ai_use_case_type": args.get("ai_use_case_type", ""),
            "engagement_context": args.get("engagement_context") or "",
        }

        regs = self.workers.invoke(
            "WORKER-04",
            {
                "industry": context["industry"],
                "geography": context["geography"],
                "data_types": data_types,
                "ai_use_case_type": context["ai_use_case_type"],
            },
        )
        if regs.get("status") != "ok":
            return {"status": "error", "message": "Could not match regulations."}
        regulations = regs.get("regulations", [])

        chk = self.workers.invoke(
            "WORKER-05",
            {"regulations": regulations, "engagement_context": context},
        )
        if chk.get("status") != "ok":
            return {"status": "error", "message": "Could not generate the checklist."}
        checklist = chk.get("checklist", [])

        summary = self._summarize(context, regulations, checklist)

        review_id = "gov-" + uuid.uuid4().hex[:12]
        display_name = args.get("display_name") or "anon"
        created_at = _now_iso()
        vault_path = self._write_review(
            review_id, display_name, created_at, context, regulations, checklist, summary
        )

        result = {
            "review_id": review_id,
            "display_name": display_name,
            "created_at": created_at,
            "context": context,
            "regulations": regulations,
            "checklist": checklist,
            "summary": summary,
            "vault_file_path": vault_path,
        }
        self._save_state(result)
        return {"status": "ok", **result}

    # --- LLM summary (the only model call) ---------------------------------
    def _summarize(self, context: dict, regulations: list[dict], checklist: list[dict]) -> str:
        reg_names = ", ".join(r.get("name", r.get("id", "")) for r in regulations) or "none matched"
        top = [c for c in checklist if c.get("priority") in ("critical", "high")][:6]
        items_md = "\n".join(f"- [{c['priority']}] {c['statement']}" for c in top) or "- (none)"
        user_text = (
            f"Engagement context:\n"
            f"- Industry: {context.get('industry')}\n"
            f"- Geography: {context.get('geography')}\n"
            f"- Data types: {', '.join(context.get('data_types') or []) or 'unspecified'}\n"
            f"- AI use case: {context.get('ai_use_case_type')}\n\n"
            f"Regulations matched: {reg_names}\n\n"
            f"Highest-priority checklist items:\n{items_md}\n\n"
            f"Write the executive summary."
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
                    system=SUMMARY_SYSTEM,
                    max_tokens=400,
                    usage=usage,
                )
            text = _extract_text(resp.get("output", {}).get("message", {}))
            if text:
                return text
        except Exception:  # noqa: BLE001 — fall back to a deterministic summary
            pass
        return self._fallback_summary(context, regulations, checklist)

    def _fallback_summary(
        self, context: dict, regulations: list[dict], checklist: list[dict]
    ) -> str:
        names = ", ".join(r.get("name", r.get("id", "")) for r in regulations[:3])
        criticals = sum(1 for c in checklist if c.get("priority") == "critical")
        return (
            f"This {context.get('industry') or 'engagement'} use case in "
            f"{context.get('geography') or 'the target geography'} triggers "
            f"{len(regulations)} relevant regulation(s)"
            f"{f' (notably {names})' if names else ''}. "
            f"The review produced {len(checklist)} checklist item(s), "
            f"{criticals} of them critical. Address the critical and high-priority items "
            f"before delivery and document the controls for audit."
        )

    # --- vault + state I/O -------------------------------------------------
    def _write_review(
        self,
        review_id: str,
        display_name: str,
        created_at: str,
        context: dict,
        regulations: list[dict],
        checklist: list[dict],
        summary: str,
    ) -> str:
        ts_key = created_at.replace(":", "-")
        key = f"{_REVIEW_PREFIX}{_slug(display_name)}/{ts_key}.md"
        reg_md = (
            "\n".join(f"- {r.get('name')} (`{r.get('id')}`)" for r in regulations) or "- (none)"
        )
        def _chk_line(c: dict) -> str:
            line = f"- **[{c.get('priority')}]** {c.get('statement')}"
            links = c.get("regulation_links") or []
            if links:
                line += f"  \n  _Links:_ {', '.join(links)}"
            return line

        chk_md = "\n".join(_chk_line(c) for c in checklist) or "- (none)"
        dt_csv = ", ".join(context.get("data_types") or [])
        body = (
            f"---\n"
            f"id: {review_id}\n"
            f"type: governance-review\n"
            f"display_name: {display_name}\n"
            f"industry: {context.get('industry') or ''}\n"
            f"geography: {context.get('geography') or ''}\n"
            f"data_types: [{dt_csv}]\n"
            f"ai_use_case_type: {context.get('ai_use_case_type') or ''}\n"
            f"created_at: {created_at}\n"
            f"---\n\n"
            f"# Governance & Risk Review\n\n"
            f"{summary}\n\n"
            f"## Regulations considered\n\n{reg_md}\n\n"
            f"## Risk checklist\n\n{chk_md}\n"
        )
        self.s3.put_object(
            Bucket=self.vault_bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="text/markdown",
        )
        return key

    def _state_key(self, display_name: str, review_id: str) -> str:
        return f"{_REVIEW_PREFIX}{_slug(display_name)}/{review_id}.json"

    def _save_state(self, result: dict) -> None:
        key = self._state_key(result["display_name"], result["review_id"])
        self.s3.put_object(
            Bucket=self.sessions_bucket,
            Key=key,
            Body=json.dumps(result, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    def _find_state_keys(self, review_id: str) -> list[str]:
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=_REVIEW_PREFIX)
        suffix = f"/{review_id}.json"
        return [o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(suffix)]

    def _get(self, review_id: str | None) -> dict[str, Any]:
        if not review_id:
            return {"status": "error", "message": "review_id is required."}
        for key in self._find_state_keys(review_id):
            try:
                raw = self.s3.get_object(Bucket=self.sessions_bucket, Key=key)["Body"].read()
            except ClientError as exc:
                if exc.response.get("Error", {}).get("Code") in _NOT_FOUND:
                    continue
                raise
            except (KeyError, FileNotFoundError):
                continue
            return {"status": "ok", **json.loads(raw)}
        return {"status": "not_found", "review_id": review_id}

    def _list(self, display_name: str | None) -> dict[str, Any]:
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        prefix = f"{_REVIEW_PREFIX}{_slug(display_name)}/"
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=prefix)
        out = []
        for o in resp.get("Contents", []):
            if not o["Key"].endswith(".json"):
                continue
            raw = self.s3.get_object(Bucket=self.sessions_bucket, Key=o["Key"])["Body"].read()
            st = json.loads(raw)
            out.append(
                {
                    "review_id": st.get("review_id"),
                    "industry": (st.get("context") or {}).get("industry"),
                    "geography": (st.get("context") or {}).get("geography"),
                    "ai_use_case_type": (st.get("context") or {}).get("ai_use_case_type"),
                    "created_at": st.get("created_at"),
                    "item_count": len(st.get("checklist") or []),
                }
            )
        out.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return {"status": "ok", "reviews": out}


def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()
