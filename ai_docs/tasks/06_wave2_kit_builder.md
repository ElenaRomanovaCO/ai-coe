# Task: Wave 2 — Engagement Kit Builder (Module 3, AGENT-04)

> **Phase:** 2
> **Feature group:** Wave 2 (Assessment & Delivery)
> **Covers:** FR-020 (start from Chat), FR-021 (zip with README), FR-022 (preview + swap items)
> **Builds:** AGENT-04 (Engagement Kit Builder, Sonnet 4.6)
> **Depends on:** 00, 01, 02, 03
> **Blocks:** none
> **Estimated effort:** 2-3 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** User states engagement context (industry, stage, engagement type) and gets a zip containing 8-15 relevant markdown files plus an auto-written one-page kit README.

**Build steps:**

1. AGENT-04 in ModuleAgentsLambda (Sonnet 4.6, 4 tools: search_vault, get_asset, write_kit_files, zip_kit).
2. Flip Module 3 enabled in modules.json.
3. `/modules/kit-builder` page: form (industry, stage, engagement type, duration, free-text context) → preview screen with swap/add/remove → Generate Kit button → download.
4. Kit folder structure: `kits/{display_name}/{ts}/{kit-slug}/` with subfolders (architecture/, templates/, governance/, intelligence/, README.md).
5. Smoke test: build a kit for healthcare stage 2 discovery → 8-12 files + README → download zip → contents match.

**Files to create/edit:**

- `agents/lambdas/modules/agent_04_kit_builder.py`
- `vault/modules.json` — flip Module 3
- `web/app/(authenticated)/modules/kit-builder/page.tsx`
- `web/app/(authenticated)/modules/kit-builder/actions.ts`
- `web/components/KitPreview.tsx`
- `web/lib/zip.ts` — client-side zip helper (or server-side via JSZip / zip in Lambda)

**Done when:**

- [ ] FRs 020-022 verified
- [ ] Kit downloads cleanly, opens as a labeled folder
- [ ] README references each included file
- [ ] User can swap items before download
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Engagement Kit Builder (Module 3, AGENT-04)** for the AI CoE Platform. Tasks 00-05 are done.

#### Project context

- Kit Builder is a composition module: it selects files from the vault and writes a coherent README narrative around them.
- It pulls from Asset Library (Module 2), Compliance Tracker (Module 25, not yet built — handle absence gracefully), and Tools Repository (Module 7, not yet built).

#### Agent spec (AGENT-04)

```python
class BuildKitRequest(BaseModel):
    display_name: str
    industry: str
    ai_stage: int
    engagement_type: Literal["discovery", "pilot", "scale", "optimize"]
    duration_weeks: int
    extra_context: str | None = None
    overrides: list[str] | None = None              # explicit asset IDs to include

class KitManifest(BaseModel):
    kit_id: str
    files: list[KitFile]                            # category, source_path, target_path_in_zip
    readme_markdown: str
    download_url: str                               # presigned S3 URL, 1h TTL

class KitFile(BaseModel):
    category: Literal["architecture", "templates", "governance", "intelligence", "tools"]
    source_path: str                                # vault path
    target_path: str                                # path inside zip
    rationale: str                                  # why this file was included (for README)
```

Tools (4):
- `search_vault(query, content_types, limit)` → list[VaultFile]
- `get_asset(asset_id)` → AssetDetail
- `write_kit_files(manifest)` → writes files to `kits/{display_name}/{ts}/{kit_slug}/` and the README; returns S3 keys
- `zip_kit(kit_id)` → produces a presigned URL for download

System prompt outline: build a coherent kit, not a random pile. Group by category. README must explain why each file is in the kit and how the consultant should use it during the engagement.

#### modules.json entry
```json
{
  "id": "module-3",
  "name": "Engagement Kit Builder",
  "wave": 2,
  "purpose": "Assemble a tailored engagement starter pack of vault files with a one-page README.",
  "when_to_use": ["Start a new engagement", "Prepare a discovery workshop", "Hand off to a delivery team"],
  "example_queries": ["Build me a kit for a healthcare client at stage 2", "I have a fraud detection pilot starting next week", "Create a discovery kit for retail"],
  "agent_id": "AGENT-04",
  "model_tier": "sonnet-4-6",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps

1. Agent + 4 tools per spec.
2. `/modules/kit-builder/page.tsx`: form with shadcn Form components.
3. On submit: call `build_kit_action` (server action) → AGENT-04 returns manifest.
4. Preview screen: shows manifest, allows add/remove/swap. Add/swap pull from `search_vault`.
5. On confirm: AGENT-04 finalizes files in S3, returns presigned URL, browser triggers download.
6. Smoke test: build a kit for fintech stage 3 pilot → 10-15 files, README references each, zip extracts cleanly.

#### Definition of done
- [ ] FRs 020-022 verified
- [ ] Zip integrity verified
- [ ] README narrative coherent
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Real-time collaborative editing of kits (post-demo)
- Kit versioning (post-demo)
- Kit sharing with non-platform users (Module 14, Wave 6 covers Client Report sharing; kits remain internal)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 020-022, AGENT-04
- Design: Section 5.2 AGENT-04
- Foundation: `ai_docs/tasks/00_foundation.md`
