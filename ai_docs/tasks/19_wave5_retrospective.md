# Task: Wave 5 — Engagement Retrospective Tracker (Module 16, AGENT-15)

> **Phase:** 5
> **Feature group:** Wave 5 (Intelligence & Insight)
> **Covers:** FR-054 (structured retro form), FR-055 (insight extraction)
> **Builds:** AGENT-15 (Sonnet 4.6)
> **Depends on:** 00, 01, 02, 18 (engagements)
> **Blocks:** none
> **Estimated effort:** 1-2 days solo
> **Status:** ☐ Not started

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
## D. References
- Brief: FRs 054-055, AGENT-15
- Foundation: `ai_docs/tasks/00_foundation.md`
