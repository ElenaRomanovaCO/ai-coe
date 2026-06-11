# Task: Wave 5 (inserted) — Agentic Skills & Plugin Exchange (Module 28, AGENT-27)

> **Phase:** 5 (inserted / expedited — build NEXT, before Task 17)
> **Feature group:** Agentic Development Enablement
> **Covers:** FR-078 (browse/filter the exchange), FR-079 (entry detail + install steps + scoped Q&A), FR-080 (semantic search across entries)
> **Builds:** AGENT-27 (Agentic Skills & Plugin Exchange, Haiku 4.5 — deterministic catalog, no chat-LLM loop)
> **Depends on:** 00, 01, 03 (mirrors the Asset Library agent), 07 (reuses the AssetChatPanelHook)
> **Blocks:** none
> **Estimated effort:** ~1 day solo (catalog mirrors Asset Library)
> **Status:** ☑ DONE — deployed + live-verified (2026-06-11). Backend AGENT-27 deployed
> (image-only diff, no IAM change); 12 seed entries + modules.json synced to S3 (re-embedded
> as `content_type: exchange`). Live smoke: `list` (tool+category filter) and `search`
> ("security review" → security-review skill ranks #1) both pass. Amplify build #37 SUCCEED
> on `3a419d2`; `/modules/exchange` + `/[id]` serve (gated 307).

---

## A. TL;DR Checklist

**Goal:** A browsable, searchable exchange of reusable agentic-dev artifacts — Claude Code skills / slash-commands / MCP servers, Claude Cowork setups, GitHub Copilot configs, Kiro configs, and cross-tool prompt-packs — each with install steps and a "Chat with this" panel. Read-only catalog for the demo (publish/contribute deferred).

**Build steps:**

1. AGENT-27 in ModuleAgentsLambda (Haiku 4.5; deterministic — mechanical `list` / `get` / `search`, NO chat-LLM loop). Mirror AGENT-03 (`agent_03_asset_library.py`): the proven content-type-scoped catalog agent.
2. Seed `vault/exchange/{tool}/{slug}.md` content (~10–14 entries) spanning the tools and categories below, each with a per-type frontmatter schema (`agents/lib/schemas/`) wired into `scripts/validate_vault.py`.
3. Flip Module 28 `enabled=true` + `ui_route=/modules/exchange` in `modules.json`.
4. UI: `/modules/exchange` browse (tool + category facets + text filter) and `/modules/exchange/[id]` detail (markdown body + install-steps block + `FrontmatterPanel` + reused `AssetChatPanelHook`). Nav entry + dashboard Quick Action.
5. Smoke: filter `tool=claude-code, category=skill` → entries surface; open one → install steps render + "Chat with this" answers "how do I install this"; search "security review" → relevant entry ranks top.

**Files to create/edit:**

- `agents/lambdas/modules/agent_27_exchange.py`
- `agents/lambdas/modules/router.py` — register AGENT-27
- `agents/lib/schemas/exchange.py` (or `.json`) — frontmatter schema; wire into `scripts/validate_vault.py`
- `vault/exchange/**` — seed entries
- `vault/modules.json` — flip Module 28
- `web/lib/exchange.ts`, `web/app/(authenticated)/modules/exchange/page.tsx`, `.../exchange/[id]/page.tsx`, `web/app/(authenticated)/modules/exchange/actions.ts`, `web/components/exchange/ExchangeBrowser.tsx`
- `web/lib/nav.ts` — add Module 28

**Done when:**

- [ ] FRs 078–080 verified
- [ ] Browse filters by tool + category; detail renders install steps; search returns relevant entries
- [ ] Exchange entries carry `content_type: exchange` so they do NOT pollute Asset Library / scoped-asset search
- [ ] DoD from `00_foundation.md` passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Agentic Skills & Plugin Exchange (Module 28, AGENT-27)** for the AI CoE Platform. Tasks 00–16 are done; this is an inserted, expedited module to build NEXT.

#### Project context

- This is a **read-only catalog**, structurally identical to the Asset Library (Module 2 / AGENT-03). Build it by mirroring `agent_03_asset_library.py` — do NOT invent a new pattern. Haiku tier, deterministic `list` / `get` / `search`, no Bedrock Converse loop.
- It is the home for the "agentic development / skills exchange / plugins / prompts" capability: shareable artifacts for Claude Code, Claude Cowork, GitHub Copilot, and Kiro.
- Publish/contribute (user write path) is **out of scope** for this task — seed content only. (When publish lands later it becomes a runtime-vault-writer and must follow the `runtime-vault-writers` content-typing convention.)

#### Content model

`vault/exchange/{tool}/{slug}.md`, frontmatter (new `exchange` schema, validated in CI):

```yaml
id: exch-<slug>            # canonical id, e.g. exch-claude-code-security-review
content_type: exchange     # REQUIRED — keeps these out of asset/content searches
name: "Security Review Skill"
tool: claude-code          # claude-code | claude-cowork | copilot | kiro | generic
category: skill            # skill | slash-command | mcp-server | plugin | prompt-pack | config
summary: "One-line what-it-does."
tags: [security, review]
install: |                 # rendered as a copy-able install block on the detail page
  1. ...
source_url: ""            # optional
```

Seed ~10–14 entries across all five `tool` values and all six `category` values (at least one Claude Code skill, one slash-command, one MCP server, one Copilot config, one Kiro config, one cross-tool prompt-pack).

#### Agent spec (AGENT-27)

```python
class ExchangeRequest(BaseModel):
    op: Literal["list", "get", "search"]
    tool: str | None = None          # filter
    category: str | None = None      # filter
    query: str | None = None         # for search
    entry_id: str | None = None      # for get
    top_k: int = 10

class ExchangeEntry(BaseModel):
    id: str
    name: str
    tool: str
    category: str
    summary: str
    tags: list[str]
    install: str
    body_markdown: str               # get only

class ExchangeResponse(BaseModel):
    status: str
    entries: list[ExchangeEntry]     # list/search
    entry: ExchangeEntry | None      # get
```

- `list`: S3 ListObjectsV2 under `exchange/` + frontmatter parse + filter by tool/category (reuse AGENT-03's listing helpers).
- `get`: locate by `id == entry_id` (frontmatter id first, filename slug fallback — same `_reg_id`/`_asset_id` resolution pattern used elsewhere).
- `search`: Titan embed query → S3 Vectors QueryVectors filtered `content_type=exchange` → GetVectors for content; dedup by id.

#### Implementation steps

1. `agent_27_exchange.py` mirroring AGENT-03; register in `modules/router.py` REGISTRY.
2. `exchange` frontmatter schema + wire `scripts/validate_vault.py`; author seed content.
3. Flip Module 28 enabled + ui_route in `modules.json`.
4. UI: browse page (server fetch → `ExchangeBrowser` client filters: tool, category, text — same shape as `AssetBrowser`) + `[id]` detail (`MarkdownRenderer` body + install block + `FrontmatterPanel` + `<AssetChatPanelHook entryId={id} … />` reusing the Task-07 panel) + nav + dashboard Quick Action.
5. Tests (FakeS3/FakeMetrics in `modules/tests/conftest`): list filters, get-by-id resolution, search content-type scoping, `test_no_untyped_entries` (every seed entry has `content_type: exchange`).

#### Definition of done

- [ ] FRs 078–080 verified; DoD from `00_foundation.md` passed
- [ ] No IAM/infra change (module-agents role already covers vault Get/List + s3vectors Query/Get + Titan; AssetChatPanelHook → AGENT-25 already deployed)
- [ ] `content_type: exchange` on every entry → no Asset Library search pollution

#### Out of scope

- Publish/contribute (user write path) — later; ties into the `runtime-vault-writers` decision.
- Auto-install / executing skills — the exchange shows install steps only.
- AI "fit recommender" — deferred (could be a follow-up `recommend` op).

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

- **2026-06-11:** Module created by expedite request — renamed Module 27 to "Agentic Development Accelerator" (broadened from Claude-Code-only) and split the catalog/exchange capability into this new Module 28, slotted to build NEXT (insert-as-next, no renumber; Wave 5 Tasks 17–20 keep their numbers). MVP = browse+detail catalog mirroring Asset Library; deterministic, no new IAM/infra. New `content_type: exchange` chosen up front so the exchange never pollutes asset/content search.
- **2026-06-11 (build):** AGENT-27 mirrors AGENT-03 exactly — deterministic `list`/`get`/`search`, Haiku tier, no chat-LLM loop, all clients injectable. `search` filters vectors on `content_type == "exchange"`; the ReEmbed pipeline derives that same value from the `exchange/` folder, and the `exchange` folder is deliberately **not** in the orchestrator's `CONTENT_TYPE_FROM_DIR`, so exchange entries are searchable *within the module* but never surface in general chat KB search (no cross-pollution, both directions). New `ExchangeFrontmatter` schema (in `agents/lib/schemas`, `content_type: Literal["exchange"]`) auto-wires into `validate_vault.py` via the folder map; `test_no_untyped_entries` asserts every seed carries it. 12 seed entries across all 5 tools + all 6 categories. Detail page reuses the Task-07 `AssetChatPanelHook` (AGENT-25) — the install steps live in frontmatter, which the panel bakes into context, so "how do I install this" is answerable. No workers, no IAM change.

**Verification (local):** `pytest agents/` 346 passed; `ruff` clean; `validate_vault.py` OK (74 files); web `tsc`/`eslint` clean, `next build` succeeds with `/modules/exchange` + `/[id]`. list/get/search + content-type scoping + seed typing covered by `test_agent_27.py`.

## D. References

- Pattern source: `ai_docs/tasks/03_wave1_asset_library.md` (AGENT-03 catalog) + `07_wave2_universal_asset_qa.md` (AssetChatPanelHook reuse)
- Foundation: `ai_docs/tasks/00_foundation.md`
