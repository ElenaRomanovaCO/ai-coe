# Task: Wave 3 — Global AI Regulation & Compliance Tracker (Module 25, AGENT-24 + WORKER-12/13)

> **Phase:** 3
> **Feature group:** Wave 3 (Risk & Governance)
> **Covers:** FR-029 (browse filtered), FR-030 (per-reg detail), FR-031 (apply to use case)
> **Builds:** AGENT-24 (Sonnet 4.6), WORKER-12 reg_summarizer, WORKER-13 applicability_checker
> **Depends on:** 00, 01 (seeded regulations critical), 02, 07 (Universal Asset Q&A pattern reused)
> **Blocks:** Module 4 enrichment (Module 4 will link here once both exist)
> **Estimated effort:** 2-3 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** User can browse regulations (filter by geography, industry, status, AI use case type), open any one to read summary + checklist, or ask Chat to apply a regulation to a specific use case.

**Build steps:**

1. WORKER-12 reg_summarizer (regulation → plain language summary).
2. WORKER-13 applicability_checker (regulation + use case → applicability checklist).
3. AGENT-24 in ModuleAgentsLambda (Sonnet 4.6).
4. Flip Module 25 enabled.
5. `/modules/compliance-tracker` browse + detail pages. Embed Universal Asset Q&A panel on each regulation detail.
6. Cross-link from Governance Checker (Module 4): regulation links in checklists now route here.

**Files to create/edit:**

- `agents/lambdas/workers/worker_12_reg_summarizer.py`
- `agents/lambdas/workers/worker_13_applicability_checker.py`
- `agents/lambdas/modules/agent_24_compliance.py`
- `vault/modules.json` — flip Module 25
- `web/app/(authenticated)/modules/compliance-tracker/page.tsx`
- `web/app/(authenticated)/modules/compliance-tracker/[id]/page.tsx` — embed AssetChatPanel
- `web/app/(authenticated)/modules/compliance-tracker/actions.ts`

**Done when:**

- [ ] FRs 029-031 verified
- [ ] Browse filters work across seeded regulations
- [ ] Detail page renders + Q&A panel works
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Global AI Regulation & Compliance Tracker (Module 25)** for the AI CoE Platform. Tasks 00-09 are done. Seeded regulations exist under `vault/regs/`.

#### Worker specs
- **WORKER-12 reg_summarizer**: regulation full text → plain language summary + key requirements + sector implications
- **WORKER-13 applicability_checker**: regulation + use case description → list of applicability items (which clauses apply, which do not)

#### Agent spec (AGENT-24)

```python
class ListRegulationsRequest(BaseModel):
    geography: str | None
    industry: str | None
    status: str | None
    use_case_type: str | None
    query: str | None

class RegulationDetailRequest(BaseModel):
    reg_id: str

class ApplyRegulationRequest(BaseModel):
    reg_id: str
    use_case_description: str
    industry: str
    geography: str
```

Tools: list_regulations, get_regulation, invoke_worker (WORKER-12), invoke_worker (WORKER-13).

#### modules.json entry
```json
{
  "id": "module-25",
  "name": "Compliance Tracker",
  "wave": 3,
  "purpose": "Browse, search, and apply AI regulations across geographies and industries.",
  "when_to_use": ["Before delivery in a regulated industry", "When a new regulation may apply", "When a client asks about specific compliance"],
  "example_queries": ["What does the EU AI Act say about high-risk use cases?", "Find regulations for healthcare AI in the US", "Apply HIPAA to this clinical decision tool"],
  "agent_id": "AGENT-24",
  "model_tier": "sonnet-4-6",
  "worker_ids": ["WORKER-12", "WORKER-13"],
  "enabled": true
}
```

#### Implementation steps

1. Workers + agent per spec.
2. Browse page: filter sidebar, list view with status badges and effective dates.
3. Detail page: full markdown render + frontmatter sidebar + AssetChatPanel for scoped Q&A.
4. Apply-to-use-case modal: opens from regulation detail; takes use case description; calls AGENT-24 → returns applicability checklist.
5. Smoke test: filter EU + healthcare → EU AI Act + HIPAA equivalents appear; open EU AI Act → ask "summarize for executive" → useful answer; apply EU AI Act to "clinical imaging classifier" → applicability checklist.

#### Definition of done
- [ ] FRs 029-031 verified
- [ ] AssetChatPanel embedded on every regulation
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Live regulatory monitoring (post-demo Section 3.2)
- Email alerts on regulation changes (post-demo Section 3.2)
- Subscriber lists per regulation (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 029-031, AGENT-24, WORKER-12/13
- Design: Section 5.2 AGENT-24
- Foundation: `ai_docs/tasks/00_foundation.md`
- Reuses pattern from: `07_wave2_universal_asset_qa.md`
