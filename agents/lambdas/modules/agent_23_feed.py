"""AGENT-23 — AI Intelligence Feed & Release Radar (Module 24), Sonnet 4.6 tier.

Lets a user browse the seeded feed items in ``vault/feed/`` personalized to their
profile (industries + AI stage focus + tech focus), open one to read it plus a tailored
"what this means for you" note, or view the quarterly tech radar grouped into
Adopt / Trial / Assess / Hold.

**Orchestration is mechanical**, following the AGENT-24 precedent
(``vault/decisions/agent-05-orchestration.md``): the two workers do the analysis and
AGENT-23 makes no LLM call of its own.

  - WORKER-10 item_classifier   — item + profile → relevance score (ranks the feed)
  - WORKER-11 commentary_writer  — item + profile → tailored note (the one LLM call,
    invoked lazily on ``get``; degrades to a deterministic note if Bedrock fails)

No Bedrock guardrail is applied (the module-agents role lacks ``ApplyGuardrail`` — see
``vault/decisions/asset-panel-no-guardrail.md``); WORKER-11's prompt is grounded in the
item body, so the risk is low.

Operations (on ``op``):
  - ``list``   — filter + personalized-rank the feed, return summaries (default)
  - ``get``    — one item's body + frontmatter + WORKER-11 commentary
  - ``radar``  — every item grouped by radar status into the 4 quadrants
"""

from __future__ import annotations

import os
from typing import Any

from agents.lambdas.modules.agent_03_asset_library import _split_frontmatter
from agents.lib import models as lib_models

from .base import ModuleAgent
from .worker_client import WorkerInvoker

AGENT_ID = "AGENT-23"
FEED_ROUTE = "/modules/intelligence-feed"
FEED_PREFIX = "feed/"

# The radar quadrants, in conventional left-to-right order.
RADAR_QUADRANTS = ("adopt", "trial", "assess", "hold")


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _norm_list(values: Any) -> list[str]:
    return [_norm(v) for v in (values or []) if str(v).strip()]


class FeedAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.SONNET_4_6

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        region: str = lib_models.REGION,
        s3: Any = None,
        worker_invoker: WorkerInvoker | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.region = region
        self._s3 = s3
        self.workers = worker_invoker or WorkerInvoker(region=region)

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        # Liberal aliasing: the orchestrator/web may send ``id`` for ``item_id``.
        if "item_id" not in args and args.get("id"):
            args = {**args, "item_id": args["id"]}
        op = args.get("op")
        if op == "radar":
            return self.run_tool("get_radar", lambda _u: self._radar(args))
        if op == "get" or (op is None and args.get("item_id")):
            return self.run_tool("get_feed_item", lambda _u: self._get(args))
        return self.run_tool("list_feed_items", lambda _u: self._list(args))

    # --- feed corpus I/O ---------------------------------------------------
    def _all_items(self) -> list[tuple[dict, str, str]]:
        """(frontmatter, body, key) for every feed markdown file."""
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": FEED_PREFIX}
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
    def _item_id(fm: dict, key: str) -> str:
        return str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md"))

    @staticmethod
    def _summary_of(fm: dict, key: str) -> dict[str, Any]:
        return {
            "id": FeedAgent._item_id(fm, key),
            "title": str(fm.get("title", "")),
            "category": str(fm.get("category", "")),
            "industries": [str(s) for s in (fm.get("industries") or [])],
            "tags": [str(t) for t in (fm.get("tags") or [])],
            "radar_status": None if fm.get("radar_status") is None else str(fm.get("radar_status")),
            "published_at": str(fm.get("published_at", "")),
            "source_url": str(fm.get("source_url", "")),
            "file_path": key,
        }

    @staticmethod
    def _profile_from(args: dict[str, Any]) -> dict[str, Any]:
        """Build the WORKER profile from explicit user_profile and/or list filters."""
        profile = dict(args.get("user_profile") or {})
        industries = _norm_list(profile.get("industries"))
        # A single ``industry`` filter doubles as a profile industry for scoring.
        industry = _norm(args.get("industry"))
        if industry and industry not in industries:
            industries.append(industry)
        return {
            "industries": industries,
            "ai_stage": profile.get("ai_stage", args.get("ai_stage")),
            "tech_focus": _norm_list(profile.get("tech_focus") or args.get("tech_focus")),
        }

    def _load_item(self, item_id: str) -> tuple[dict, str, str] | None:
        """Resolve an item by frontmatter id (basename fallback), like AGENT-24 get."""
        target = str(item_id)
        basename = f"/{target}.md"
        fallback: tuple[dict, str, str] | None = None
        for fm, body, key in self._all_items():
            if self._item_id(fm, key) == target:
                return fm, body, key
            if key.endswith(basename):
                fallback = (fm, body, key)
        return fallback

    # --- operations --------------------------------------------------------
    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        category = _norm(args.get("category"))
        industry = _norm(args.get("industry"))
        radar_status = _norm(args.get("radar_status"))
        profile = self._profile_from(args)

        scored: list[tuple[float, str, dict[str, Any]]] = []
        for fm, _body, key in self._all_items():
            summary = self._summary_of(fm, key)
            item_industries = [_norm(i) for i in summary["industries"]]
            item_radar = _norm(summary["radar_status"])

            if category and _norm(summary["category"]) != category:
                continue
            if industry and industry not in item_industries:
                # An industry filter still admits broadly-relevant cross-industry items.
                if "cross-industry" not in item_industries:
                    continue
            if radar_status and item_radar != radar_status:
                continue

            result = self.workers.invoke(
                "WORKER-10", {"frontmatter": fm, "user_profile": profile}
            )
            ok = result.get("status") == "ok"
            score = float(result.get("relevance_score", 0.0)) if ok else 0.0
            summary["relevance_score"] = score
            summary["matched"] = result.get("matched", {}) if ok else {}
            scored.append((score, summary["published_at"], summary))

        # Highest relevance first; newest first as the tie-break.
        scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return {"status": "ok", "items": [s for _score, _date, s in scored]}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        item_id = args.get("item_id")
        if not item_id:
            return {"status": "error", "message": "item_id is required."}
        loaded = self._load_item(item_id)
        if loaded is None:
            return {"status": "not_found", "item_id": item_id, "message": "No such feed item."}
        fm, body, key = loaded
        profile = self._profile_from(args)

        commentary = self.workers.invoke(
            "WORKER-11", {"item": {"frontmatter": fm, "body": body}, "user_profile": profile}
        )
        if commentary.get("status") != "ok":
            commentary = {"commentary": "", "industry": "", "ai_stage": None, "tailored": False}

        item = {
            "id": self._item_id(fm, key),
            "title": str(fm.get("title", "")),
            "frontmatter": fm,
            "body_markdown": body.strip(),
            "file_path": key,
        }
        return {
            "status": "ok",
            "item": item,
            "summary": self._summary_of(fm, key),
            "commentary": {
                "commentary": commentary.get("commentary", ""),
                "industry": commentary.get("industry", ""),
                "ai_stage": commentary.get("ai_stage"),
                "tailored": commentary.get("tailored", False),
            },
        }

    def _radar(self, args: dict[str, Any]) -> dict[str, Any]:
        quadrants: dict[str, list[dict[str, Any]]] = {q: [] for q in RADAR_QUADRANTS}
        for fm, _body, key in self._all_items():
            status = _norm(fm.get("radar_status"))
            if status in quadrants:
                quadrants[status].append(self._summary_of(fm, key))
        for items in quadrants.values():
            items.sort(key=lambda s: s["published_at"], reverse=True)
        return {"status": "ok", **quadrants}
