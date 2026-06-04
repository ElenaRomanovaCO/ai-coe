# Task: Wave 5 — AI Use Case Ideation Engine (Module 12, AGENT-12)

> **Phase:** 5
> **Feature group:** Wave 5 (Intelligence & Insight)
> **Covers:** FR-045 (5-input form), FR-046 (ranked candidates), FR-047 (export markdown)
> **Builds:** AGENT-12 (Sonnet 4.6)
> **Depends on:** 00, 01, 02
> **Blocks:** none
> **Estimated effort:** 2 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** User inputs industry, pain points, goals, available data, AI maturity stage → ranked list of use case candidates with effort/impact/prerequisites/examples.

**Build steps:**
1. AGENT-12 (Sonnet 4.6, 3 tools: generate_candidates, score_candidates, export_to_markdown).
2. Flip Module 12 enabled.
3. `/modules/ideation` form + ranked-results page + export button.

**Files to create/edit:**

- `agents/lambdas/modules/agent_12_ideation.py`
- `vault/modules.json` — flip Module 12
- `web/app/(authenticated)/modules/ideation/page.tsx`
- `web/app/(authenticated)/modules/ideation/[id]/page.tsx`
- `web/app/(authenticated)/modules/ideation/actions.ts`

**Done when:**
- [ ] FRs 045-047 verified
- [ ] Each candidate has effort + impact + prerequisites + reference example
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **AI Use Case Ideation Engine (Module 12)** for the AI CoE Platform. Tasks 00-15 are done.

#### Agent spec (AGENT-12)

```python
class IdeationRequest(BaseModel):
    industry: str
    pain_points: list[str]
    goals: list[str]
    available_data: list[str]
    ai_stage: int

class UseCaseCandidate(BaseModel):
    id: str
    title: str
    description: str
    effort: Literal["low", "medium", "high"]
    impact: Literal["low", "medium", "high"]
    prerequisites: list[str]
    reference_example_asset_id: str | None
    rationale: str

class IdeationResult(BaseModel):
    ideation_id: str
    candidates: list[UseCaseCandidate]              # ranked
    vault_file_path: str
```

Tools: generate_candidates, score_candidates (effort/impact scoring with historical priors), export_to_markdown.

#### modules.json entry
```json
{
  "id": "module-12",
  "name": "AI Use Case Ideation Engine",
  "wave": 5,
  "purpose": "Generate ranked AI use case candidates from client context.",
  "when_to_use": ["Client says we want to do AI but doesn't know where", "Discovery workshop preparation", "Refresh of an existing portfolio"],
  "example_queries": ["Ideate use cases for a fintech at stage 2", "What AI projects could a retailer with customer data start?", "Healthcare use cases at stage 1"],
  "agent_id": "AGENT-12",
  "model_tier": "sonnet-4-6",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent + 3 tools.
2. UI: 5-input form → ranked grid of candidates with effort/impact 2D matrix visual.
3. Each candidate: expandable card with full description, prerequisites, reference example link to Asset Library.
4. Export → vault/ideation/{display_name}/{ts}.md.
5. Smoke test: ideate for retail + stage 2 + customer transactions + reduce churn → 5+ candidates with effort/impact scores + reference assets linked.

#### Definition of done
- [ ] FRs 045-047 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Workshop-mode multi-stakeholder voting (post-demo)
- Integration with client OKR tools (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 045-047, AGENT-12
- Foundation: `ai_docs/tasks/00_foundation.md`
