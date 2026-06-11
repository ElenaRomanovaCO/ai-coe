"""AGENT-12 — AI Use Case Ideation Engine (Module 12), Sonnet 4.6 tier.

Turns a client context (industry, pain points, goals, available data, AI maturity
stage) into a **ranked** list of use-case candidates, each with an effort/impact
rating, prerequisites, a reference example from the Asset Library, and a rationale.

This is a generative module, so — unlike the deterministic-by-default workers
(``vault/decisions/worker-pattern.md``) — the candidate *generation* is an LLM call
(Sonnet returns a JSON array, validated against :class:`UseCaseCandidate`). Everything
around it stays deterministic and testable: **scoring/ranking** is a rule
(impact/effort + stage & data priors), **reference linking** composes AGENT-03's
semantic search, and **export** is a templated markdown writer.

Persistence mirrors AGENT-02/05: the full result JSON is written to the sessions
bucket (read back by ``get`` for the results page), and a human-readable markdown
export is written to the vault under ``ideation/{display_name}/{ts}.md`` (re-embedded,
searchable) — that file path is the ``vault_file_path`` returned to the caller.

No Bedrock guardrail is applied (the module-agents role lacks ``ApplyGuardrail`` — see
``vault/decisions/asset-panel-no-guardrail.md``); the prompt is grounded in the
caller-supplied context.

Operations (on ``op``):
  - ``generate`` (default) — generate + score + link + persist → IdeationResult
  - ``get``                — read a saved ideation by id → IdeationResult
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .agent_03_asset_library import AssetLibraryAgent, _slug
from .base import ModuleAgent

AGENT_ID = "AGENT-12"
IDEATION_PREFIX = "ideation/"
ASSET_LIBRARY_ROUTE = "/modules/asset-library"
MAX_CANDIDATES = 8

# Effort/impact -> weight for the deterministic ranking. Impact is weighted above
# effort so a high-impact/high-effort idea still beats a low-impact/low-effort one.
_IMPACT_W = {"low": 1, "medium": 2, "high": 3}
_EFFORT_W = {"low": 1, "medium": 2, "high": 3}
_LEVELS = ("low", "medium", "high")

SYSTEM = """You are an AI use-case ideation engine for a delivery consultancy. Given a \
client's industry, pain points, goals, available data, and AI maturity stage (0-5), \
propose concrete, realistic AI use cases tailored to them.

Return ONLY a JSON array (no prose, no code fences) of 5-8 objects, each:
{
  "title": "<short use-case name>",
  "description": "<2-3 sentences: what it does and how>",
  "effort": "low" | "medium" | "high",
  "impact": "low" | "medium" | "high",
  "prerequisites": ["<data/capability needed>", ...],
  "rationale": "<1-2 sentences tying it to their pain points/goals/data/stage>"
}

