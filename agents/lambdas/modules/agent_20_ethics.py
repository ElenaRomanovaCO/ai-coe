"""AGENT-20 — AI Ethics & Bias Checker (Module 21), Sonnet 4.6 tier.

Given a use case (data types, affected populations, decision type, geography,
industry), produces a structured ethics review across five areas — bias risks,
fairness considerations, explainability requirements, human-oversight
recommendations, and regulatory-tier mapping — and saves it to the vault.

**Mechanical orchestration**, per ``vault/decisions/agent-05-orchestration.md``:
the two deterministic workers run in a fixed pipeline — WORKER-08 (bias_analyzer) →
WORKER-09 (regulation_mapper) — and the three remaining structured areas (fairness,
explainability, human oversight) are derived deterministically here. The Sonnet model
is used for **one thing only**: the executive summary (deterministic fallback on
failure). The LLM never produces the structured findings, so the review stays
reproducible and testable. No Bedrock guardrail is applied (the module-agents role
lacks ``ApplyGuardrail`` — see ``vault/decisions/asset-panel-no-guardrail.md``).

Operations (on ``op``): ``check`` (run + save, default), ``get`` (by review_id),
``list`` (a user's reviews).
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

AGENT_ID = "AGENT-20"
ETHICS_ROUTE = "/modules/ethics-checker"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}
_SLUG_UNSAFE = re.compile(r"[^a-zA-Z0-9._-]+")
_REVIEW_PREFIX = "reviews/ethics/"

_PROTECTED = {
    "minority",
    "minorities",
    "race",
    "racial",
    "ethnic",
    "ethnicity",
    "immigrant",
    "women",
    "woman",
    "female",
    "gender",
    "lgbtq",
    "disabled",
    "disability",
    "elderly",
    "senior",
    "low-income",
    "poor",
    "veteran",
    "religious",
    "rural",
    "children",
    "minors",
}

SUMMARY_SYSTEM = """You write a concise executive summary for a pre-deployment AI \
ethics review. You are given the use case and a structured review (bias risks, \
fairness, explainability, human oversight, and regulatory tier) that has already been \
compiled deterministically. Write 3-4 sentences a delivery lead can read at a glance: \
the overall ethical risk posture, the regulatory tier, and the few most important \
actions. Do not invent risks or requirements beyond those provided. Be direct and \
plain-spoken; no preamble, no bullet points."""


def _slug(name: str) -> str:
    s = _SLUG_UNSAFE.sub("-", (name or "").strip()).strip("-").lower()
    return s or "anon"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _tokens(values: list[str]) -> set[str]:
    out: set[str] = set()
    for v in values:
        out.update(t for t in re.split(r"[^a-z0-9]+", str(v).lower()) if t)
    return out


class EthicsAgent(ModuleAgent):
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
            if not args.get("use_case"):
                return {"status": "error", "message": "use_case is required."}
            return self.run_tool("ethics_check", lambda _u: self._check(args))
        if op == "get":
            return self.run_tool("get_review", lambda _u: self._get(args.get("review_id")))
        if op == "list":
            return self.run_tool("list_reviews", lambda _u: self._list(args.get("display_name")))
        return {"status": "error", "message": f"Unknown op '{op}'."}

    # --- pipeline ----------------------------------------------------------
    def _check(self, args: dict[str, Any]) -> dict[str, Any]:
        data_types = list(args.get("data_types") or [])
        populations = list(args.get("affected_populations") or [])
        decision_type = str(args.get("decision_type") or "assisted").strip().lower()
        context = {
            "use_case": args.get("use_case", ""),
            "data_types": data_types,
            "affected_populations": populations,
            "decision_type": decision_type,
            "geography": args.get("geography", ""),
            "industry": args.get("industry", ""),
        }

        bias = self.workers.invoke(
            "WORKER-08",
            {
                "use_case": context["use_case"],
                "data_types": data_types,
                "affected_populations": populations,
                "decision_type": decision_type,
            },
        )
        if bias.get("status") != "ok":
            return {"status": "error", "message": "Bias analysis failed."}
        bias_risks = bias.get("bias_risks", [])

        regmap = self.workers.invoke(
            "WORKER-09",
            {
                "use_case": context["use_case"],
                "decision_type": decision_type,
                "geography": context["geography"],
                "industry": context["industry"],
                "data_types": data_types,
            },
        )
        if regmap.get("status") != "ok":
            return {"status": "error", "message": "Regulation mapping failed."}
        frameworks = regmap.get("frameworks", [])
        regulatory_tier = regmap.get("regulatory_tier", {})

        fairness = self._fairness(context, populations)
        explainability = self._explainability(decision_type, frameworks)
        oversight = self._oversight(decision_type)

        summary = self._summarize(
            context, bias_risks, frameworks, fairness, explainability, oversight
        )

        review_id = "eth-" + uuid.uuid4().hex[:12]
        display_name = args.get("display_name") or "anon"
        created_at = _now_iso()
        vault_path = self._write_review(
            review_id,
            display_name,
            created_at,
            context,
            bias_risks,
            fairness,
            explainability,
            oversight,
            frameworks,
            summary,
        )

        result = {
            "review_id": review_id,
            "display_name": display_name,
            "created_at": created_at,
            "context": context,
            "bias_risks": bias_risks,
            "fairness_considerations": fairness,
            "explainability_requirements": explainability,
            "human_oversight_recommendations": oversight,
            "regulatory_tier": regulatory_tier,
            "frameworks": frameworks,
            "summary": summary,
            "vault_file_path": vault_path,
        }
        self._save_state(result)
        return {"status": "ok", **result}

    # --- deterministic derivations (the 3 non-worker structured areas) ------
    def _fairness(self, context: dict, populations: list[str]) -> list[str]:
        has_protected = bool(_tokens(populations) & _PROTECTED)
        items = [
            "Measure model performance separately for each affected subgroup, not just "
            "in aggregate.",
            "Test for disparate impact and define an acceptable fairness threshold before launch.",
        ]
        if has_protected:
            items.append(
                "Protected or vulnerable groups are in scope — agree fairness metrics with "
                "stakeholders and document the trade-offs chosen."
            )
        return items

    def _explainability(self, decision_type: str, frameworks: list[dict]) -> list[str]:
        high = decision_type == "automated" or any(f.get("tier") == "high" for f in frameworks)
        items = [
            "Provide a plain-language reason for each decision the system produces.",
            "Maintain a model card documenting training data, intended use, and known limitations.",
        ]
        if high:
            items.append(
                "High-risk/automated: provide feature-level explanations and a durable decision "
                "log sufficient for audit and appeal."
            )
        return items

    def _oversight(self, decision_type: str) -> list[str]:
        if decision_type == "automated":
            return [
                "Require human review for any adverse or high-impact decision before it "
                "takes effect.",
                "Provide an override mechanism and monitor override rates for rubber-stamping.",
                "Define an escalation path and an owner accountable for the system's decisions.",
            ]
        if decision_type == "assisted":
            return [
                "Train reviewers on automation bias and their authority to overrule the model.",
                "Surface model confidence so reviewers can calibrate trust.",
                "Define an escalation path for contested cases.",
            ]
        return [
            "Frame outputs as advisory only; keep a human as the sole decision-maker.",
            "Periodically audit whether advisory outputs are de facto driving decisions.",
        ]

    # --- LLM summary (the only model call) ---------------------------------
    def _summarize(
        self,
        context: dict,
        bias_risks: list[dict],
        frameworks: list[dict],
        fairness: list[str],
        explainability: list[str],
        oversight: list[str],
    ) -> str:
        tier = next((f.get("tier") for f in frameworks if f.get("framework") == "EU AI Act"), "?")
        fw = ", ".join(f"{f.get('framework')}={f.get('tier')}" for f in frameworks) or "none"
        top_bias = [r for r in bias_risks if r.get("severity") in ("critical", "high")][:5]
        bias_md = (
            "\n".join(f"- [{r['severity']}] {r['description']}" for r in top_bias) or "- (none)"
        )
        user_text = (
            f"Use case: {context.get('use_case')}\n"
            f"Decision type: {context.get('decision_type')}\n"
            f"Industry/Geography: {context.get('industry')} / {context.get('geography')}\n"
            f"Affected populations: "
            f"{', '.join(context.get('affected_populations') or []) or 'unspecified'}\n"
            f"EU AI Act tier: {tier}; frameworks: {fw}\n\n"
            f"Highest-severity bias risks:\n{bias_md}\n\n"
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
        except Exception:  # noqa: BLE001 — deterministic fallback
            pass
        return self._fallback_summary(context, bias_risks, frameworks)

    def _fallback_summary(
        self, context: dict, bias_risks: list[dict], frameworks: list[dict]
    ) -> str:
        tier = next((f.get("tier") for f in frameworks if f.get("framework") == "EU AI Act"), "?")
        highs = sum(1 for r in bias_risks if r.get("severity") in ("critical", "high"))
        return (
            f"This {context.get('decision_type')} use case maps to EU AI Act tier "
            f"'{tier}' and surfaced {len(bias_risks)} bias risk(s), {highs} high-severity. "
            f"Prioritize subgroup fairness testing, decision explainability, and human "
            f"oversight proportional to the tier, and resolve the high-severity bias risks "
            f"before deployment."
        )

    # --- vault + state I/O -------------------------------------------------
    def _write_review(
        self,
        review_id: str,
        display_name: str,
        created_at: str,
        context: dict,
        bias_risks: list[dict],
        fairness: list[str],
        explainability: list[str],
        oversight: list[str],
        frameworks: list[dict],
        summary: str,
    ) -> str:
        ts_key = created_at.replace(":", "-")
        key = f"{_REVIEW_PREFIX}{_slug(display_name)}/{ts_key}.md"

        def _bullets(items: list[str]) -> str:
            return "\n".join(f"- {it}" for it in items) or "- (none)"

        bias_md = (
            "\n".join(
                f"- **[{r.get('severity')}]** ({r.get('category')}) {r.get('description')}  \n"
                f"  _Mitigation:_ {r.get('mitigation')}"
                for r in bias_risks
            )
            or "- (none)"
        )
        fw_md = (
            "\n".join(
                f"- **{f.get('framework')}**: {f.get('tier')} — {f.get('note')}" for f in frameworks
            )
            or "- (none)"
        )
        dt_csv = ", ".join(context.get("data_types") or [])
        pop_csv = ", ".join(context.get("affected_populations") or [])
        body = (
            f"---\n"
            f"id: {review_id}\n"
            f"type: ethics-review\n"
            f"display_name: {display_name}\n"
            f"use_case: {context.get('use_case') or ''}\n"
            f"industry: {context.get('industry') or ''}\n"
            f"geography: {context.get('geography') or ''}\n"
            f"decision_type: {context.get('decision_type') or ''}\n"
            f"data_types: [{dt_csv}]\n"
            f"affected_populations: [{pop_csv}]\n"
            f"created_at: {created_at}\n"
            f"---\n\n"
            f"# AI Ethics & Bias Review\n\n"
            f"{summary}\n\n"
            f"## Regulatory mapping\n\n{fw_md}\n\n"
            f"## Bias risks\n\n{bias_md}\n\n"
            f"## Fairness considerations\n\n{_bullets(fairness)}\n\n"
            f"## Explainability requirements\n\n{_bullets(explainability)}\n\n"
            f"## Human-oversight recommendations\n\n{_bullets(oversight)}\n"
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
            ctx = st.get("context") or {}
            out.append(
                {
                    "review_id": st.get("review_id"),
                    "use_case": ctx.get("use_case"),
                    "decision_type": ctx.get("decision_type"),
                    "industry": ctx.get("industry"),
                    "created_at": st.get("created_at"),
                    "risk_count": len(st.get("bias_risks") or []),
                }
            )
        out.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return {"status": "ok", "reviews": out}


def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()
