"""AGENT-30 — Vendor Vetting (Module 31), Sonnet 4.6 tier.

The risk/approval counterpart to Benchmarks (Module 13): Benchmarks answers *which*
vendor performs best; this answers *are we allowed to use it and is it safe*. Both read
``vault/vendors/``; this one scores security posture (data handling, certifications,
training-on-customer-data, BAA) and records a team-wide approval status.

**Orchestration is mechanical** (AGENT-24 / AGENT-05 precedent): WORKER-20 computes the
risk tier + per-control results deterministically, and Sonnet is used for **one thing
only** — the risk narrative on the ``assess`` path, with a deterministic fallback.
``list`` / ``get`` / ``set_status`` never call the model.

Approval/vetting records persist as an **org-shared JSON sidecar** in the vault bucket
(``vendors/_vetting/{vendor_id}.json``) — a ``.json`` (not ``.md``), so the ReEmbed
pipeline ignores it, exactly like ``assets/_metadata/``. Team-wide approvals, no KB
pollution.

Operations (on ``op``):
  - ``list``       — vendors + risk/approval badges (default)
  - ``get``        — one vendor: profile + current vetting record
  - ``assess``     — WORKER-20 + one Sonnet narrative; persists the result to the sidecar
  - ``set_status`` — record approved | conditional | rejected (+ note) in the sidecar
"""

from __future__ import annotations

import json
import os
from typing import Any

from agents.lambdas.modules.agent_03_asset_library import _slug, _split_frontmatter
from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .base import ModuleAgent
from .worker_client import WorkerInvoker

AGENT_ID = "AGENT-30"
VENDORS_PREFIX = "vendors/"
VETTING_PREFIX = "vendors/_vetting/"
ASSET_LIBRARY_ROUTE = "/modules/asset-library"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}
_STATUSES = ("approved", "conditional", "rejected", "unvetted")

NARRATIVE_SYSTEM = """You write a short vendor risk note for an internal approval review, \
from a deterministic vetting result you are given (risk tier + per-control pass/gap/unknown). \
Write 2-3 sentences a delivery lead can act on: the overall risk, the gaps that matter most, \
and what to require before approving. Do not invent controls or facts beyond those provided. \
Be direct; no preamble, no bullet lists."""


def _norm(s: Any) -> str:
    return str(s or "").strip()


