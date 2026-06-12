"""AGENT-14 — Client Maturity Report Portal (Module 14), Sonnet 4.6 tier.

From a completed maturity assessment, generates a polished, client-facing report: six
sections (executive summary, stage placement, what this means, top next steps,
recommended use cases, benchmark paragraph). The user can edit any section; the report
exports to PDF (rendered in the web layer from the structured sections — see
``web/app/(authenticated)/modules/reports``).

**No workers, inline (AGENT-29 precedent).** The spec listed WORKER-06 (narrative_writer)
+ WORKER-07 (benchmark_lookup), but the locked worker-pattern keeps workers
deterministic/no-LLM and the most recent document-generator (AGENT-29 SOW) folded the prose
into the agent's single Sonnet call. AGENT-14 follows that: it reads the assessment, **composes
AGENT-21 in-process** for the benchmark (the AGENT-16→AGENT-03 composition precedent — no
worker, no cross-Lambda hop), builds a deterministic six-section skeleton, and makes **one**
Sonnet call for the narrative prose. A deterministic skeleton-only assembly is the fallback
when Bedrock fails, so the report is always producible and fully testable.

Reports are client-specific deliverables, so they persist to the **sessions** bucket
(``reports/{display_name}/{report_id}.md`` + a ``.json`` state) and never to the vault — they
must not enter the searchable knowledge base (AGENT-29 storage precedent). Editing rewrites
both objects (FR-059).

Operations (on ``op``):
  - ``generate``       — assessment + benchmark → skeleton + Sonnet prose → persist (default)
  - ``get``            — one saved report (sections + markdown)
  - ``list``           — the caller's saved reports
  - ``update_section`` — replace one section's content, re-render + re-persist (FR-059)
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

from .agent_03_asset_library import _slug
from .agent_21_benchmark import BenchmarkAgent
from .base import ModuleAgent

AGENT_ID = "AGENT-14"
REPORT_ROUTE = "/modules/reports"
REPORTS_PREFIX = "reports/"
ASSESSMENTS_PREFIX = "assessments/"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}

# Section keys in render order. Prose sections are strings; list sections are list[str].
PROSE_SECTIONS = ("executive_summary", "stage_placement", "what_this_means", "benchmark_paragraph")
LIST_SECTIONS = ("top_next_steps", "recommended_use_cases")
SECTION_ORDER = (
    "executive_summary",
    "stage_placement",
    "benchmark_paragraph",
    "what_this_means",
    "top_next_steps",
    "recommended_use_cases",
)
SECTION_TITLES = {
    "executive_summary": "Executive Summary",
    "stage_placement": "Maturity Stage Placement",
    "benchmark_paragraph": "How You Compare to Peers",
    "what_this_means": "What This Means",
    "top_next_steps": "Top Next Steps",
    "recommended_use_cases": "Recommended Use Cases",
}

PROSE_SYSTEM = """You write the prose for a polished, client-facing AI maturity report, \
grounded ONLY in the structured assessment and benchmark facts provided. Do not invent \
scores, stages, regulations, peer figures, or recommendations beyond the inputs. The tone is \
that of a senior consultant briefing a client executive: clear, confident, plain-spoken, no \
jargon dumps.

Return ONLY a JSON object:
{
  "executive_summary": "<2-3 sentences: where the client stands and the headline takeaway>",
  "stage_placement": "<1 short paragraph explaining the assessed stage and what drove it>",
  "what_this_means": "<1 short paragraph on the implications, grounded in the dimensions>",
  "benchmark_paragraph": "<2-3 sentences placing the client against the peer distribution given>",
  "top_next_steps": ["<concrete next step>", ...],
  "recommended_use_cases": ["<use case appropriate to the stage>", ...]
}

