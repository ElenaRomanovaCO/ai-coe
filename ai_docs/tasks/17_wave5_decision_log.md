# Task: Wave 5 — Decision Log (Module 19, AGENT-18)

> **Phase:** 5
> **Feature group:** Wave 5 (Intelligence & Insight)
> **Covers:** FR-048 (log decision), FR-049 (search across decisions), FR-050 (related-decisions via vector similarity)
> **Builds:** AGENT-18 (Haiku 4.5)
> **Depends on:** 00, 01, 02
> **Blocks:** none
> **Estimated effort:** 1-2 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** User logs decisions (decision, context, alternatives, rationale, outcome). Searchable across engagements; opening one shows similar past decisions via vector similarity.

**Build steps:**
1. AGENT-18 (Haiku 4.5, 3 tools: write_decision, search_decisions, get_similar).
2. Flip Module 19 enabled.
3. `/modules/decisions` browse + `/modules/decisions/new` form + `/modules/decisions/[id]` detail with Similar Decisions panel.

**Files to create/edit:**

- `agents/lambdas/modules/agent_18_decisions.py`
- `vault/modules.json` — flip Module 19
- `web/app/(authenticated)/modules/decisions/page.tsx`
- `web/app/(authenticated)/modules/decisions/new/page.tsx`
- `web/app/(authenticated)/modules/decisions/[id]/page.tsx`
- `web/app/(authenticated)/modules/decisions/actions.ts`

**Done when:**
- [ ] FRs 048-050 verified
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Decision Log (Module 19)** for the AI CoE Platform. Tasks 00-16 are done.

#### Agent spec (AGENT-18)

```python
class WriteDecisionRequest(BaseModel):
    display_name: str
    decision: str
    context: str
    alternatives: list[str]
    rationale: str
    outcome: str | None = None                      # filled later
    tags: list[str]
    engagement_id: str | None = None

class SearchDecisionsRequest(BaseModel):
    query: str
    tags: list[str] | None
    industry: str | None

class GetSimilarRequest(BaseModel):
    decision_id: str
    top_k: int = 5
```

Tools: write_decision (suggests tags via Haiku call), search_decisions, get_similar (vector similarity in S3 Vectors filtered by content_type=decision).

#### Decision storage
- `vault/decisions/{display_name}/{decision_id}.md` with frontmatter (decision_id, decision, context, alternatives, rationale, outcome, tags, engagement_id, created_at, updated_at)

#### modules.json entry
```json
{
  "id": "module-19",
  "name": "Decision Log",
  "wave": 5,
  "purpose": "Capture and search engagement decisions for continuity and onboarding.",
  "when_to_use": ["Log an architectural choice", "Find precedent for a similar decision", "Onboard a new consultant to past reasoning"],
  "example_queries": ["What decisions did we make about vector DBs in healthcare projects?", "Log this LLM provider choice", "Find similar decisions to this one"],
  "agent_id": "AGENT-18",
  "model_tier": "haiku-4-5",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent + 3 tools.
2. UI: list view (filter tags, industry), new-decision form with tag suggestions auto-filled by AGENT-18, detail view with rendered fields + Similar Decisions panel.
3. Smoke test: log 3 decisions in healthcare RAG space, open one, similar panel shows the other two.

#### Definition of done
- [ ] FRs 048-050 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Decision approval / sign-off workflow (post-demo)
- Decision graph visualization (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 048-050, AGENT-18
- Foundation: `ai_docs/tasks/00_foundation.md`