Rules:
- Ground every candidate in the provided context; prefer ideas the available data can \
support and that fit the client's maturity stage (don't propose stage-5 moonshots to a \
stage-1 org).
- effort/impact are your honest estimate for THIS client.
- No vendor names, no company names. Be specific and practical."""


class IdeationRequest(BaseModel):
    industry: str
    pain_points: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    available_data: list[str] = Field(default_factory=list)
    ai_stage: int = 2


class UseCaseCandidate(BaseModel):
    id: str = ""
    title: str
    description: str = ""
    effort: Literal["low", "medium", "high"] = "medium"
    impact: Literal["low", "medium", "high"] = "medium"
    prerequisites: list[str] = Field(default_factory=list)
    reference_example_asset_id: str | None = None
    # Display helpers (superset of the spec model; harmless to extra consumers).
    reference_example_title: str | None = None
    reference_example_url: str | None = None
    rationale: str = ""
    rank_score: float = 0.0


class IdeationResult(BaseModel):
    ideation_id: str
    candidates: list[UseCaseCandidate] = Field(default_factory=list)
    vault_file_path: str = ""


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


class IdeationAgent(ModuleAgent):
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
        s3vectors: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.region = region
        self._s3 = s3
        self.bedrock_client = bedrock_client or BedrockClient(client=bedrock)
        # AGENT-03 owns the S3 + S3 Vectors plumbing; compose it for reference search.
        self.asset_agent = asset_agent or AssetLibraryAgent(
            vault_bucket=vault_bucket,
            sessions_bucket=sessions_bucket,
            s3=s3,
            s3vectors=s3vectors,
            bedrock=bedrock,
            region=region,
        )

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        if "ideation_id" not in args and args.get("id"):
            args = {**args, "ideation_id": args["id"]}
        op = args.get("op")
        if op == "get" or (op is None and args.get("ideation_id")):
            return self.run_tool("get_ideation", lambda _u: self._get(args))
        return self.run_tool("generate_ideation", lambda _u: self._generate(args))

    # --- operations --------------------------------------------------------
    def _generate(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        try:
            req = IdeationRequest.model_validate(args)
        except ValidationError as exc:
            return {"status": "error", "message": f"Invalid request: {exc.errors()[:1]}"}
        if not req.industry:
            return {"status": "error", "message": "industry is required."}

        candidates = self._generate_candidates(req)
        if not candidates:
            return {
                "status": "error",
                "message": "Could not generate use-case candidates. Please try again.",
            }
        candidates = self._score_candidates(candidates, req)
        self._attach_references(candidates)

        ideation_id = "idea-" + uuid.uuid4().hex[:12]
        created_at = _now_iso()
        markdown = self._export_to_markdown(req, candidates, created_at)
        vault_path = self._write_vault(display_name, created_at, markdown)

        result = IdeationResult(
            ideation_id=ideation_id, candidates=candidates, vault_file_path=vault_path
        )
        self._save_state(
            {
                "ideation_id": ideation_id,
                "display_name": display_name,
                "request": req.model_dump(),
                "created_at": created_at,
                "markdown": markdown,
                **result.model_dump(),
            }
        )
        return {"status": "ok", "markdown": markdown, **result.model_dump()}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        ideation_id = _norm(args.get("ideation_id"))
        if not ideation_id:
            return {"status": "error", "message": "ideation_id is required."}
        state = self._load_state(ideation_id)
        if state is None:
            return {"status": "not_found", "ideation_id": ideation_id}
        return {
            "status": "ok",
            "ideation_id": state["ideation_id"],
            "candidates": state.get("candidates", []),
            "vault_file_path": state.get("vault_file_path", ""),
            "request": state.get("request", {}),
            "created_at": state.get("created_at", ""),
            "markdown": state.get("markdown", ""),
        }

    # --- generate (the one LLM call) ---------------------------------------
    def _generate_candidates(self, req: IdeationRequest) -> list[UseCaseCandidate]:
        user_text = (
            f"Industry: {req.industry}\n"
            f"AI maturity stage (0-5): {req.ai_stage}\n"
            f"Pain points: {_join(req.pain_points)}\n"
            f"Goals: {_join(req.goals)}\n"
            f"Available data: {_join(req.available_data)}\n\n"
            f"Generate the JSON array of use-case candidates."
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
                    system=SYSTEM,
                    max_tokens=2048,
                    usage=usage,
                )
            text = _extract_text(resp.get("output", {}).get("message", {}))
        except Exception:  # noqa: BLE001 — generation is the whole job; surface as empty
            return []

        raw_items = _parse_candidate_list(text)
        out: list[UseCaseCandidate] = []
        for i, item in enumerate(raw_items[:MAX_CANDIDATES]):
            if not isinstance(item, dict) or not _norm(item.get("title")):
                continue
            item = {k: v for k, v in item.items() if k in UseCaseCandidate.model_fields}
            item.setdefault("id", f"uc-{i + 1}")
            item["effort"] = _coerce_level(item.get("effort"))
            item["impact"] = _coerce_level(item.get("impact"))
            try:
                out.append(UseCaseCandidate.model_validate(item))
            except ValidationError:
                continue
        return out

    # --- score / rank (deterministic) --------------------------------------
    def _score_candidates(
        self, candidates: list[UseCaseCandidate], req: IdeationRequest
    ) -> list[UseCaseCandidate]:
        data_terms = {t for d in req.available_data for t in _tokens(d)}
        for c in candidates:
            score = 2.0 * _IMPACT_W[c.impact] - _EFFORT_W[c.effort]
            # Prior: reward ideas the client's available data can already support.
            hay = _tokens(c.title) | _tokens(c.description) | {
                t for p in c.prerequisites for t in _tokens(p)
            }
            if data_terms and (data_terms & hay):
                score += 1.0
            # Prior: a high-effort idea is a worse early-stage fit.
            if req.ai_stage <= 1 and c.effort == "high":
                score -= 1.0
            c.rank_score = round(score, 2)
        candidates.sort(key=lambda c: (c.rank_score, _IMPACT_W[c.impact]), reverse=True)
        return candidates

    # --- reference linking (composes AGENT-03) -----------------------------
    def _attach_references(self, candidates: list[UseCaseCandidate]) -> None:
        for c in candidates:
            query = f"{c.title} {c.description}".strip()
            try:
                res = self.asset_agent.handle({"op": "search", "query": query, "top_k": 1})
            except Exception:  # noqa: BLE001 — references are best-effort
                continue
            assets = res.get("assets", []) if res.get("status") == "ok" else []
            if assets:
                aid = _norm(assets[0].get("id"))
                if aid:
                    c.reference_example_asset_id = aid
                    c.reference_example_title = _norm(assets[0].get("title")) or aid
                    c.reference_example_url = f"{ASSET_LIBRARY_ROUTE}/{aid}"

    # --- export (templated markdown) ---------------------------------------
    def _export_to_markdown(
        self, req: IdeationRequest, candidates: list[UseCaseCandidate], created_at: str
    ) -> str:
        lines = [
            f"# AI Use Case Ideation — {req.industry.title()} · Stage {req.ai_stage}",
            "",
            f"_Generated {created_at[:10]} · {len(candidates)} candidates, ranked by "
            f"impact vs. effort._",
            "",
            "## Context",
            "",
            f"- **Industry:** {req.industry}",
            f"- **AI maturity stage:** {req.ai_stage}",
            f"- **Pain points:** {_join(req.pain_points)}",
            f"- **Goals:** {_join(req.goals)}",
            f"- **Available data:** {_join(req.available_data)}",
            "",
            "## Ranked candidates",
            "",
        ]
        for i, c in enumerate(candidates, 1):
            prereqs = "; ".join(c.prerequisites) or "—"
            ref = (
                f"[{c.reference_example_title}](`{c.reference_example_asset_id}`)"
                if c.reference_example_asset_id
                else "—"
            )
            lines += [
                f"### {i}. {c.title}",
                "",
                f"- **Impact:** {c.impact} · **Effort:** {c.effort}",
                f"- {c.description}",
                f"- **Prerequisites:** {prereqs}",
                f"- **Reference example:** {ref}",
                f"- **Why this fits:** {c.rationale}",
                "",
            ]
        return "\n".join(lines)

    # --- persistence -------------------------------------------------------
    def _write_vault(self, display_name: str, created_at: str, markdown: str) -> str:
        ts_key = created_at.replace(":", "-")
        key = f"{IDEATION_PREFIX}{_slug(display_name)}/{ts_key}.md"
        self.s3.put_object(
            Bucket=self.vault_bucket,
            Key=key,
            Body=markdown.encode("utf-8"),
            ContentType="text/markdown",
        )
        return key

    def _state_key(self, display_name: str, ideation_id: str) -> str:
        return f"{IDEATION_PREFIX}{_slug(display_name)}/{ideation_id}.json"

    def _save_state(self, state: dict) -> None:
        self.s3.put_object(
            Bucket=self.sessions_bucket,
            Key=self._state_key(state["display_name"], state["ideation_id"]),
            Body=json.dumps(state, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    def _load_state(self, ideation_id: str) -> dict | None:
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=IDEATION_PREFIX)
        suffix = f"/{ideation_id}.json"
        for o in resp.get("Contents", []):
            if o["Key"].endswith(suffix):
                raw = self.s3.get_object(Bucket=self.sessions_bucket, Key=o["Key"])["Body"].read()
                try:
                    return json.loads(raw)
                except (json.JSONDecodeError, ValueError):
                    return None
        return None


# --- module-level helpers --------------------------------------------------
def _join(items: list[str]) -> str:
    vals = [_norm(i) for i in (items or []) if _norm(i)]
    return ", ".join(vals) if vals else "(none provided)"


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", str(text or "").lower()) if len(t) >= 3}


def _coerce_level(value: Any) -> str:
    v = _norm(value).lower()
    return v if v in _LEVELS else "medium"


def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()


def _parse_candidate_list(text: str) -> list:
    """Pull a JSON array of candidates out of the model's response, leniently."""
    t = text.strip()
    if t.startswith("```"):
        # drop the opening fence (``` or ```json) and any closing fence
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t).strip()
    # Prefer the outermost [...] slice; fall back to a {"candidates": [...]} object.
    start, end = t.find("["), t.rfind("]")
    if start != -1 and end > start:
        t = t[start : end + 1]
    try:
        data = json.loads(t)
    except (json.JSONDecodeError, ValueError):
        return []
    if isinstance(data, dict):
        data = data.get("candidates") or data.get("use_cases") or []
    return data if isinstance(data, list) else []