Use ONLY the numbers and items given. No client names beyond what is provided; no PII."""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _list_str(values: Any) -> list[str]:
    return [_norm(v) for v in (values or []) if _norm(v)]


class ReportAgent(ModuleAgent):
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
        benchmark_agent: BenchmarkAgent | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.region = region
        self._s3 = s3
        self.bedrock_client = bedrock_client or BedrockClient(client=bedrock)
        self._benchmark_agent = benchmark_agent
        self._bedrock = bedrock

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    @property
    def benchmark(self) -> BenchmarkAgent:
        # Compose AGENT-21 in-process (no worker, no cross-Lambda hop) sharing our clients.
        if self._benchmark_agent is None:
            self._benchmark_agent = BenchmarkAgent(
                vault_bucket=self.vault_bucket,
                sessions_bucket=self.sessions_bucket,
                region=self.region,
                s3=self._s3,
                bedrock=self._bedrock,
                bedrock_client=self.bedrock_client,
                metrics_client=self.metrics_client,
            )
        return self._benchmark_agent

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        if "report_id" not in args and args.get("id"):
            args = {**args, "report_id": args["id"]}
        op = args.get("op")
        if op == "get" or (op is None and args.get("report_id")):
            return self.run_tool("get_report", lambda _u: self._get(args))
        if op == "list":
            return self.run_tool("list_reports", lambda _u: self._list(args))
        if op == "update_section":
            return self.run_tool("update_section", lambda _u: self._update_section(args))
        return self.run_tool("generate_report", lambda _u: self._generate(args))

    # --- state I/O (sessions only) -----------------------------------------
    def _md_key(self, display_name: str, report_id: str) -> str:
        return f"{REPORTS_PREFIX}{_slug(display_name)}/{report_id}.md"

    def _state_key(self, display_name: str, report_id: str) -> str:
        return f"{REPORTS_PREFIX}{_slug(display_name)}/{report_id}.json"

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

    def _find_state_key(self, report_id: str) -> str | None:
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=REPORTS_PREFIX)
        suffix = f"/{report_id}.json"
        for o in resp.get("Contents", []):
            if o["Key"].endswith(suffix):
                return o["Key"]
        return None

    def _load_assessment(self, assessment_id: str) -> dict | None:
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=ASSESSMENTS_PREFIX)
        suffix = f"/{assessment_id}.json"
        for o in resp.get("Contents", []):
            if o["Key"].endswith(suffix):
                return self._read_json(self.sessions_bucket, o["Key"])
        return None

    def _persist(self, state: dict) -> None:
        display_name = state["display_name"]
        report_id = state["report_id"]
        self.s3.put_object(
            Bucket=self.sessions_bucket,
            Key=self._md_key(display_name, report_id),
            Body=state["markdown"].encode("utf-8"),
            ContentType="text/markdown",
        )
        self.s3.put_object(
            Bucket=self.sessions_bucket,
            Key=self._state_key(display_name, report_id),
            Body=json.dumps(state, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    # --- operations --------------------------------------------------------
    def _generate(self, args: dict[str, Any]) -> dict[str, Any]:
        assessment_id = _norm(args.get("assessment_id"))
        if not assessment_id:
            return {"status": "error", "message": "assessment_id is required."}
        astate = self._load_assessment(assessment_id)
        if astate is None:
            return {"status": "not_found", "assessment_id": assessment_id}
        result = astate.get("result") or {}
        if astate.get("status") != "complete" or not result:
            return {"status": "error", "message": "Assessment is not complete yet."}

        display_name = _norm(astate.get("display_name")) or "anon"
        industry = _norm(astate.get("industry")) or "cross-industry"
        stage = int(result.get("stage", 0) or 0)

        bench = self.benchmark.handle({"op": "get", "assessment_id": assessment_id})
        bench = bench if bench.get("status") == "ok" else {}

        facts = self._facts(industry, stage, result, bench, args.get("client_context"))
        prose = self._draft_prose(facts)
        sections = self._assemble_sections(facts, prose, result, bench)

        report_id = "report-" + uuid.uuid4().hex[:12]
        created_at = _now_iso()
        title = f"AI Maturity Report — {industry.title()} (Stage {stage})"
        markdown = self._render_markdown(title, display_name, created_at, sections)
        state = {
            "report_id": report_id,
            "assessment_id": assessment_id,
            "display_name": display_name,
            "created_at": created_at,
            "updated_at": created_at,
            "title": title,
            "industry": industry,
            "stage": stage,
            "client_context": (
                _norm(args.get("client_context")) or _norm(astate.get("client_context"))
            ),
            "sections": sections,
            "markdown": markdown,
        }
        self._persist(state)
        return {"status": "ok", **self._public(state)}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        report_id = _norm(args.get("report_id"))
        if not report_id:
            return {"status": "error", "message": "report_id is required."}
        key = self._find_state_key(report_id)
        if key is None:
            return {"status": "not_found", "report_id": report_id}
        state = self._read_json(self.sessions_bucket, key)
        if not state:
            return {"status": "not_found", "report_id": report_id}
        return {"status": "ok", **self._public(state)}

    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        prefix = f"{REPORTS_PREFIX}{_slug(display_name)}/"
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=prefix)
        out: list[dict] = []
        for o in resp.get("Contents", []):
            if not o["Key"].endswith(".json"):
                continue
            state = self._read_json(self.sessions_bucket, o["Key"])
            if state:
                out.append(
                    {
                        "report_id": state["report_id"],
                        "assessment_id": state.get("assessment_id", ""),
                        "title": state.get("title", ""),
                        "industry": state.get("industry", ""),
                        "stage": state.get("stage"),
                        "created_at": state.get("created_at", ""),
                        "updated_at": state.get("updated_at", ""),
                    }
                )
        out.sort(key=lambda r: r.get("updated_at") or r.get("created_at") or "", reverse=True)
        return {"status": "ok", "reports": out}

    def _update_section(self, args: dict[str, Any]) -> dict[str, Any]:
        report_id = _norm(args.get("report_id"))
        section = _norm(args.get("section"))
        if not report_id or not section:
            return {"status": "error", "message": "report_id and section are required."}
        if section not in SECTION_ORDER:
            return {"status": "error", "message": f"Unknown section '{section}'."}
        key = self._find_state_key(report_id)
        if key is None:
            return {"status": "not_found", "report_id": report_id}
        state = self._read_json(self.sessions_bucket, key)
        if not state:
            return {"status": "not_found", "report_id": report_id}

        content = args.get("content")
        if section in LIST_SECTIONS:
            state["sections"][section] = (
                _list_str(content)
                if isinstance(content, list)
                else [_norm(line) for line in str(content or "").splitlines() if _norm(line)]
            )
        else:
            state["sections"][section] = _norm(content)
        state["updated_at"] = _now_iso()
        state["markdown"] = self._render_markdown(
            state["title"], state["display_name"], state["created_at"], state["sections"]
        )
        self._persist(state)
        return {"status": "ok", **self._public(state)}

    # --- fact gathering + prose (the one LLM call; deterministic fallback) --
    def _facts(
        self, industry: str, stage: int, result: dict, bench: dict, client_context: Any
    ) -> dict[str, Any]:
        dims = result.get("dimension_scores") or {}
        weak = sorted([d for d, s in dims.items() if int(s) <= 2])
        strong = sorted([d for d, s in dims.items() if int(s) >= 4])
        dist = bench.get("peer_distribution") or {}
        at_or_below = sum(
            float(p) for s, p in dist.items() if _as_int(s) is not None and _as_int(s) <= stage
        )
        return {
            "industry": industry,
            "stage": stage,
            "client_context": _norm(client_context),
            "rationale": _norm(result.get("rationale")),
            "dimension_scores": {k: int(v) for k, v in dims.items()},
            "weak_dimensions": weak,
            "strong_dimensions": strong,
            "recommendations": [
                _norm(r.get("title") or r.get("id")) for r in (result.get("recommendations") or [])
            ],
            "peer_distribution": {str(k): float(v) for k, v in dist.items()},
            "peers_at_or_below_pct": round(at_or_below),
            "typical_use_cases": _list_str(
                (bench.get("typical_use_cases_at_stage") or {}).get(stage)
                or (bench.get("typical_use_cases_at_stage") or {}).get(str(stage))
            ),
            "common_next_moves": _list_str(bench.get("common_next_moves")),
            "benchmark_narrative": _norm(bench.get("narrative")),
        }

    def _draft_prose(self, facts: dict[str, Any]) -> dict[str, Any]:
        dims_md = ", ".join(f"{k}: {v}/5" for k, v in facts["dimension_scores"].items()) or "(none)"
        dist_md = (
            ", ".join(f"stage {k}: {v:.0f}%" for k, v in sorted(facts["peer_distribution"].items()))
            or "(none)"
        )
        user_text = (
            f"Client context: {facts['client_context'] or '(none)'}\n"
            f"Industry: {facts['industry']}\n"
            f"Assessed maturity stage: {facts['stage']} of 5\n"
            f"Scoring rationale: {facts['rationale'] or '(none)'}\n"
            f"Dimension scores: {dims_md}\n"
            f"Weak dimensions (<=2): {', '.join(facts['weak_dimensions']) or '(none)'}\n"
            f"Strong dimensions (>=4): {', '.join(facts['strong_dimensions']) or '(none)'}\n"
            f"Recommended assets: {', '.join(facts['recommendations']) or '(none)'}\n"
            f"Peer distribution: {dist_md}\n"
            f"Approx. peers at or below this stage: {facts['peers_at_or_below_pct']}%\n"
            f"Typical use cases at stage: {', '.join(facts['typical_use_cases']) or '(none)'}\n"
            f"Common next moves: {', '.join(facts['common_next_moves']) or '(none)'}\n\n"
            f"Write the report prose JSON."
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
                    max_tokens=1100,
                    usage=usage,
                )
            data = _parse_json_object(_extract_text(resp.get("output", {}).get("message", {})))
            if data:
                return {
                    "executive_summary": _norm(data.get("executive_summary")),
                    "stage_placement": _norm(data.get("stage_placement")),
                    "what_this_means": _norm(data.get("what_this_means")),
                    "benchmark_paragraph": _norm(data.get("benchmark_paragraph")),
                    "top_next_steps": _list_str(data.get("top_next_steps")),
                    "recommended_use_cases": _list_str(data.get("recommended_use_cases")),
                }
        except Exception:  # noqa: BLE001 — fall back to a deterministic skeleton
            pass
        return {k: "" for k in PROSE_SECTIONS} | {k: [] for k in LIST_SECTIONS}

    def _assemble_sections(
        self, facts: dict, prose: dict, result: dict, bench: dict
    ) -> dict[str, Any]:
        stage = facts["stage"]
        industry = facts["industry"]
        narrative = facts["benchmark_narrative"]

        exec_summary = prose.get("executive_summary") or (
            f"This {industry} organization is assessed at stage {stage} of 5 on the AI maturity "
            f"curve. {narrative}".strip()
        )
        stage_placement = prose.get("stage_placement") or (
            facts["rationale"]
            or f"The assessment places the organization at stage {stage} of 5 across the six "
            f"maturity dimensions."
        )
        benchmark_paragraph = prose.get("benchmark_paragraph") or narrative or (
            f"Roughly {facts['peers_at_or_below_pct']}% of peers sit at or below stage {stage}."
        )
        what_this_means = prose.get("what_this_means") or _fallback_what_this_means(facts)

        top_next_steps = prose.get("top_next_steps") or facts["common_next_moves"]
        top_next_steps = top_next_steps[:5] or ["Define the next set of high-value use cases."]

        use_cases = prose.get("recommended_use_cases") or (
            facts["typical_use_cases"] + facts["recommendations"]
        )
        # de-dup, preserve order, cap
        seen: set[str] = set()
        deduped = []
        for u in use_cases:
            if u and u not in seen:
                seen.add(u)
                deduped.append(u)
        use_cases = deduped[:6] or ["(to be defined with the client)"]

        return {
            "executive_summary": exec_summary,
            "stage_placement": stage_placement,
            "benchmark_paragraph": benchmark_paragraph,
            "what_this_means": what_this_means,
            "top_next_steps": top_next_steps,
            "recommended_use_cases": use_cases,
        }

    # --- markdown rendering (for vault-free export + .md persistence) ------
    def _render_markdown(
        self, title: str, display_name: str, created_at: str, sections: dict
    ) -> str:
        def block(key: str) -> str:
            heading = f"## {SECTION_TITLES[key]}\n\n"
            value = sections.get(key)
            if key in LIST_SECTIONS:
                body = "\n".join(f"- {v}" for v in (value or [])) or "- (none)"
            else:
                body = _norm(value) or "_(empty)_"
            return heading + body

        body = "\n\n".join(block(k) for k in SECTION_ORDER)
        return f"# {title}\n\n_Prepared for {display_name} · {created_at}_\n\n{body}\n"

    def _public(self, state: dict) -> dict[str, Any]:
        return {
            "report_id": state["report_id"],
            "assessment_id": state.get("assessment_id", ""),
            "title": state.get("title", ""),
            "industry": state.get("industry", ""),
            "stage": state.get("stage"),
            "client_context": state.get("client_context", ""),
            "sections": state.get("sections", {}),
            "section_order": list(SECTION_ORDER),
            "section_titles": dict(SECTION_TITLES),
            "markdown": state.get("markdown", ""),
            "created_at": state.get("created_at", ""),
            "updated_at": state.get("updated_at", ""),
        }


def _as_int(v: Any) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _fallback_what_this_means(facts: dict) -> str:
    weak = facts["weak_dimensions"]
    strong = facts["strong_dimensions"]
    parts = []
    if strong:
        parts.append(
            f"Strengths in {', '.join(strong)} give a foundation to build on."
        )
    if weak:
        parts.append(
            f"The binding constraints are {', '.join(weak)}; closing these gaps is the fastest "
            f"path to the next stage."
        )
    if not parts:
        parts.append("Capabilities are balanced across dimensions; focus on disciplined execution.")
    return " ".join(parts)


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
