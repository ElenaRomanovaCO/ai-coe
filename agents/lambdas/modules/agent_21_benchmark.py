"""AGENT-21 — Client Benchmark Comparator (Module 22), Haiku 4.5 tier.

After a maturity assessment, places the client against anonymized industry peers: where
they sit on the 0-5 curve vs the peer distribution, the typical use cases at each stage,
and common next moves — plus a slide-ready export.

**Deterministic core + one Haiku call** (AGENT-05 precedent): the peer distribution comes
from a seeded file (``vault/benchmarks/_seed_peer_distribution.json``); use cases and next
moves are fixed by-stage maps; only the narrative is generated (with a deterministic
fallback). ``get`` never persists; ``export`` writes a slide to the vault tagged
``generated: true`` (runtime-vault-writers convention — client-specific, scoped out of
chat KB search).

The client's stage + industry are read from the assessment's sessions state (AGENT-02),
located by id under ``assessments/``.

Operations (on ``op``):
  - ``get``     — benchmark for an assessment (default when ``assessment_id`` present)
  - ``export``  — render + persist the slide markdown → vault path + markdown
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import ClientError

from agents.lambdas.modules.agent_03_asset_library import _slug
from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .base import ModuleAgent
from .vault_export import export_frontmatter

AGENT_ID = "AGENT-21"
ASSESSMENTS_PREFIX = "assessments/"
BENCHMARKS_PREFIX = "benchmarks/"
SEED_KEY = "benchmarks/_seed_peer_distribution.json"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}
_STAGES = [0, 1, 2, 3, 4, 5]

# Fixed, deterministic by-stage maps (industry-agnostic — the narrative personalizes).
TYPICAL_USE_CASES_BY_STAGE: dict[int, list[str]] = {
    0: ["Awareness building", "Data-readiness assessment"],
    1: ["First proof-of-concept", "Exploratory RAG / chatbot pilot"],
    2: ["Production pilot", "Internal copilot", "Document Q&A"],
    3: ["Multiple production use cases", "LLMOps foundation", "Governance controls"],
    4: ["Scaled platform + reusable patterns", "Center of Excellence", "Adoption programs"],
    5: ["AI-native products", "Continuous optimization", "Org-wide enablement"],
}
NEXT_MOVES_BY_STAGE: dict[int, list[str]] = {
    0: ["Run a maturity + data-readiness assessment", "Pick 1-2 high-value pilot use cases"],
    1: ["Stand up a production-grade pilot with an eval set", "Define governance guardrails early"],
    2: ["Promote a pilot to production", "Establish LLMOps + cost monitoring",
        "Formalize a use-case intake pipeline"],
    3: ["Build reusable platform components", "Stand up a CoE / shared services",
        "Scale governance org-wide"],
    4: ["Drive adoption + enablement across teams", "Optimize cost/quality with evals",
        "Pursue AI-native product bets"],
    5: ["Continuous benchmarking + reinvestment", "Externalize patterns / thought leadership"],
}

NARRATIVE_SYSTEM = """You write a short, executive-friendly benchmark note. You are given a \
client's AI maturity stage (0-5), their industry, and the anonymized peer distribution \
across stages. Write 2-3 sentences: where the client sits relative to peers (ahead/typical/ \
behind), what that implies, and the thrust of their next move. Use ONLY the numbers given; \
do not invent figures. Be direct; no preamble, no bullet lists."""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _norm(s: Any) -> str:
    return str(s or "").strip()


class BenchmarkAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.HAIKU_4_5

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
        if "assessment_id" not in args and args.get("id"):
            args = {**args, "assessment_id": args["id"]}
        op = args.get("op")
        if op == "export":
            return self.run_tool("export_benchmark", lambda _u: self._export(args))
        return self.run_tool("get_benchmark", lambda _u: self._get(args))

    # --- data loading ------------------------------------------------------
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

    def _load_assessment(self, assessment_id: str) -> dict | None:
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=ASSESSMENTS_PREFIX)
        suffix = f"/{assessment_id}.json"
        for o in resp.get("Contents", []):
            if o["Key"].endswith(suffix):
                return self._read_json(self.sessions_bucket, o["Key"])
        return None

    def _peer_distribution(self, industry: str) -> dict[int, float]:
        seed = self._read_json(self.vault_bucket, SEED_KEY) or {}
        industries = seed.get("industries", {})
        raw = industries.get(industry) or industries.get("cross-industry") or {}
        return {s: float(raw.get(str(s), 0)) for s in _STAGES}

    # --- benchmark assembly ------------------------------------------------
    def _build(self, state: dict) -> dict[str, Any]:
        result = state.get("result") or {}
        stage = int(result.get("stage", state.get("stage", 0)) or 0)
        industry = _norm(state.get("industry")) or "cross-industry"
        distribution = self._peer_distribution(industry)
        narrative = self._narrate(stage, industry, distribution)
        return {
            "assessment_id": state.get("assessment_id", ""),
            "client_stage": stage,
            "industry": industry,
            "peer_distribution": distribution,
            "typical_use_cases_at_stage": {s: TYPICAL_USE_CASES_BY_STAGE[s] for s in _STAGES},
            "common_next_moves": NEXT_MOVES_BY_STAGE.get(stage, []),
            "narrative": narrative,
        }

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        assessment_id = _norm(args.get("assessment_id"))
        if not assessment_id:
            return {"status": "error", "message": "assessment_id is required."}
        state = self._load_assessment(assessment_id)
        if state is None:
            return {"status": "not_found", "assessment_id": assessment_id}
        bench = self._build(state)
        bench["markdown"] = self._slide_markdown(bench)
        return {"status": "ok", **bench}

    def _export(self, args: dict[str, Any]) -> dict[str, Any]:
        assessment_id = _norm(args.get("assessment_id"))
        if not assessment_id:
            return {"status": "error", "message": "assessment_id is required."}
        state = self._load_assessment(assessment_id)
        if state is None:
            return {"status": "not_found", "assessment_id": assessment_id}
        bench = self._build(state)
        markdown = self._slide_markdown(bench)
        display_name = _norm(state.get("display_name")) or "anon"
        ts = _now_iso().replace(":", "-")
        key = f"{BENCHMARKS_PREFIX}{_slug(display_name)}/{ts}.md"
        self.s3.put_object(
            Bucket=self.vault_bucket, Key=key, Body=markdown.encode("utf-8"),
            ContentType="text/markdown",
        )
        return {"status": "ok", **bench, "markdown": markdown, "vault_file_path": key}

    # --- narrative (the one LLM call; deterministic fallback) --------------
    def _narrate(self, stage: int, industry: str, distribution: dict[int, float]) -> str:
        at_or_below = sum(p for s, p in distribution.items() if s <= stage)
        dist_md = ", ".join(f"stage {s}: {distribution[s]:.0f}%" for s in _STAGES)
        user_text = (
            f"Client industry: {industry}\n"
            f"Client maturity stage: {stage} (of 5)\n"
            f"Peer distribution: {dist_md}\n"
            f"Approx. share of peers at or below the client's stage: {at_or_below:.0f}%\n\n"
            f"Write the benchmark note."
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
        peak = max(distribution, key=lambda s: distribution[s])
        posture = (
            "ahead of" if stage > peak else "in line with" if stage == peak else "behind"
        )
        return (
            f"At stage {stage}, this {industry} client is {posture} the peer median "
            f"(most peers cluster at stage {peak}). The priority is to execute the "
            f"stage-{stage} next moves and close the binding capability gap."
        )

    # --- slide markdown ----------------------------------------------------
    def _slide_markdown(self, bench: dict[str, Any]) -> str:
        stage = bench["client_stage"]
        dist = bench["peer_distribution"]
        bars = "\n".join(
            f"| Stage {s} | {dist[s]:.0f}% |" + (" **← client**" if s == stage else "")
            for s in _STAGES
        )
        moves = "\n".join(f"- {m}" for m in bench["common_next_moves"]) or "- (none)"
        uc = "\n".join(f"- {u}" for u in bench["typical_use_cases_at_stage"].get(stage, []))
        fm = export_frontmatter(
            "benchmark",
            {
                "assessment_id": bench["assessment_id"],
                "title": f"AI Maturity Benchmark — {bench['industry']} (Stage {stage})",
                "industry": bench["industry"],
                "client_stage": stage,
                "created_at": _now_iso(),
            },
        )
        return (
            f"{fm}\n# AI Maturity Benchmark — {bench['industry'].title()}\n\n"
            f"**Client is at stage {stage} of 5.**\n\n"
            f"{bench['narrative']}\n\n"
            f"## Peer distribution\n\n| Stage | Peers | |\n|---|---|---|\n{bars}\n\n"
            f"## Typical use cases at stage {stage}\n\n{uc or '- (n/a)'}\n\n"
            f"## Common next moves\n\n{moves}\n"
        )


def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()
