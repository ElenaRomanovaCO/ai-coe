"""WORKER-04 — regulation_finder (deterministic, structured-filter + keyword relevance).

Scores the seeded regulations in ``vault/regs/`` against an engagement context
(industry, geography, data types, AI use-case type) and returns the relevant ones,
most-relevant first. Scoring is **soft**, not a hard gate: a regulation can surface
on industry + data-type relevance even when its geography differs (e.g. HIPAA still
applies to PHI for a healthcare use case framed as EU), which matches the task's
smoke expectation (healthcare + EU + PHI → EU AI Act *and* HIPAA).

Deterministic and fully testable (no Bedrock, no S3 Vectors) — the regulation corpus
is small and structured, so a list-parse-score pass over ``regs/`` is simpler and more
predictable than semantic search, consistent with the other Layer-3 workers
(``vault/decisions/worker-pattern.md``). Reuses AGENT-03's frontmatter splitter rather
than duplicating YAML parsing.
"""

from __future__ import annotations

import os
import re
from typing import Any

from pydantic import BaseModel, Field

from agents.lambdas.modules.agent_03_asset_library import _split_frontmatter

from .base import Worker

WORKER_ID = "WORKER-04"
REGS_PREFIX = "regs/"
DEFAULT_TOP_K = 8

_H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

# Normalize free-text geography to the `geo` values used in reg frontmatter.
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


class RegulationMatch(BaseModel):
    id: str
    name: str
    geo: str = ""
    relevance_score: int = 0
    applicable_clauses: list[str] = Field(default_factory=list)
    file_path: str = ""
    tags: list[str] = Field(default_factory=list)


class RegulationFinderWorker(Worker):
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
        return self.run_tool("find_regulations", lambda _u: self._find(args))

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

    def _find(self, args: dict[str, Any]) -> dict[str, Any]:
        industry = (args.get("industry") or "").strip().lower()
        geo = _norm_geo(args.get("geography") or "")
        data_types = [
            str(d).strip().lower() for d in (args.get("data_types") or []) if str(d).strip()
        ]
        use_case = (args.get("ai_use_case_type") or "").strip().lower()
        # Use-case word tokens (3+ chars) used for soft keyword relevance.
        use_tokens = {t for t in re.split(r"[^a-z0-9]+", use_case) if len(t) >= 3}
        top_k = int(args.get("top_k", DEFAULT_TOP_K))

        scored: list[tuple[int, RegulationMatch]] = []
        for fm, md, key in self._all_regs():
            scope = [str(s).lower() for s in (fm.get("industry_scope") or [])]
            tags = [str(t).lower() for t in (fm.get("tags") or [])]
            reg_geo = str(fm.get("geo") or "").lower()
            name = str(fm.get("name") or "").lower()

            geo_match = bool(geo) and reg_geo == geo
            is_cross = "cross-industry" in scope
            industry_in_scope = bool(industry) and industry in scope
            scope_specific = any(s != "cross-industry" for s in scope)
            data_match = sum(1 for d in data_types if any(d in t for t in tags))
            hay = set(tags) | {w for t in (tags + [name]) for w in re.split(r"[^a-z0-9]+", t)}
            usecase_match = min(3, sum(1 for w in use_tokens if w in hay))

            # Industry gate: a reg scoped to specific industries that exclude this
            # engagement's industry only applies if a data type pulls it in (e.g. PHI
            # → HIPAA across industries). This stops a healthcare-only reg surfacing
            # for a financial use case just because both are US-federal.
            if scope_specific and not is_cross and not industry_in_scope and data_match == 0:
                continue
            # Relevance: geography, industry, a data type, or a use-case keyword must
            # connect — a shared jurisdiction alone is not enough for an off-industry reg.
            if not (geo_match or industry_in_scope or data_match or usecase_match):
                continue

            score = (
                (3 if geo_match else 0)
                + (2 if industry_in_scope else 0)
                + (1 if is_cross else 0)
                + data_match
                + usecase_match
            )
            clauses = _H2.findall(md)[:4]
            scored.append(
                (
                    score,
                    RegulationMatch(
                        id=str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md")),
                        name=str(fm.get("name", "")),
                        geo=reg_geo,
                        relevance_score=score,
                        applicable_clauses=clauses,
                        file_path=key,
                        tags=tags,
                    ),
                )
            )

        scored.sort(key=lambda pair: (-pair[0], pair[1].name))
        regulations = [m.model_dump() for _, m in scored[:top_k]]
        return {"status": "ok", "regulations": regulations}
