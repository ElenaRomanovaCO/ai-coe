"""AGENT-04 — Engagement Kit Builder (Module 3), Sonnet 4.6 tier.

Composes a tailored "engagement kit" from the vault: it selects relevant files
across categories (architecture/templates from assets, governance from regs,
intelligence from feed, tools from tools), writes a templated README narrating
why each is included, bundles everything into a zip in the **sessions** bucket
(not the vault — kits must not be re-embedded), and returns a presigned download
URL.

Mechanical/deterministic selection (same approach as the other module agents);
the README is templated, not LLM-authored (LLM narrative is a later enhancement).

Operations (dispatched from :meth:`handle` on ``op``):
  - ``preview`` (default) — auto-select files + render README → manifest (no zip)
  - ``search_vault``      — candidate files for the add/swap picker
  - ``generate``          — write the zip from a (possibly edited) file list → URL
"""

from __future__ import annotations

import io
import os
import uuid
import zipfile
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from agents.lib import models as lib_models

from .agent_03_asset_library import _slug, _split_frontmatter
from .base import ModuleAgent

AGENT_ID = "AGENT-04"

ARCH_TYPES = {"reference-architecture", "solution-pattern"}
# category -> vault prefix for the non-asset categories.
CATEGORY_PREFIX = {"governance": "regs/", "intelligence": "feed/", "tools": "tools/"}
CATEGORY_RATIONALE = {
    "architecture": "Reference architecture/pattern to anchor the solution shape.",
    "templates": "Template to run the engagement's working sessions.",
    "governance": "Governance/regulatory reference to keep the work compliant.",
    "intelligence": "Recent market/technology signal relevant to the engagement.",
    "tools": "Tooling reference for the delivery team.",
}
PER_CATEGORY = {"architecture": 3, "templates": 3, "governance": 2, "intelligence": 2, "tools": 2}


class KitFile(BaseModel):
    category: str
    source_path: str
    target_path: str
    title: str = ""
    rationale: str = ""


class KitManifest(BaseModel):
    kit_id: str
    kit_slug: str
    files: list[KitFile] = Field(default_factory=list)
    readme_markdown: str = ""
    download_url: str | None = None


def _basename(key: str) -> str:
    return key.rsplit("/", 1)[-1]


class KitBuilderAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.SONNET_4_6

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        sessions_bucket: str | None = None,
        region: str = lib_models.REGION,
        s3: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.region = region
        self._s3 = s3

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        op = args.get("op", "preview")
        if op == "search_vault":
            return self.run_tool("search_vault", lambda _u: self._search(args))
        if op == "generate":
            if not args.get("display_name"):
                return {"status": "error", "message": "display_name is required."}
            return self.run_tool("generate_kit", lambda _u: self._generate(args))
        return self.run_tool("preview_kit", lambda _u: self._preview(args))

    # --- vault helpers -----------------------------------------------------
    def _list_prefix(self, prefix: str) -> list[tuple[str, dict]]:
        out: list[tuple[str, dict]] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": prefix}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            for obj in resp.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".md") and "/_metadata/" not in key:
                    fm, _ = _split_frontmatter(self._read(key))
                    out.append((key, fm))
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
        return out

    def _read(self, key: str) -> str:
        return self.s3.get_object(Bucket=self.vault_bucket, Key=key)["Body"].read().decode("utf-8")

    @staticmethod
    def _title(key: str, fm: dict) -> str:
        return str(fm.get("title") or _basename(key).removesuffix(".md"))

    # --- selection ---------------------------------------------------------
    def _select(self, criteria: dict[str, Any], kit_slug: str) -> list[KitFile]:
        industry = (criteria.get("industry") or "").lower()
        stage = int(criteria.get("ai_stage", 2) or 2)
        files: list[KitFile] = []

        def add(category: str, key: str, fm: dict) -> None:
            files.append(
                KitFile(
                    category=category,
                    source_path=key,
                    target_path=f"{kit_slug}/{category}/{_basename(key)}",
                    title=self._title(key, fm),
                    rationale=CATEGORY_RATIONALE.get(category, ""),
                )
            )

        # Architecture + templates from assets matching industry + stage proximity.
        assets = self._list_prefix("assets/")

        def stage_ok(fm: dict) -> bool:
            s = int(fm.get("ai_stage", 0) or 0)
            return stage - 1 <= s <= stage + 1

        def ind_ok(fm: dict) -> bool:
            i = (fm.get("industry") or "").lower()
            return not industry or i == industry or i == "cross-industry"

        def dist(item: tuple[str, dict]) -> tuple:
            return (abs(int(item[1].get("ai_stage", 0) or 0) - stage), item[0])

        matched = sorted([a for a in assets if ind_ok(a[1]) and stage_ok(a[1])], key=dist)
        arch = [a for a in matched if a[1].get("type") in ARCH_TYPES]
        templ = [a for a in matched if a[1].get("type") not in ARCH_TYPES]
        for key, fm in arch[: PER_CATEGORY["architecture"]]:
            add("architecture", key, fm)
        for key, fm in templ[: PER_CATEGORY["templates"]]:
            add("templates", key, fm)

        for category, prefix in CATEGORY_PREFIX.items():
            items = sorted(self._list_prefix(prefix), key=lambda x: x[0])
            for key, fm in items[: PER_CATEGORY[category]]:
                add(category, key, fm)

        # Explicit overrides (asset ids) — include if not already present.
        present = {f.source_path for f in files}
        for asset_id in criteria.get("overrides") or []:
            hit = next((a for a in assets if str(a[1].get("id")) == asset_id), None)
            if hit and hit[0] not in present:
                add("architecture", hit[0], hit[1])
        return files

    # --- README ------------------------------------------------------------
    def _readme(self, criteria: dict[str, Any], files: list[KitFile]) -> str:
        industry = criteria.get("industry") or "general"
        stage = criteria.get("ai_stage", 2)
        etype = criteria.get("engagement_type") or "engagement"
        weeks = criteria.get("duration_weeks")
        extra = criteria.get("extra_context") or ""

        lines = [
            f"# Engagement Kit — {etype.title()} · {industry.title()} · Stage {stage}",
            "",
            f"A starter pack for a {weeks}-week {etype} engagement"
            + (f" in {industry}" if industry else "")
            + f", targeted at AI maturity stage {stage}.",
        ]
        if extra:
            lines += ["", f"> {extra}"]
        lines += ["", f"## What's inside ({len(files)} files)", ""]

        order = ["architecture", "templates", "governance", "intelligence", "tools"]
        for cat in order:
            cat_files = [f for f in files if f.category == cat]
            if not cat_files:
                continue
            lines.append(f"### {cat.title()}")
            for f in cat_files:
                lines.append(f"- **{f.title}** — {f.rationale} (`{f.target_path}`)")
            lines.append("")

        lines += [
            "## How to use this kit",
            "",
            "1. Start with the **architecture** references to anchor the solution shape.",
            "2. Run your sessions with the **templates**.",
            "3. Check the **governance** materials before launch.",
            "4. Skim the **intelligence** items for what's current.",
            "",
        ]
        return "\n".join(lines)

    # --- operations --------------------------------------------------------
    def _preview(self, args: dict[str, Any]) -> dict[str, Any]:
        kit_slug = self._kit_slug(args)
        files = self._select(args, kit_slug)
        manifest = KitManifest(
            kit_id="kit-" + uuid.uuid4().hex[:12],
            kit_slug=kit_slug,
            files=files,
            readme_markdown=self._readme(args, files),
        )
        return {"status": "ok", **manifest.model_dump()}

    def _search(self, args: dict[str, Any]) -> dict[str, Any]:
        query = (args.get("query") or "").strip().lower()
        content_types = args.get("content_types") or ["assets", "regs", "feed", "tools"]
        limit = int(args.get("limit", 10))
        results: list[dict] = []
        for ct in content_types:
            prefix = ct if ct.endswith("/") else f"{ct}/"
            for key, fm in self._list_prefix(prefix):
                title = self._title(key, fm)
                hay = f"{title} {' '.join(str(t) for t in (fm.get('tags') or []))}".lower()
                if not query or query in hay:
                    results.append(
                        {"source_path": key, "title": title, "content_type": prefix.rstrip("/")}
                    )
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break
        return {"status": "ok", "files": results}

    def _kit_slug(self, args: dict[str, Any]) -> str:
        etype = args.get("engagement_type") or "engagement"
        industry = _slug(args.get("industry") or "general")
        stage = args.get("ai_stage", 2)
        return f"{_slug(etype)}-{industry}-stage{stage}"

    def _generate(self, args: dict[str, Any]) -> dict[str, Any]:
        kit_slug = self._kit_slug(args)
        # Use the (possibly edited) file list from the UI, else auto-select.
        provided = args.get("files")
        if provided:
            files = []
            for f in provided:
                key = f["source_path"]
                category = f.get("category", "architecture")
                fm, _ = _split_frontmatter(self._read(key))
                files.append(
                    KitFile(
                        category=category,
                        source_path=key,
                        target_path=f"{kit_slug}/{category}/{_basename(key)}",
                        title=self._title(key, fm),
                        rationale=CATEGORY_RATIONALE.get(category, ""),
                    )
                )
        else:
            files = self._select(args, kit_slug)

        readme = self._readme(args, files)
        ts = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(f"{kit_slug}/README.md", readme)
            for kf in files:
                obj = self.s3.get_object(Bucket=self.vault_bucket, Key=kf.source_path)
                z.writestr(kf.target_path, obj["Body"].read())

        zip_key = f"kits/{_slug(args['display_name'])}/{ts}/{kit_slug}.zip"
        self.s3.put_object(
            Bucket=self.sessions_bucket,
            Key=zip_key,
            Body=buf.getvalue(),
            ContentType="application/zip",
        )
        url = self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.sessions_bucket, "Key": zip_key},
            ExpiresIn=3600,
        )
        manifest = KitManifest(
            kit_id="kit-" + uuid.uuid4().hex[:12],
            kit_slug=kit_slug,
            files=files,
            readme_markdown=readme,
            download_url=url,
        )
        return {"status": "ok", "zip_key": zip_key, **manifest.model_dump()}
