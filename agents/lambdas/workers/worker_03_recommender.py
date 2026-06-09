"""WORKER-03 — recommender (deterministic, filter-based).

Filters the Asset Library by industry and stage proximity (stage-1 .. stage+1),
boosts assets whose tags relate to the weak dimensions, and returns the top 5.
Reuses AGENT-03's frontmatter helpers (same reuse pattern as AGENT-16) rather
than duplicating asset parsing.
"""

from __future__ import annotations

import os
from typing import Any

from agents.lambdas.modules.agent_03_asset_library import (
    ASSET_PREFIX,
    AssetSummary,
    _split_frontmatter,
    _summary_from_frontmatter,
)

from .base import Worker

WORKER_ID = "WORKER-03"


class RecommenderWorker(Worker):
    agent_id = WORKER_ID

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        region: str = "us-east-1",
        s3: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.region = region
        self._s3 = s3

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.run_tool("recommend", lambda _u: self._recommend(args))

    def _all_assets(self) -> list[AssetSummary]:
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": ASSET_PREFIX}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            for obj in resp.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".md") and "/_metadata/" not in key:
                    keys.append(key)
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")

        out: list[AssetSummary] = []
        for key in keys:
            body = self.s3.get_object(Bucket=self.vault_bucket, Key=key)["Body"].read()
            fm, _ = _split_frontmatter(body.decode("utf-8"))
            out.append(_summary_from_frontmatter(fm, key))
        return out

    def _recommend(self, args: dict[str, Any]) -> dict[str, Any]:
        stage = int(args.get("stage", 2))
        industry = (args.get("industry") or "").strip().lower()
        weak = {w.lower() for d in (args.get("weak_dimensions") or []) for w in d.split("_")}
        top_k = int(args.get("top_k", 5))

        assets = self._all_assets()

        def in_stage(a: AssetSummary) -> bool:
            return stage - 1 <= a.ai_stage <= stage + 1

        def industry_ok(a: AssetSummary) -> bool:
            if not industry:
                return True
            return a.industry.lower() == industry or a.industry.lower() == "cross-industry"

        def boost(a: AssetSummary) -> int:
            hay = {t.lower() for t in a.tags} | {a.type.lower()}
            return sum(1 for w in weak if any(w in h for h in hay))

        primary = [a for a in assets if in_stage(a) and industry_ok(a)]
        # Relax to stage-only, then to everything, to always fill up to top_k.
        pool = primary or [a for a in assets if in_stage(a)] or assets

        ranked = sorted(
            pool,
            key=lambda a: (-boost(a), abs(a.ai_stage - stage), a.title),
        )
        return {
            "status": "ok",
            "recommendations": [a.model_dump() for a in ranked[:top_k]],
        }
