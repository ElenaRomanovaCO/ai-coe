# Task: Wave 4 — Skills & Tools Repository (Module 7, AGENT-08)

> **Phase:** 4
> **Feature group:** Wave 4 (Specialized Tools)
> **Covers:** FR-032 (browse filtered), FR-033 (tool detail)
> **Builds:** AGENT-08 (Skills & Tools, Haiku 4.5)
> **Depends on:** 00, 01 (seeded tools), 02
> **Blocks:** none
> **Estimated effort:** 1-2 days solo
> **Status:** ☑ Done — deployed + live-verified (backend + UI smoke) 2026-06-10

---

## A. TL;DR Checklist

**Goal:** Browse tools by category, stack, AI stage, cost model; open detail with description, best-fit, ratings, limitations.

**Build steps:**

1. AGENT-08 (Haiku 4.5, 3 tools: list_tools, get_tool, recommend_tools_for_context).
2. Flip Module 7 enabled.
3. `/modules/tools-repo` browse + `/modules/tools-repo/[id]` detail with embedded AssetChatPanel.

**Files to create/edit:**

- `agents/lambdas/modules/agent_08_tools.py`
- `vault/modules.json` — flip Module 7
- `web/app/(authenticated)/modules/tools-repo/page.tsx`
- `web/app/(authenticated)/modules/tools-repo/[id]/page.tsx`
- `web/app/(authenticated)/modules/tools-repo/actions.ts`

**Done when:**
- [ ] FRs 032-033 verified
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Skills & Tools Repository (Module 7)**. Tasks 00-10 done. Seeded tools at `vault/tools/`.

#### Agent spec (AGENT-08)

Tools: list_tools (filters: category, stack, stage, cost), get_tool, recommend_tools_for_context (vector + filter).

#### modules.json entry
```json
{
  "id": "module-7",
  "name": "Skills & Tools Repository",
  "wave": 4,
  "purpose": "Curated directory of AI tools, frameworks, libraries with context.",
  "when_to_use": ["Picking a vector DB", "Choosing an agent framework", "Finding a tool for a specific stage"],
  "example_queries": ["Recommend a vector DB for low-volume RAG", "What orchestration framework should I use?", "Tools for healthcare AI projects"],
  "agent_id": "AGENT-08",
  "model_tier": "haiku-4-5",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent with 3 tools.
2. Reuse AssetCard pattern from Asset Library, adapt frontmatter fields.
3. Detail page reuses MarkdownRenderer + FrontmatterPanel + AssetChatPanel.
4. Smoke test: filter category=vector-db → returns Pinecone + S3 Vectors + pgvector; open S3 Vectors detail → chat panel works.

#### Definition of done
- [ ] FRs 032-033 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Tool ratings aggregation (uses Asset Library's metadata sidecar pattern)
- Tool comparison UI (Module 13 Vendor Eval covers this)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

- **2026-06-10 — Deployed + backend-smoked live; user UI smoke pending.** Commits pushed.
  `cdk deploy AiCoE-Agents` (ModuleAgents updated; AiCoE-Iam untouched) → synced modules.json
  → pushed. Live AGENT-08: `list_tools` vector-db → S3 Vectors + Pinecone; `get_tool` → body;
  `recommend_tools_for_context` "small RAG pilot" → vector-dbs first. Remaining: user UI smoke
  (filter category=vector-db; tool detail "Chat with this"), then flip Status/INDEX ☑.
- **2026-06-10 — DONE ☑.** User UI smoke passed (browse filter + tool detail Chat-with-this).
  Status + INDEX flipped ☑. FRs 032-033 verified live.
- **AGENT-08 is a read-only near-clone of AGENT-03** (Haiku, mechanical, no LLM loop, no
  workers) over `vault/tools/`: `list_tools` (category/stack/stage/cost/tags/query filters),
  `get_tool` (resolve by frontmatter id w/ basename fallback), `recommend_tools_for_context`
  (Titan embed → S3 Vectors `content_type=tools` + optional category/stage/cost post-filters).
  Reuses `agent_03_asset_library._split_frontmatter`.
- **No write ops** (save/rate/flag) — task defers tool ratings to the Asset Library sidecar
  pattern (out of scope). Detail page reuses `MarkdownRenderer` + `FrontmatterPanel` +
  Task-07 `AssetChatPanelHook` (content-agnostic) for scoped Q&A.
- **No new IAM/infra/decision** — module-agents role already has vault Get/List + Titan +
  s3vectors Query/Get; AGENT-08 only embeds (no chat model). Deploy just rebuilds the image.
- **Seed reality:** 6 tools — vector-db ×2 (Pinecone, S3 Vectors; no pgvector), framework ×2
  (LangChain, LlamaIndex), llm-provider ×1 (Bedrock), orchestration ×1 (Strands). The task's
  "category=vector-db → Pinecone + S3 Vectors + pgvector" smoke resolves to the 2 seeded ones.
- **Verified local:** ruff clean, 235 pytest (+11), vault valid (58), `cdk synth` exit 0,
  web `pnpm lint` + `build` clean.
- **Remaining:** deploy (`cdk deploy AiCoE-Agents` → re-sync modules.json → push) + user live
  smoke (FR-032/033). Then flip Status/INDEX ☑.

## D. References
- Brief: FRs 032-033, AGENT-08
- Foundation: `ai_docs/tasks/00_foundation.md`
