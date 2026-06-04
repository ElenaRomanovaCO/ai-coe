# Task: Wave 4 — Vendor & Model Evaluation Center (Module 13, AGENT-13)

> **Phase:** 4
> **Feature group:** Wave 4 (Specialized Tools)
> **Covers:** FR-034 (browse evaluations), FR-035 (custom side-by-side comparison)
> **Builds:** AGENT-13 (Sonnet 4.6)
> **Depends on:** 00, 01, 02
> **Blocks:** none
> **Estimated effort:** 2 days solo
> **Status:** ☐ Not started

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
## D. References
- Brief: FRs 034-035, AGENT-13
- Foundation: `ai_docs/tasks/00_foundation.md`
