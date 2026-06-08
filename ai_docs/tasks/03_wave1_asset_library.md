# Task: Wave 1 — Asset Library (Module 2, AGENT-03)

> **Phase:** 1
> **Feature group:** Wave 1 (Foundation)
> **Covers:** FR-010 (browse filtered), FR-011 (view rendered asset), FR-012 (save to dashboard), FR-013 (rate/flag)
> **Builds:** AGENT-03 (Asset Library, Haiku 4.5)
> **Depends on:** 00_foundation, 01_wave1_vault_seed_content, 02_wave1_chat_orchestrator
> **Blocks:** any task that links to Asset Library entries (Chat citations, Kit Builder, Recommendations)
> **Estimated effort:** 2-3 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** A user can browse the seeded assets at `/modules/asset-library`, filter by industry / stage / type, open any asset to see rendered markdown with frontmatter sidebar, save assets, and rate/flag.

**Build steps:**

1. **Add AGENT-03 to ModuleAgentsLambda** (Haiku 4.5, 3 tools: list_assets, get_asset, search_vector_index) → Verify: unit tests pass.
2. **Register AGENT-03 in modules.json** (set enabled=true for Module 2) → Verify: Chat's `list_modules` includes it.
3. **Build `/modules/asset-library` page** (filters, asset grid, search box) → Verify: page renders all seed assets.
4. **Build `/modules/asset-library/[id]` page** (rendered markdown + frontmatter sidebar) → Verify: opening any asset shows it.
5. **Save + Rate + Flag** (writes to user profile JSON + asset metadata) → Verify: saved assets appear on dashboard (task 04 dependency).
6. **Wire Chat citations** to link to `/modules/asset-library/{id}` → Verify: clicking a Chat citation opens the asset page.

**Files to create/edit:**

- `agents/lambdas/modules/agent_03_asset_library.py` — AGENT-03 implementation
- `agents/lambdas/modules/router.py` — register AGENT-03 in the Lambda router
- `vault/modules.json` — flip Module 2 enabled=true
- `web/app/(authenticated)/modules/asset-library/page.tsx` — browse view
- `web/app/(authenticated)/modules/asset-library/[id]/page.tsx` — detail view
- `web/app/(authenticated)/modules/asset-library/actions.ts` — server actions (list, get, save, rate, flag)
- `web/components/AssetCard.tsx` — card component
- `web/components/FrontmatterPanel.tsx` — sidebar
- `web/components/MarkdownRenderer.tsx` — markdown rendering (shadcn typography + remark/rehype)

**Done when:**

- [ ] All listed FRs have smoke tests
- [ ] Grid lists 10+ seed assets, filters work
- [ ] Detail page renders markdown + frontmatter
- [ ] Saving an asset updates user profile JSON
- [ ] Chat citations route to asset detail
- [ ] DoD checklist from `00_foundation.md` passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing the **Asset Library (Module 2, AGENT-03)** for the AI CoE Platform. Foundation (task 00), vault content (task 01), and Chat orchestrator (task 02) are done.

#### Project context

- AGENT-03 is a Layer 2 module agent. It runs inside ModuleAgentsLambda (one Lambda for 26 agents, internal Strands routing per AD-01).
- Asset Library is read-mostly. Most work is UI; agent is thin.
- The vault has seed assets under `vault/assets/{industry}/{stage}/*.md` with `AssetFrontmatter` schema (see task 01).

#### Agent specification (AGENT-03)

```python
class ListAssetsRequest(BaseModel):
    industry: str | None = None
    ai_stage: int | None = None
    asset_type: str | None = None
    tags: list[str] | None = None
    query: str | None = None
    limit: int = 50

class AssetSummary(BaseModel):
    id: str
    title: str
    type: str
    industry: str
    ai_stage: int
    tags: list[str]
    file_path: str
    updated_at: str

class GetAssetRequest(BaseModel):
    asset_id: str

class AssetDetail(BaseModel):
    summary: AssetSummary
    body_markdown: str
    frontmatter: dict
```

Tools (3):
- `list_assets(filters)` → list[AssetSummary] (reads vault listing, optional vector search)
- `get_asset(asset_id)` → AssetDetail (reads file from S3)
- `search_vector_index(query, top_k)` → list[AssetSummary] (S3 Vectors filtered by content_type=asset)

Model tier: Haiku 4.5 (mostly mechanical retrieval, occasional natural-language search).

#### UI specification

- **`/modules/asset-library`**:
  - Header: "Asset Library" + count
  - Left sidebar: filters (industry checkboxes, AI stage slider 0-5, type checkboxes, tag multiselect, search box)
  - Main: grid of AssetCard components (title, type badge, industry, stage, save/flag buttons, rating stars)
  - Pagination: 24 cards per page
- **`/modules/asset-library/[id]`**:
  - Header: title, type, industry, stage badges, breadcrumb
  - Left: rendered markdown body
  - Right sidebar: FrontmatterPanel (all frontmatter fields), Save button, Rate stars, Flag button, "Saved by N users", "Last updated"
- **Chat citation link target**: `/modules/asset-library/{id}` (no full-page nav, opens in side panel or new tab depending on user preference)

#### IAM deltas

