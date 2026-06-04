# Task: Wave 3 — Governance & Risk Checker (Module 4, AGENT-05 + WORKER-04/05)

> **Phase:** 3
> **Feature group:** Wave 3 (Risk & Governance)
> **Covers:** FR-025 (4-input form), FR-026 (risk checklist with regulation links)
> **Builds:** AGENT-05 (Sonnet 4.6), WORKER-04 regulation_finder, WORKER-05 checklist_generator
> **Depends on:** 00, 01, 02; soft-depends on 10 (Compliance Tracker) for richer links
> **Blocks:** none directly; later modules (Project Health, Ethics) reference governance reviews
> **Estimated effort:** 2-3 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** User inputs engagement context (industry, data types, geography, AI use case type) and gets a structured pre-delivery risk checklist with links to relevant regulations and remediation guidance.

**Build steps:**

1. WORKER-04 regulation_finder (vector search over `vault/regs/` filtered by geo + industry + use case).
2. WORKER-05 checklist_generator (turns regulation list + context into actionable checklist items).
3. AGENT-05 in ModuleAgentsLambda (Sonnet 4.6, 3 tools: invoke_worker × 2, write_governance_review).
4. Flip Module 4 enabled.
5. `/modules/governance-checker` page: 4-input form → result page with checklist + links.
6. Save review to `vault/reviews/governance/{display_name}/{ts}.md`.

**Files to create/edit:**

- `agents/lambdas/workers/worker_04_regulation_finder.py`
- `agents/lambdas/workers/worker_05_checklist_generator.py`
- `agents/lambdas/workers/router.py` — register
- `agents/lambdas/modules/agent_05_governance.py`
- `vault/modules.json` — flip Module 4
- `web/app/(authenticated)/modules/governance/page.tsx`
- `web/app/(authenticated)/modules/governance/[id]/page.tsx`
- `web/app/(authenticated)/modules/governance/actions.ts`

**Done when:**

- [ ] FRs 025-026 verified
- [ ] Checklist references at least 2-3 regulations from seeded data
- [ ] Review saved to vault
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Governance & Risk Checker (Module 4)** for the AI CoE Platform. Tasks 00-07 are done.

#### Worker specs

**WORKER-04 regulation_finder**

```python
class FindRegulationsRequest(BaseModel):
    industry: str
    geography: str
    data_types: list[str]                           # e.g. ["pii", "phi", "financial"]
    ai_use_case_type: str

class FindRegulationsResponse(BaseModel):
    regulations: list[RegulationMatch]              # id, name, relevance_score, applicable_clauses
```

Logic: combine vector search (use case description) with structured filter (geo + industry) over `vault/regs/`.

**WORKER-05 checklist_generator**

```python
class GenerateChecklistRequest(BaseModel):
    regulations: list[RegulationMatch]
    engagement_context: dict

class GenerateChecklistResponse(BaseModel):
    checklist: list[ChecklistItem]                  # id, statement, priority, regulation_links

class ChecklistItem(BaseModel):
    statement: str                                  # actionable
    priority: Literal["critical", "high", "medium", "low"]
    regulation_links: list[str]                     # regulation IDs
    rationale: str
```

#### Agent spec (AGENT-05)

```python
class GovernanceCheckRequest(BaseModel):
    industry: str
    geography: str
    data_types: list[str]
    ai_use_case_type: str
    engagement_context: str | None = None

class GovernanceCheckResponse(BaseModel):
    review_id: str
    checklist: list[ChecklistItem]
    summary: str                                    # 3-4 sentence executive summary
    vault_file_path: str
```

Tools: invoke_worker (WORKER-04), invoke_worker (WORKER-05), write_governance_review.

#### modules.json entry
```json
{
  "id": "module-4",
  "name": "Governance & Risk Checker",
  "wave": 3,
  "purpose": "Surface compliance, governance, and risk considerations for an engagement context.",
  "when_to_use": ["Before delivery", "When a new regulation may apply", "When data types change mid-engagement"],
  "example_queries": ["Check governance for a healthcare ML model in EU", "What risks apply to a fintech credit scoring use case?", "Run a risk pass for retail customer analytics"],
  "agent_id": "AGENT-05",
  "model_tier": "sonnet-4-6",
  "worker_ids": ["WORKER-04", "WORKER-05"],
  "enabled": true
}
```

#### Implementation steps

1. Workers + agent per spec.
2. UI: 4-input form using shadcn Form. On submit → result page with checklist (priority-sorted, grouped by regulation).
3. Each checklist item links to its regulation entries (currently just the file path; once Module 25 is built, link to `/modules/compliance-tracker/{reg_id}`).
4. Save review to vault; re-embed picks it up so Chat can later cite it.
5. Smoke test: healthcare + EU + PHI + clinical decision support → checklist references EU AI Act + HIPAA seeded entries.

#### Definition of done
- [ ] FRs 025-026 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Auto-monitoring for regulation changes (Module 25 + post-demo Section 3.2)
- Sign-off workflow (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 025-026, AGENT-05, WORKER-04/05
- Design: Section 5.2 AGENT-05
- Foundation: `ai_docs/tasks/00_foundation.md`
