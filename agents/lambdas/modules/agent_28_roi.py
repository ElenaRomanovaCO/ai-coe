"""AGENT-28 — AI Project ROI Calculator (Module 29), Sonnet 4.6 tier.

Takes an AI project's cost and value drivers and returns a defensible ROI estimate —
total cost, annual value, net value, ROI %, and payback period — plus a short
business-case narrative.

**The numbers are computed in Python, never by the LLM** (:func:`compute`), following the
AGENT-05 precedent (``vault/decisions/agent-05-orchestration.md``): a deterministic core
plus **exactly one** Sonnet call that writes the narrative from the computed figures, with
a templated deterministic fallback if Bedrock fails.

Results are engagement-specific and client-financial, so they are persisted to the
**sessions** bucket (``roi/{display_name}/{id}.json``) and never to the vault — they must
not enter the searchable knowledge base. ``get`` / ``list`` read them back.

Operations (on ``op``):
  - ``calculate`` — compute + narrate + persist (default)
  - ``get``       — one saved result
  - ``list``      — the caller's saved results
"""

from __future__ import annotations

import json
import os
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

AGENT_ID = "AGENT-28"
ROI_PREFIX = "roi/"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}

NARRATIVE_SYSTEM = """You write a short, candid business case for an AI project from \
figures that have ALREADY been computed deterministically. You are given the project, \
its costs, its expected annual value, the ROI %, and the payback period. Write 2-3 \
short paragraphs a delivery lead can put in front of a sponsor: what it costs, what it \
returns, how fast it pays back, and the main caveat. Use ONLY the numbers provided — do \
not invent or recompute figures. Be direct; no preamble, no bullet lists."""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _f(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


class RoiRequest(BaseModel):
    project_name: str = ""
    industry: str = ""
    build_cost_usd: float = 0
    run_cost_usd_yr: float = 0
    team_size: int = 0
    duration_weeks: int = 0
    hours_saved_yr: float = 0
    loaded_hourly_rate_usd: float = 0
    revenue_uplift_usd_yr: float = 0
    other_benefit_usd_yr: float = 0
    horizon_years: int = 3
    display_name: str = ""


class RoiResult(BaseModel):
    total_cost_usd: float
    annual_value_usd: float
    net_value_usd: float
    roi_pct: float
    payback_months: float | None
    narrative: str = ""


def compute(req: RoiRequest) -> RoiResult:
    """Deterministic financial model. No LLM. Same inputs → same numbers."""
    horizon = max(1, int(req.horizon_years or 1))
    total_cost = round(_f(req.build_cost_usd) + _f(req.run_cost_usd_yr) * horizon, 2)
    annual_value = round(
        _f(req.hours_saved_yr) * _f(req.loaded_hourly_rate_usd)
        + _f(req.revenue_uplift_usd_yr)
        + _f(req.other_benefit_usd_yr),
        2,
    )
    net_value = round(annual_value * horizon - total_cost, 2)
    roi_pct = round((net_value / total_cost) * 100, 1) if total_cost > 0 else 0.0

    # Payback = one-time build cost / annual net cash flow (value minus annual run cost).
    annual_net_cash = annual_value - _f(req.run_cost_usd_yr)
    if annual_net_cash > 0 and _f(req.build_cost_usd) > 0:
        payback_months = round(_f(req.build_cost_usd) / annual_net_cash * 12, 1)
    elif _f(req.build_cost_usd) <= 0 and annual_net_cash > 0:
        payback_months = 0.0
    else:
        payback_months = None  # never pays back at these figures

    return RoiResult(
        total_cost_usd=total_cost,
        annual_value_usd=annual_value,
        net_value_usd=net_value,
        roi_pct=roi_pct,
        payback_months=payback_months,
    )


class RoiCalculatorAgent(ModuleAgent):
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
        if "roi_id" not in args and args.get("id"):
            args = {**args, "roi_id": args["id"]}
        op = args.get("op")
        if op == "get" or (op is None and args.get("roi_id")):
            return self.run_tool("get_roi", lambda _u: self._get(args))
        if op == "list":
            return self.run_tool("list_roi", lambda _u: self._list(args))
        return self.run_tool("calculate_roi", lambda _u: self._calculate(args))

    # --- state I/O (sessions only — never vault) ---------------------------
    def _state_key(self, display_name: str, roi_id: str) -> str:
        return f"{ROI_PREFIX}{_slug(display_name)}/{roi_id}.json"

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

    def _save(self, state: dict) -> None:
        self.s3.put_object(
            Bucket=self.sessions_bucket,
            Key=self._state_key(state["display_name"], state["roi_id"]),
            Body=json.dumps(state, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    # --- operations --------------------------------------------------------
    def _calculate(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        req = RoiRequest.model_validate({**args, "display_name": display_name})
        result = compute(req)
        result.narrative = self._narrate(req, result)

        roi_id = "roi-" + uuid.uuid4().hex[:12]
        created_at = _now_iso()
        state = {
            "roi_id": roi_id,
            "display_name": display_name,
            "created_at": created_at,
            "inputs": req.model_dump(),
            "result": result.model_dump(),
        }
        self._save(state)
        return {"status": "ok", "roi_id": roi_id, "created_at": created_at,
                "inputs": req.model_dump(), "result": result.model_dump()}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        roi_id = _norm(args.get("roi_id"))
        if not roi_id:
            return {"status": "error", "message": "roi_id is required."}
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=ROI_PREFIX)
        suffix = f"/{roi_id}.json"
        for o in resp.get("Contents", []):
            if o["Key"].endswith(suffix):
                state = self._read_json(o["Key"])
                if state:
                    return {"status": "ok", **state}
        return {"status": "not_found", "roi_id": roi_id}

    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        prefix = f"{ROI_PREFIX}{_slug(display_name)}/"
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=prefix)
        out: list[dict] = []
        for o in resp.get("Contents", []):
            if not o["Key"].endswith(".json"):
                continue
            state = self._read_json(o["Key"])
            if state:
                out.append({
                    "roi_id": state["roi_id"],
                    "project_name": state.get("inputs", {}).get("project_name", ""),
                    "industry": state.get("inputs", {}).get("industry", ""),
                    "roi_pct": state.get("result", {}).get("roi_pct", 0),
                    "payback_months": state.get("result", {}).get("payback_months"),
                    "created_at": state.get("created_at", ""),
                })
        out.sort(key=lambda r: r["created_at"], reverse=True)
        return {"status": "ok", "results": out}

    # --- narrative (the one LLM call; deterministic fallback) --------------
    def _narrate(self, req: RoiRequest, result: RoiResult) -> str:
        payback = (
            f"{result.payback_months:.1f} months" if result.payback_months is not None
            else "does not pay back within the horizon"
        )
        user_text = (
            f"Project: {req.project_name or 'AI project'}"
            + (f" ({req.industry})" if req.industry else "")
            + f"\nHorizon: {req.horizon_years} years\n"
            f"Total cost: ${result.total_cost_usd:,.0f}\n"
            f"Expected annual value: ${result.annual_value_usd:,.0f}\n"
            f"Net value over horizon: ${result.net_value_usd:,.0f}\n"
            f"ROI: {result.roi_pct:.1f}%\n"
            f"Payback: {payback}\n\n"
            f"Write the business case."
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
                    max_tokens=500,
                    usage=usage,
                )
            text = _extract_text(resp.get("output", {}).get("message", {}))
            if text:
                return text
        except Exception:  # noqa: BLE001 — fall back to a templated business case
            pass
        return self._fallback_narrative(req, result, payback)

    @staticmethod
    def _fallback_narrative(req: RoiRequest, result: RoiResult, payback: str) -> str:
        name = req.project_name or "This AI project"
        verdict = (
            "a strong return" if result.roi_pct >= 100
            else "a positive return" if result.roi_pct > 0
            else "a negative return at these inputs"
        )
        return (
            f"{name} is estimated to cost ${result.total_cost_usd:,.0f} over "
            f"{req.horizon_years} years and to generate about ${result.annual_value_usd:,.0f} of "
            f"value per year, for a net of ${result.net_value_usd:,.0f} — {verdict} "
            f"({result.roi_pct:.1f}% ROI), with payback in {payback}. "
            "Treat these as planning estimates; validate the value drivers (hours saved, "
            "uplift) against a baseline before committing."
        )


def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()