- `aicoe-module-agents-lambda-role`: no new permissions (already has s3 read + s3vectors query)
- No changes to other roles.

#### modules.json entry

```json
{
  "id": "module-2",
  "name": "Asset Library",
  "wave": 1,
  "purpose": "Browse, filter, and read curated AI delivery assets.",
  "when_to_use": [
    "Find a reference architecture for a specific industry and AI stage",
    "Locate a kickoff template or workshop agenda",
    "Pull a solution pattern relevant to a use case"
  ],
  "example_queries": [
    "Show me healthcare assets at stage 2",
    "Find a kickoff template for discovery workshops",
    "What patterns exist for fraud detection?"
  ],
  "agent_id": "AGENT-03",
  "model_tier": "haiku-4-5",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps

1. Write `agent_03_asset_library.py` as a BaseAgent subclass. 3 tools above.
2. Register AGENT-03 in `agents/lambdas/modules/router.py` (map `agent_id` to module).
3. Flip Module 2 to `enabled: true` in `vault/modules.json`.
4. Build `/modules/asset-library/page.tsx` (Server Component for initial list, Client Component for filters).
5. Server action `list_assets_action` invokes AGENT-03 via proxy Lambda or directly via lambda:Invoke (since this is a read-only flow, direct invoke is fine; orchestrator not needed in the loop).
6. Build `/modules/asset-library/[id]/page.tsx` (Server Component fetching AssetDetail via `get_asset_action`).
7. Build `web/components/MarkdownRenderer.tsx` using react-markdown + remark-gfm + rehype-highlight; sanitize HTML.
8. Build `web/components/FrontmatterPanel.tsx` rendering frontmatter as labeled rows.
9. Save / Rate / Flag: server actions that read-modify-write `users/{display_name}.json` in S3. Asset metadata aggregates (rating count, average, flag count) stored on the asset's frontmatter JSON sidecar at `vault/assets/_metadata/{asset_id}.json` (separate file so the source markdown stays clean).
10. Chat citations: confirm task 02's `Citation.asset_library_url` is populated as `/modules/asset-library/{asset_id}` for content_type=asset.
11. Smoke test:
    - Login → navigate to Asset Library → see all seed assets
    - Filter by industry=healthcare → grid reduces
    - Open an asset → markdown renders + frontmatter shows
    - Save → check user profile JSON has the asset in saved list
    - Rate 4 stars → average updates
    - Flag → flag indicator shows
    - From Chat, ask "Healthcare reference architecture for clinical notes" → citation appears, click → asset detail opens

#### Definition of done
- [ ] All FRs (010-013) verified
- [ ] All seed assets visible and openable
- [ ] Save/Rate/Flag round-trip correctly
- [ ] Chat citations link correctly
- [ ] DoD from 00_foundation.md passed

#### Behavioral guardrails
Same as task 00.

#### Out of scope
- Asset contribution flow (Module 5, Wave 6)
- AI-assisted asset search by Chat (already in task 02 via `search_knowledge_base`)
- Asset editing UI (post-demo-plan.md Section 7.3)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
- 2026-06-03: created. Read-only module; aggregates in sidecar JSON files to keep source .md clean.
- 2026-06-07: **Module-agents routing = static dispatch registry, NOT Strands** (cross-cutting; all 26 module agents inherit it). `router.py` maps `agent_id → ModuleAgent factory`; each agent dispatches an `op` key. Resolves the spec's "internal Strands routing" against `vault/decisions/agent-runtime.md`. Full rationale: `vault/decisions/module-agent-routing.md`.
- 2026-06-07: **Backend-core slice DONE** (agent + router + module Lambda + IAM + modules.json flip + tests; synth-clean, NOT deployed). UI slice (browse/detail pages, MarkdownRenderer, FrontmatterPanel, save/rate/flag server actions) deferred to next session, same scoping as task 02.
- 2026-06-07: **`module-agents-lambda-role` IAM deltas baked in** (spec said "no new permissions" — wrong; these would 403 live like AGENT-01 did): added `s3:ListBucket` on vault+sessions (404 not 403), `s3vectors:GetVectors` (citation content) alongside QueryVectors, and **Titan** in `bedrock:InvokeModel` (search embeds with Titan — chat-model-only scoping would 403 the vector search).
- 2026-06-07: AGENT-03 built **mechanical** (deterministic S3 reads for list/get; embedding-only Titan→S3 Vectors for search) — no chat-LLM loop for a read-only Haiku module. Module-2 `enabled` flipped to true; **must re-sync `vault/modules.json` to the vault bucket so the orchestrator hot-reloads it** (then `asset_library_url` activates in chat citations, FR-003).
- 2026-06-07: Module-agents Lambda packaged as a **container image** (`agents/lambdas/modules/Dockerfile`, `public.ecr.aws/lambda/python:3.12`, x86_64, handler `agents.lambdas.modules.router.handler`) because it imports `agents.lib` + pyyaml — added a lean `modules` extra (pyyaml) to pyproject. CDK: `ModuleAgentsFunction` added to `infra/stacks/agents.py`.

## D. References
- Brief: FRs 010-013, AGENT-03 in Section 6.3
- Design: Section 5.2 AGENT-03
- Foundation: `ai_docs/tasks/00_foundation.md`
