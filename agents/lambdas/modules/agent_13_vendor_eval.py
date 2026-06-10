"""AGENT-13 — Vendor & Model Evaluation Center (Module 13), Sonnet 4.6 tier.

Browse the structured vendor/model evaluations in ``vault/vendors/`` (filter by
category, flag stale entries), open one, or build a custom side-by-side comparison
from 2-4 selected evaluations and export it as markdown.

**Orchestration is mechanical** (the AGENT-05/24 precedent,
``vault/decisions/agent-05-orchestration.md``): the comparison table is assembled
deterministically from the evaluations' frontmatter, and the Sonnet model is used for
**one thing only** — the 3-5 cross-cutting insights — with a deterministic fallback if
it fails. ``list``/``get``/``flag_stale`` never call the model. No workers.

Operations (on ``op``):
  - ``list_evaluations``  — filter + staleness, newest-verified first (default)
  - ``get_evaluation``    — one evaluation's body + frontmatter
  - ``build_comparison``  — 2-4 evaluations → side-by-side markdown table + insights
  - ``flag_stale``        — staleness verdict from ``last_verified`` (one or all)

Comparisons are ephemeral (no persistence; the web slice downloads the markdown),
matching the spec's request models — there is no get/list of past comparisons.
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import UTC, date, datetime
from typing import Any

from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .agent_03_asset_library import _split_frontmatter
from .base import ModuleAgent

AGENT_ID = "AGENT-13"
VENDORS_PREFIX = "vendors/"
VENDOR_EVAL_ROUTE = "/modules/vendor-eval"
# Evaluations recommend re-verifying quarterly; flag anything older than a quarter.
STALE_DAYS = 90
_H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_H2_SECTION = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_MAX_COMPARE = 4


def _today() -> date:
    return datetime.now(UTC).date()


def _parse_date(value: Any) -> date | None:
    s = str(value or "").strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def _title_from_body(body: str, fallback: str) -> str:
    m = _H1.search(body)
    return m.group(1).strip() if m else fallback


def _section(body: str, name_re: str) -> str:
    """Return the text of the first ``##`` section whose heading matches name_re."""
    matches = list(_H2_SECTION.finditer(body))
    pat = re.compile(name_re, re.IGNORECASE)
    for i, m in enumerate(matches):
        if pat.search(m.group(1)):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            return body[start:end].strip()
    return ""


def _first_sentence(text: str, limit: int = 240) -> str:
    text = " ".join(text.split())
    m = re.search(r"(.+?[.!?])(\s|$)", text)
    out = m.group(1) if m else text
    return out if len(out) <= limit else out[: limit - 1].rstrip() + "…"