class VendorVettingAgent(ModuleAgent):
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
        if "vendor_id" not in args and args.get("id"):
            args = {**args, "vendor_id": args["id"]}
        op = args.get("op")
        if op == "assess":
            return self.run_tool("assess_vendor", lambda _u: self._assess(args))
        if op == "set_status":
            return self.run_tool("set_vendor_status", lambda _u: self._set_status(args))
        if op == "get" or (op is None and args.get("vendor_id")):
            return self.run_tool("get_vendor", lambda _u: self._get(args))
        return self.run_tool("list_vendors", lambda _u: self._list(args))

    # --- vendor corpus I/O -------------------------------------------------
    def _all_vendors(self) -> list[tuple[dict, str, str]]:
        """(frontmatter, body, key) for every vendor markdown file (excl. _vetting/)."""
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": VENDORS_PREFIX}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            keys.extend(
                o["Key"] for o in resp.get("Contents", [])
                if o["Key"].endswith(".md") and "/_vetting/" not in o["Key"]
            )
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
        out: list[tuple[dict, str, str]] = []
        for key in keys:
            fm, md = _split_frontmatter(self._read(key))
            out.append((fm, md, key))
        return out

    def _read(self, key: str) -> str:
        return self.s3.get_object(Bucket=self.vault_bucket, Key=key)["Body"].read().decode("utf-8")

    @staticmethod
    def _vendor_id(fm: dict, key: str) -> str:
        return str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md"))

    def _load_vendor(self, vendor_id: str) -> tuple[dict, str, str] | None:
        target = str(vendor_id)
        basename = f"/{target}.md"
        fallback: tuple[dict, str, str] | None = None
        for fm, body, key in self._all_vendors():
            if self._vendor_id(fm, key) == target:
                return fm, body, key
            if key.endswith(basename):
                fallback = (fm, body, key)
        return fallback

    # --- sidecar (org-shared, non-indexed) ---------------------------------
    def _sidecar_key(self, vendor_id: str) -> str:
        return f"{VETTING_PREFIX}{_slug(vendor_id)}.json"

    def _read_sidecar(self, vendor_id: str) -> dict:
        from botocore.exceptions import ClientError

        try:
            raw = self.s3.get_object(
                Bucket=self.vault_bucket, Key=self._sidecar_key(vendor_id)
            )["Body"].read()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _NOT_FOUND:
                return {"vendor_id": vendor_id, "approval_status": "unvetted"}
            raise
        except (KeyError, FileNotFoundError):
            return {"vendor_id": vendor_id, "approval_status": "unvetted"}
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return {"vendor_id": vendor_id, "approval_status": "unvetted"}

    def _write_sidecar(self, vendor_id: str, record: dict) -> None:
        self.s3.put_object(
            Bucket=self.vault_bucket, Key=self._sidecar_key(vendor_id),
            Body=json.dumps(record, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    # --- operations --------------------------------------------------------
    @staticmethod
    def _summary(fm: dict, key: str, sidecar: dict) -> dict[str, Any]:
        return {
            "vendor_id": VendorVettingAgent._vendor_id(fm, key),
            "category": str(fm.get("category", "")),
            "vendors_compared": [str(v) for v in (fm.get("vendors_compared") or [])],
            "last_verified": str(fm.get("last_verified", "")),
            "approval_status": str(sidecar.get("approval_status", "unvetted")),
            "risk_tier": sidecar.get("risk_tier"),
            "file_path": key,
        }

    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        category = _norm(args.get("category")).lower()
        out: list[dict[str, Any]] = []
        for fm, _body, key in self._all_vendors():
            if category and str(fm.get("category", "")).lower() != category:
                continue
            sidecar = self._read_sidecar(self._vendor_id(fm, key))
            out.append(self._summary(fm, key, sidecar))
        out.sort(key=lambda v: v["vendor_id"])
        return {"status": "ok", "vendors": out}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        vendor_id = _norm(args.get("vendor_id"))
        if not vendor_id:
            return {"status": "error", "message": "vendor_id is required."}
        loaded = self._load_vendor(vendor_id)
        if loaded is None:
            return {"status": "not_found", "vendor_id": vendor_id}
        fm, body, key = loaded
        sidecar = self._read_sidecar(self._vendor_id(fm, key))
        return {
            "status": "ok",
            "vendor": {
                "vendor_id": self._vendor_id(fm, key),
                "category": str(fm.get("category", "")),
                "vendors_compared": [str(v) for v in (fm.get("vendors_compared") or [])],
                "last_verified": str(fm.get("last_verified", "")),
                "frontmatter": fm,
                "body_markdown": body.strip(),
                "file_path": key,
            },
            "vetting": {
                "approval_status": str(sidecar.get("approval_status", "unvetted")),
                "risk_tier": sidecar.get("risk_tier"),
                "controls": sidecar.get("controls", []),
                "gaps": sidecar.get("gaps", []),
                "narrative": sidecar.get("narrative", ""),
                "note": sidecar.get("note", ""),
                "assessed_at": sidecar.get("assessed_at", ""),
            },
        }

    def _assess(self, args: dict[str, Any]) -> dict[str, Any]:
        vendor_id = _norm(args.get("vendor_id"))
        if not vendor_id:
            return {"status": "error", "message": "vendor_id is required."}
        loaded = self._load_vendor(vendor_id)
        if loaded is None:
            return {"status": "not_found", "vendor_id": vendor_id}
        fm, _body, key = loaded
        vid = self._vendor_id(fm, key)
        context_industry = _norm(args.get("context_industry"))
        data_sensitivity = _norm(args.get("data_sensitivity"))

        scored = self.workers.invoke(
            "WORKER-20",
            {"frontmatter": fm, "context_industry": context_industry,
             "data_sensitivity": data_sensitivity},
        )
        if scored.get("status") != "ok":
            return {"status": "error", "message": "Could not score the vendor."}
        risk_tier = scored.get("risk_tier", "medium")
        controls = scored.get("controls", [])
        gaps = scored.get("gaps", [])
        narrative = self._narrate(vid, risk_tier, gaps, context_industry, data_sensitivity)

        sidecar = self._read_sidecar(vid)
        sidecar.update({
            "vendor_id": vid,
            "risk_tier": risk_tier,
            "controls": controls,
            "gaps": gaps,
            "narrative": narrative,
            "context_industry": context_industry,
            "data_sensitivity": data_sensitivity,
            "assessed_at": _now_iso(),
        })
        self._write_sidecar(vid, sidecar)
        return {
            "status": "ok",
            "vendor_id": vid,
            "risk_tier": risk_tier,
            "controls": controls,
            "gaps": gaps,
            "approval_status": str(sidecar.get("approval_status", "unvetted")),
            "narrative": narrative,
        }

    def _set_status(self, args: dict[str, Any]) -> dict[str, Any]:
        vendor_id = _norm(args.get("vendor_id"))
        status = _norm(args.get("status")).lower()
        if not vendor_id:
            return {"status": "error", "message": "vendor_id is required."}
        if status not in _STATUSES:
            return {"status": "error", "message": f"status must be one of {_STATUSES}."}
        loaded = self._load_vendor(vendor_id)
        if loaded is None:
            return {"status": "not_found", "vendor_id": vendor_id}
        fm, _body, key = loaded
        vid = self._vendor_id(fm, key)

        sidecar = self._read_sidecar(vid)
        sidecar.update({
            "vendor_id": vid,
            "approval_status": status,
            "note": _norm(args.get("note")),
            "set_by": _norm(args.get("display_name")),
            "set_at": _now_iso(),
        })
        self._write_sidecar(vid, sidecar)
        return {"status": "ok", "vendor_id": vid, "approval_status": status}

    # --- LLM narrative (assess path only) ----------------------------------
    def _narrate(
        self, vendor_id: str, risk_tier: str, gaps: list[str], industry: str, sensitivity: str
    ) -> str:
        gaps_md = "\n".join(f"- {g}" for g in gaps) or "- (none)"
        user_text = (
            f"Vendor: {vendor_id}\n"
            f"Context: industry={industry or 'n/a'}, data sensitivity={sensitivity or 'n/a'}\n"
            f"Deterministic risk tier: {risk_tier}\n"
            f"Control gaps:\n{gaps_md}\n\n"
            f"Write the vendor risk note."
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
                    max_tokens=300,
                    usage=usage,
                )
            text = _extract_text(resp.get("output", {}).get("message", {}))
            if text:
                return text
        except Exception:  # noqa: BLE001 — deterministic fallback
            pass
        gap_names = ", ".join(gaps[:4]) or "no major control gaps"
        return (
            f"Overall risk: {risk_tier}. Key gaps to close before approval: {gap_names}. "
            "Require documented evidence for any unknown controls."
        )


def _now_iso() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()
