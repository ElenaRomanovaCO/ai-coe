# Task: Wave 5 — Engagement Retrospective Tracker (Module 16, AGENT-15)

> **Phase:** 5
> **Feature group:** Wave 5 (Intelligence & Insight)
> **Covers:** FR-054 (structured retro form), FR-055 (insight extraction)
> **Builds:** AGENT-15 (Sonnet 4.6)
> **Depends on:** 00, 01, 02, 18 (engagements)
> **Blocks:** none
> **Estimated effort:** 1-2 days solo
> **Status:** ☑ Built + verified locally (2026-06-11); commit/deploy pending review

---

## A. TL;DR Checklist

**Goal:** At engagement close, consultant fills a retro (use cases attempted, patterns used, what worked, what failed, stage reassessment). AGENT-15 extracts reusable insights and saves them as Knowledge Base entries linked to the retro.

**Build steps:**
1. AGENT-15 (Sonnet 4.6, 3 tools: write_retro, extract_insights, link_back_to_assets).
2. Flip Module 16 enabled.
3. `/modules/retros/new/[engagement-id]` form + `/modules/retros/[id]` detail with extracted insights.

**Files to create/edit:**

- `agents/lambdas/modules/agent_15_retro.py`
- `vault/modules.json` — flip Module 16
- `web/app/(authenticated)/modules/retros/page.tsx`
- `web/app/(authenticated)/modules/retros/new/[engagement_id]/page.tsx`
- `web/app/(authenticated)/modules/retros/[id]/page.tsx`
- `web/app/(authenticated)/modules/retros/actions.ts`

**Done when:**
- [ ] FRs 054-055 verified
- [ ] Extracted insights appear as vault entries
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Engagement Retrospective Tracker (Module 16)** for the AI CoE Platform. Tasks 00-18 are done.

#### Agent spec (AGENT-15)

```python
class WriteRetroRequest(BaseModel):
    engagement_id: str
    use_cases_attempted: list[str]
    patterns_used: list[str]                        # asset IDs
    what_worked: str                                # free text
    what_failed: str                                # free text
    tools_recommended: list[str]
    tools_not_recommended: list[str]
    stage_reassessment: int

class ExtractInsightsResponse(BaseModel):
    insights: list[Insight]                         # each with type, statement, evidence, asset_link
```

Tools: write_retro, invoke_worker (none defined; uses Sonnet directly for extraction), link_back_to_assets.

#### Storage
- `vault/retros/{display_name}/{retro_id}.md`
- Extracted insights: `vault/retros/insights/{insight_id}.md` (each linked back to its retro)

#### modules.json entry
```json
{
  "id": "module-16",
  "name": "Engagement Retrospective Tracker",
  "wave": 5,
  "purpose": "Capture engagement learnings and extract reusable insights for the knowledge base.",
  "when_to_use": ["At engagement close", "After a major milestone", "Capturing tool effectiveness"],
  "example_queries": ["Start a retro for my engagement", "What insights did we extract last quarter?"],
  "agent_id": "AGENT-15",
  "model_tier": "sonnet-4-6",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent + 3 tools.
2. UI: structured form (predefined sections + free text fields).
3. On submit: AGENT-15 saves retro and extracts insights → links them back as a section in the retro detail page.
4. Smoke test: file a retro on a sample engagement → 2-4 insights extracted and appear in vault, retrievable by Chat.

#### Definition of done
- [ ] FRs 054-055 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Multi-stakeholder retro sessions (post-demo)
- Retro template variations per engagement type (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

- **2026-06-11: Two-tier storage by audience — the key design call.** The **retro**
  (`retros/{display_name}/{retro_id}.md`) is engagement-specific, so it's tagged
  `generated: true` via `export_frontmatter` and scoped out of curated chat KB search
  (runtime-vault-writers convention). The **insights** (`insights/{insight_id}.md`) are
  the whole point — reusable, generic knowledge — so they're written WITHOUT the
  generated flag, and the orchestrator's `CONTENT_TYPE_FROM_DIR` now maps the
  `insights/` folder → new `insight` content type, making them **retrievable by chat**
  `search_knowledge_base` (FR-055). The folder + flag cleanly separate the two even
  though both are runtime-written. (Web `Citation.content_type` is loosely typed
  `string`, so adding the `insight` literal is a no-ripple orchestrator-only change.)
- **2026-06-11: `extract_insights` is the one LLM call.** Sonnet returns 2-4 generic
  insights (type/statement/evidence/asset_id), parsed leniently; `link_back_to_assets`
  only links an `asset_id` that's actually in the retro's `patterns_used` (drops
  hallucinated links). Deterministic fallback derives insights from
  what_worked/what_failed/tools when Bedrock errors. Structured state in sessions JSON
  (read back by get/list), mirroring AGENT-02. No workers, no IAM change.
- **2026-06-11: Entry point** — retros are filed from an engagement: the Project Health
  `[id]` page gained a "File retrospective →" link to `/modules/retros/new/{engagement_id}`.

**Verification (local):** `pytest agents/` 367 passed; `ruff` clean; `validate_vault.py`
OK (74 files); web `tsc`/`eslint` clean, `next build` succeeds with `/modules/retros`,
`/new/[engagement_id]`, `/[id]`. write_retro (retro generated-flagged + insights
searchable/not-generated + asset-link validation), extraction fallback, get/list, and
the orchestrator insights mapping covered by `test_agent_15.py`.

## D. References
- Brief: FRs 054-055, AGENT-15
- Foundation: `ai_docs/tasks/00_foundation.md`