class VendorEvalAgent(ModuleAgent):
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
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
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
        if "evaluation_id" not in args and args.get("id"):
            args = {**args, "evaluation_id": args["id"]}
        op = args.get("op")
        if op == "get_evaluation" or (op is None and args.get("evaluation_id")):
            return self.run_tool("get_evaluation", lambda _u: self._get(args))
        if op == "build_comparison" or (op is None and args.get("evaluation_ids")):
            return self.run_tool("build_comparison", lambda _u: self._build_comparison(args))
        if op == "flag_stale":
            return self.run_tool("flag_stale", lambda _u: self._flag_stale(args))
        return self.run_tool("list_evaluations", lambda _u: self._list(args))

    # --- corpus I/O --------------------------------------------------------
    def _all_evals(self) -> list[tuple[dict, str, str]]:
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": VENDORS_PREFIX}
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
    def _eval_id(fm: dict, key: str) -> str:
        return str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md"))

    def _summary(self, fm: dict, body: str, key: str, as_of: date) -> dict[str, Any]:
        lv = _parse_date(fm.get("last_verified"))
        age = (as_of - lv).days if lv else None
        return {
            "id": self._eval_id(fm, key),
            "title": _title_from_body(body, self._eval_id(fm, key)),
            "category": str(fm.get("category", "")),
            "vendors_compared": [str(v) for v in (fm.get("vendors_compared") or [])],
            "criteria": [str(c) for c in (fm.get("criteria") or [])],
            "last_verified": str(fm.get("last_verified", "")),
            "stale": age is not None and age > STALE_DAYS,
            "age_days": age,
            "file_path": key,
        }

    def _load_eval(self, eval_id: str) -> tuple[dict, str, str] | None:
        target = str(eval_id)
        basename = f"/{target}.md"
        fallback: tuple[dict, str, str] | None = None
        for fm, body, key in self._all_evals():
            if self._eval_id(fm, key) == target:
                return fm, body, key
            if key.endswith(basename):
                fallback = (fm, body, key)
        return fallback

    # --- operations --------------------------------------------------------
    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        category = (args.get("category") or "").strip().lower()
        as_of = _today()
        out = []
        for fm, body, key in self._all_evals():
            s = self._summary(fm, body, key, as_of)
            if category and s["category"].lower() != category:
                continue
            out.append(s)
        # Newest-verified first; entries with no date sort last.
        out.sort(key=lambda e: e["last_verified"] or "", reverse=True)
        return {"status": "ok", "evaluations": out}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        eval_id = args.get("evaluation_id")
        if not eval_id:
            return {"status": "error", "message": "evaluation_id is required."}
        loaded = self._load_eval(eval_id)
        if loaded is None:
            return {
                "status": "not_found",
                "evaluation_id": eval_id,
                "message": "No such evaluation.",
            }
        fm, body, key = loaded
        as_of = _today()
        return {
            "status": "ok",
            "evaluation": {
                "id": self._eval_id(fm, key),
                "title": _title_from_body(body, self._eval_id(fm, key)),
                "frontmatter": fm,
                "body_markdown": body.strip(),
                "file_path": key,
                **{k: self._summary(fm, body, key, as_of)[k] for k in ("stale", "age_days")},
            },
        }

    def _flag_stale(self, args: dict[str, Any]) -> dict[str, Any]:
        as_of = _today()
        eval_id = args.get("evaluation_id")
        if eval_id:
            loaded = self._load_eval(eval_id)
            if loaded is None:
                return {"status": "not_found", "evaluation_id": eval_id}
            fm, body, key = loaded
            s = self._summary(fm, body, key, as_of)
            return {
                "status": "ok",
                "evaluation_id": s["id"],
                "last_verified": s["last_verified"],
                "age_days": s["age_days"],
                "stale": s["stale"],
                "threshold_days": STALE_DAYS,
            }
        stale = [
            {"id": s["id"], "last_verified": s["last_verified"], "age_days": s["age_days"]}
            for s in (
                self._summary(fm, body, key, as_of) for fm, body, key in self._all_evals()
            )
            if s["stale"]
        ]
        return {"status": "ok", "threshold_days": STALE_DAYS, "stale": stale}

    def _build_comparison(self, args: dict[str, Any]) -> dict[str, Any]:
        ids = [str(x) for x in (args.get("evaluation_ids") or []) if str(x).strip()]
        if not 2 <= len(ids) <= _MAX_COMPARE:
            return {
                "status": "error",
                "message": "Select between 2 and 4 evaluations to compare.",
            }
        as_of = _today()
        evals: list[dict[str, Any]] = []
        for eid in ids:
            loaded = self._load_eval(eid)
            if loaded is None:
                return {
                    "status": "not_found",
                    "evaluation_id": eid,
                    "message": f"No such evaluation '{eid}'.",
                }
            fm, body, key = loaded
            s = self._summary(fm, body, key, as_of)
            s["recommendation"] = _first_sentence(_section(body, r"recommendation")) or "—"
            evals.append(s)

        # Criteria rows: the requested subset, else the union across selected evals.
        requested = [str(c).strip() for c in (args.get("criteria") or []) if str(c).strip()]
        if requested:
            criteria = requested
        else:
            criteria = []
            for e in evals:
                for c in e["criteria"]:
                    if c not in criteria:
                        criteria.append(c)

        comparison_id = "cmp-" + uuid.uuid4().hex[:12]
        comparison_markdown = self._render_table(comparison_id, evals, criteria)
        insights = self._insights(evals, criteria)
        return {
            "status": "ok",
            "comparison_id": comparison_id,
            "evaluation_ids": [e["id"] for e in evals],
            "comparison_markdown": comparison_markdown,
            "insights": insights,
        }

    # --- deterministic markdown table --------------------------------------
    def _render_table(self, comparison_id: str, evals: list[dict], criteria: list[str]) -> str:
        cols = [e["title"] for e in evals]
        header = "| Attribute | " + " | ".join(cols) + " |"
        divider = "|" + "---|" * (len(cols) + 1)
        rows = [
            "| Category | " + " | ".join(e["category"] or "—" for e in evals) + " |",
            "| Vendors compared | "
            + " | ".join(", ".join(e["vendors_compared"]) or "—" for e in evals)
            + " |",
            "| Last verified | "
            + " | ".join(
                f"{e['last_verified'] or '—'}{' ⚠ stale' if e['stale'] else ''}" for e in evals
            )
            + " |",
        ]
        for c in criteria:
            cells = ["✓" if c in e["criteria"] else "—" for e in evals]
            rows.append(f"| {c} | " + " | ".join(cells) + " |")
        rows.append(
            "| Recommendation | " + " | ".join(e["recommendation"] for e in evals) + " |"
        )
        body = "\n".join([header, divider, *rows])
        return (
            f"# Vendor Comparison\n\n"
            f"_Comparison `{comparison_id}` of {len(evals)} evaluations._\n\n"
            f"{body}\n"
        )

    # --- LLM insights (the only model call) --------------------------------
    def _insights(self, evals: list[dict], criteria: list[str]) -> list[str]:
        titles = ", ".join(e["title"] for e in evals)
        lines = []
        for e in evals:
            lines.append(
                f"- {e['title']} ({e['category']}): "
                f"vendors {', '.join(e['vendors_compared']) or '—'}; "
                f"criteria {', '.join(e['criteria']) or '—'}; "
                f"last verified {e['last_verified'] or '—'}"
                f"{' [STALE]' if e['stale'] else ''}; recommendation: {e['recommendation']}"
            )
        shared = [c for c in criteria if all(c in e["criteria"] for e in evals)]
        user_text = (
            f"Evaluations being compared: {titles}\n\n"
            + "\n".join(lines)
            + f"\n\nShared criteria across all: {', '.join(shared) or 'none'}.\n\n"
            "Write 3-5 short, decision-useful insights contrasting these evaluations. "
            "Each insight one sentence. Do not invent data beyond what is given."
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
                    system=INSIGHTS_SYSTEM,
                    max_tokens=500,
                    usage=usage,
                )
            text = _extract_text(resp.get("output", {}).get("message", {}))
            parsed = _bullets(text)
            if parsed:
                return parsed[:5]
        except Exception:  # noqa: BLE001 — fall back to deterministic insights
            pass
        return self._fallback_insights(evals, shared)

    @staticmethod
    def _fallback_insights(evals: list[dict], shared: list[str]) -> list[str]:
        out = [
            f"Comparing {len(evals)} evaluations across categories: "
            f"{', '.join(sorted({e['category'] for e in evals if e['category']})) or '—'}.",
        ]
        if shared:
            out.append(f"All share these criteria: {', '.join(shared)}.")
        else:
            out.append("The evaluations share no common criteria — they assess different concerns.")
        stale = [e["title"] for e in evals if e["stale"]]
        if stale:
            out.append(
                f"Re-verify before relying on: {', '.join(stale)} "
                f"(past the {STALE_DAYS}-day window)."
            )
        else:
            out.append("All selected evaluations are within the re-verification window.")
        return out


INSIGHTS_SYSTEM = """You compare structured AI vendor/model evaluations for a delivery \
team. You are given several evaluations with their categories, vendors, criteria, \
verification dates, and recommendations. Produce 3-5 short, decision-useful insights \
that contrast them — overlaps, gaps, freshness, and what would drive a choice. Output \
ONLY a markdown bullet list (each line starting with '- '), one sentence per bullet. \
Do not invent data beyond what is provided."""


def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()


def _bullets(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^[-*]\s+(.*)$", line)
        if m and m.group(1).strip():
            out.append(m.group(1).strip())
    return out
