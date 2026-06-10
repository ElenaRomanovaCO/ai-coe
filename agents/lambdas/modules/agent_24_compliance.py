"""AGENT-24 — Global AI Regulation & Compliance Tracker (Module 25), Sonnet 4.6 tier.

Lets a user browse the seeded regulations in ``vault/regs/`` (filter by geography,
industry, status, use-case type), open one to read it plus a plain-language summary,
or apply a regulation to a specific use case to get an applicability checklist.

**Orchestration is mechanical**, following the AGENT-05/20 precedent
(``vault/decisions/agent-05-orchestration.md``): the two deterministic workers do the
analysis, and the Sonnet model is used for **one thing only** — the plain-language
narrative on the ``apply`` path — with a deterministic fallback if it fails. ``list``
and ``get`` never call the model.

  - WORKER-12 reg_summarizer        — reg markdown → summary + key requirements
  - WORKER-13 applicability_checker  — reg + use case → per-clause applicability

No Bedrock guardrail is applied (the module-agents role lacks ``ApplyGuardrail`` — see
``vault/decisions/asset-panel-no-guardrail.md``); the narrative prompt is grounded in
the deterministic applicability result, so the risk is low.

Operations (on ``op``):
  - ``list``  — filter the regulation corpus, return summaries (default)
  - ``get``   — one regulation's body + frontmatter + WORKER-12 summary
  - ``apply`` — WORKER-13 applicability + one-shot Sonnet narrative (no persistence)
"""

from __future__ import annotations

import os
import re
from typing import Any

from agents.lambdas.modules.agent_03_asset_library import _split_frontmatter
from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .base import ModuleAgent
from .worker_client import WorkerInvoker

AGENT_ID = "AGENT-24"
COMPLIANCE_ROUTE = "/modules/compliance-tracker"
REGS_PREFIX = "regs/"

# Normalize free-text geography to the `geo` values used in reg frontmatter. Mirrors
# WORKER-04's aliases (kept local so the agent has no hard dep on a worker's internals).
_GEO_ALIASES: dict[str, str] = {
    "eu": "eu",
    "europe": "eu",
    "european union": "eu",
    "us": "us-federal",
    "usa": "us-federal",
    "united states": "us-federal",
    "us-federal": "us-federal",
    "federal": "us-federal",
    "california": "us-state-ca",
    "ca": "us-state-ca",
    "us-ca": "us-state-ca",
    "us-state-ca": "us-state-ca",
}


def _norm_geo(geography: str) -> str:
    g = (geography or "").strip().lower()
    return _GEO_ALIASES.get(g, g)


NARRATIVE_SYSTEM = """You write a short, plain-language note on how one AI regulation \
applies to a specific use case. You are given the regulation name, the use case, and a \
clause-by-clause applicability assessment that has already been compiled \
deterministically. Write 3-4 sentences a delivery lead can act on: whether the \
regulation applies, which clauses matter most, and what to do first. Do not invent \
clauses or obligations beyond those provided. Be direct; no preamble, no bullet points."""


class ComplianceAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.SONNET_4_6

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        region: str = lib_models.REGION,
        s3: Any = None,
        bedrock: Any = None,
        bedrock_client: BedrockClient | None = None,
        worker_invoker: WorkerInvoker | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
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
        # Liberal aliasing: the orchestrator/web may send ``id`` for ``reg_id``.
        if "reg_id" not in args and args.get("id"):
            args = {**args, "reg_id": args["id"]}
        op = args.get("op")
        if op == "get" or (op is None and args.get("reg_id")):
            return self.run_tool("get_regulation", lambda _u: self._get(args))
        if op == "apply":
            return self.run_tool("apply_regulation", lambda _u: self._apply(args))
        return self.run_tool("list_regulations", lambda _u: self._list(args))

    # --- reg corpus I/O ----------------------------------------------------
    def _all_regs(self) -> list[tuple[dict, str, str]]:
        """(frontmatter, body, key) for every regulation markdown file."""
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": REGS_PREFIX}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            keys.extend(o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(".md"))
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")

        out: list[tuple[dict, str, str]] = []
        for key in keys:
            body = self.s3.get_object(Bucket=self.vault_bucket, Key=key)["Body"].read()
            fm, md = _split_frontmatter(body.decode("utf-8"))
            out.append((fm, md, key))
        return out

    @staticmethod
    def _reg_id(fm: dict, key: str) -> str:
        return str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md"))

    @staticmethod
    def _summary_of(fm: dict, body: str, key: str) -> dict[str, Any]:
        return {
            "id": ComplianceAgent._reg_id(fm, key),
            "name": str(fm.get("name", "")),
            "geo": str(fm.get("geo", "")),
            "status": str(fm.get("status", "")),
            "effective_date": str(fm.get("effective_date", "")),
            "risk_tier": "" if fm.get("risk_tier") is None else str(fm.get("risk_tier")),
            "industry_scope": [str(s) for s in (fm.get("industry_scope") or [])],
            "tags": [str(t) for t in (fm.get("tags") or [])],
            "file_path": key,
        }

    def _load_reg(self, reg_id: str) -> tuple[dict, str, str] | None:
        """Resolve a reg by frontmatter id (basename fallback), like AGENT-03 get_asset."""
        target = str(reg_id)
        basename = f"/{target}.md"
        fallback: tuple[dict, str, str] | None = None
        for fm, body, key in self._all_regs():
            if self._reg_id(fm, key) == target:
                return fm, body, key
            if key.endswith(basename):
                fallback = (fm, body, key)
        return fallback

    # --- operations --------------------------------------------------------
    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        geo = _norm_geo(args.get("geography") or "")
        industry = (args.get("industry") or "").strip().lower()
        status = (args.get("status") or "").strip().lower()
        use_case_type = (args.get("use_case_type") or "").strip().lower()
        query = (args.get("query") or "").strip().lower()
        uc_tokens = {t for t in re.split(r"[^a-z0-9]+", use_case_type) if len(t) >= 3}

        out: list[dict[str, Any]] = []
        for fm, body, key in self._all_regs():
            scope = [str(s).lower() for s in (fm.get("industry_scope") or [])]
            tags = [str(t).lower() for t in (fm.get("tags") or [])]
            reg_geo = str(fm.get("geo") or "").lower()
            reg_status = str(fm.get("status") or "").lower()
            name = str(fm.get("name") or "").lower()

            if geo and reg_geo != geo:
                continue
            if industry and industry not in scope and "cross-industry" not in scope:
                continue
            if status and reg_status != status:
                continue
            if uc_tokens:
                hay = set(tags) | set(re.split(r"[^a-z0-9]+", f"{name} {body.lower()}"))
                if not (uc_tokens & hay):
                    continue
            if query and query not in f"{name} {' '.join(tags)}":
                continue
            out.append(self._summary_of(fm, body, key))

        out.sort(key=lambda r: (r["geo"], r["name"]))
        return {"status": "ok", "regulations": out}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        reg_id = args.get("reg_id")
        if not reg_id:
            return {"status": "error", "message": "reg_id is required."}
        loaded = self._load_reg(reg_id)
        if loaded is None:
            return {"status": "not_found", "reg_id": reg_id, "message": "No such regulation."}
        fm, body, key = loaded

        summary = self.workers.invoke("WORKER-12", {"frontmatter": fm, "body": body})
        if summary.get("status") != "ok":
            summary = {"summary": "", "key_requirements": [], "sector_implications": []}

        regulation = {
            "id": self._reg_id(fm, key),
            "name": str(fm.get("name", "")),
            "frontmatter": fm,
            "body_markdown": body.strip(),
            "file_path": key,
        }
        return {
            "status": "ok",
            "regulation": regulation,
            "summary": {
                "summary": summary.get("summary", ""),
                "key_requirements": summary.get("key_requirements", []),
                "sector_implications": summary.get("sector_implications", []),
            },
        }

    def _apply(self, args: dict[str, Any]) -> dict[str, Any]:
        reg_id = args.get("reg_id")
        use_case = (args.get("use_case_description") or "").strip()
        if not reg_id or not use_case:
            return {"status": "error", "message": "reg_id and use_case_description are required."}
        loaded = self._load_reg(reg_id)
        if loaded is None:
            return {"status": "not_found", "reg_id": reg_id, "message": "No such regulation."}
        fm, body, key = loaded
        reg_name = str(fm.get("name", ""))

        result = self.workers.invoke(
            "WORKER-13",
            {
                "regulation": {"id": self._reg_id(fm, key), "name": reg_name,
                               "frontmatter": fm, "body": body},
                "use_case_description": use_case,
                "industry": args.get("industry", ""),
                "geography": args.get("geography", ""),
            },
        )
        if result.get("status") != "ok":
            return {"status": "error", "message": "Could not assess applicability."}
        applicability = result.get("applicability", [])
        overall = result.get("overall", "")

        narrative = self._narrate(reg_name, use_case, applicability, overall)
        return {
            "status": "ok",
            "regulation": {"id": self._reg_id(fm, key), "name": reg_name},
            "use_case_description": use_case,
            "regulation_applies": result.get("regulation_applies", False),
            "applicability": applicability,
            "narrative": narrative,
        }

    # --- LLM narrative (the only model call) -------------------------------
    def _narrate(
        self, reg_name: str, use_case: str, applicability: list[dict], overall: str
    ) -> str:
        applies = [a for a in applicability if a.get("applies")]
        na = [a for a in applicability if not a.get("applies")]
        applies_md = "\n".join(f"- {a['clause']}: {a['reason']}" for a in applies) or "- (none)"
        na_md = "\n".join(f"- {a['clause']}" for a in na) or "- (none)"
        user_text = (
            f"Regulation: {reg_name}\n"
            f"Use case: {use_case}\n\n"
            f"Deterministic verdict: {overall}\n\n"
            f"Applicable clauses:\n{applies_md}\n\n"
            f"Not applicable:\n{na_md}\n\n"
            f"Write the plain-language note."
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
                    system=NARRATIVE_SYSTEM,
                    max_tokens=400,
                    usage=usage,
                )
            text = _extract_text(resp.get("output", {}).get("message", {}))
            if text:
                return text
        except Exception:  # noqa: BLE001 — fall back to the deterministic verdict
            pass
        applies_names = ", ".join(a["clause"] for a in applies[:4]) or "no specific clauses"
        return f"{overall} Focus first on: {applies_names}."


def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()
