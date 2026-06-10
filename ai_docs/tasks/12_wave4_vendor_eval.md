# Task: Wave 4 — Vendor & Model Evaluation Center (Module 13, AGENT-13)

> **Phase:** 4
> **Feature group:** Wave 4 (Specialized Tools)
> **Covers:** FR-034 (browse evaluations), FR-035 (custom side-by-side comparison)
> **Builds:** AGENT-13 (Sonnet 4.6)
> **Depends on:** 00, 01, 02
> **Blocks:** none
> **Estimated effort:** 2 days solo
> **Status:** ☑ Done — deployed + live-verified (backend + UI smoke) 2026-06-10

---

## A. TL;DR Checklist

**Goal:** Browse vendor and model evaluations by category. Build a custom side-by-side comparison from 2-4 selected entries; export as markdown.

**Build steps:**
1. AGENT-13 (Sonnet 4.6, 4 tools: list_evaluations, get_evaluation, build_comparison, flag_stale).
2. Flip Module 13 enabled.
3. Browse + detail + comparison-builder UI.

**Files to create/edit:**

- `agents/lambdas/modules/agent_13_vendor_eval.py`
- `vault/modules.json` — flip Module 13
- `web/app/(authenticated)/modules/vendor-eval/page.tsx` — browse
- `web/app/(authenticated)/modules/vendor-eval/[id]/page.tsx` — detail
- `web/app/(authenticated)/modules/vendor-eval/compare/page.tsx` — comparison builder
- `web/app/(authenticated)/modules/vendor-eval/actions.ts`

**Done when:**
- [ ] FRs 034-035 verified
- [ ] Comparison exports as markdown
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Vendor & Model Evaluation Center (Module 13)** for the AI CoE Platform. Tasks 00-11 are done.

#### Agent spec (AGENT-13)

```python
class BuildComparisonRequest(BaseModel):
    evaluation_ids: list[str]                       # 2-4
    criteria: list[str] | None = None               # subset; defaults to union of all criteria

class BuildComparisonResponse(BaseModel):
    comparison_id: str
    comparison_markdown: str                        # rendered side-by-side table
    insights: list[str]                             # AGENT-13 highlights
```

Tools: list_evaluations, get_evaluation, build_comparison, flag_stale (checks `last_verified` field).

#### modules.json entry
```json
{
  "id": "module-13",
  "name": "Vendor & Model Evaluation Center",
  "wave": 4,
  "purpose": "Structured evaluations of AI vendors, models, and platforms for engagement decisions.",
  "when_to_use": ["Picking an LLM provider", "Choosing a vector DB", "Comparing cloud AI platforms"],
  "example_queries": ["Compare Sonnet vs GPT-4 for document analysis", "Pinecone vs pgvector tradeoffs", "Which orchestration framework fits a healthcare project?"],
  "agent_id": "AGENT-13",
  "model_tier": "sonnet-4-6",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent + 4 tools.
2. Browse: filter by category, sort by last_verified (highlight stale).
3. Detail: rendered comparison from seed file + Asset Chat panel.
4. Comparison builder: select 2-4 from a picker → click Compare → AGENT-13 generates table + insights → download .md.
5. Smoke test: build comparison of GPT-4o + Sonnet + Gemini → markdown table + 3-5 insights.

#### Definition of done
- [ ] FRs 034-035 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Real-time pricing scraping (post-demo)
- Community voting (post-demo Section 7.3)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

- **2026-06-10 — Deployed + backend-smoked live; user UI smoke pending.** Commits pushed
  (`0f70f2b..bc2b106`). `cdk deploy AiCoE-Agents` (ModuleAgents +AGENT-13; AiCoE-Iam untouched)
  → synced modules.json → pushed. Live AGENT-13: `list_evaluations` llm-provider → 2 evals
  (titles from H1, stale flags); `build_comparison` (llm-doc + embeddings) → deterministic
  table + 5 real Sonnet insights + comparison_id. (Note: the first "UI smoke passed" report
  predated the push — pages weren't live yet; re-smoke against the now-deployed UI before ☑.)
- **2026-06-10 — DONE ☑.** Amplify build green; user re-smoked the live vendor-eval pages
  (browse/filter + comparison builder table/insights/download). Status + INDEX flipped ☑.
  FRs 034-035 verified live.
- **AGENT-13 follows the AGENT-05/24 precedent** (`vault/decisions/agent-05-orchestration.md`):
  the side-by-side comparison **table is assembled deterministically** from the evaluations'
  frontmatter, and Sonnet is used for **one thing only** — the 3-5 insights — with a
  deterministic fallback. `list`/`get`/`flag_stale` never call the model. No workers.
- **Comparison semantics per the spec's request model:** `build_comparison(evaluation_ids[2-4],
  criteria?)` compares 2-4 **evaluation entries** (columns), rows = the requested `criteria`
  subset or the union across selected evals (✓/— cells), plus category / vendors_compared /
  last_verified / recommendation rows. (The smoke's "GPT-4o + Sonnet + Gemini" are the
  `vendors_compared` *within* the single LLM eval; the builder compares the eval entries.)
- **Ephemeral comparisons** — no vault/sessions write, no get/list of past comparisons (matches
  the spec; the web slice downloads the `comparison_markdown` as a `.md` blob client-side).
- **Staleness:** `flag_stale` / list `stale` flag uses `last_verified` vs a 90-day window
  (evals say "re-verify quarterly"). Seeds are ~3 weeks old → none stale today; UI shows the
  badge when one is.
- **Title** derived from the body H1 (eval frontmatter has no title field). Detail/compare reuse
  `MarkdownRenderer` + `FrontmatterPanel` + Task-07 `AssetChatPanelHook`.
- **No new IAM/infra/decision** — module-agents role already has vault Get/List + Sonnet
  (region-wildcarded). Deploy just rebuilds the module image.
- **Verified local:** ruff clean, 248 pytest (+13), vault valid (58), `cdk synth` exit 0, web
  `pnpm lint` + `build` clean.
- **Remaining:** deploy (`cdk deploy AiCoE-Agents` → re-sync modules.json → push) + user live
  smoke (FR-034/035). Then flip Status/INDEX ☑.

## D. References
- Brief: FRs 034-035, AGENT-13
- Foundation: `ai_docs/tasks/00_foundation.md`
