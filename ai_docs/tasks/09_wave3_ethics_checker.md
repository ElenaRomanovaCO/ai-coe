# Task: Wave 3 — AI Ethics & Bias Checker (Module 21, AGENT-20 + WORKER-08/09)

> **Phase:** 3
> **Feature group:** Wave 3 (Risk & Governance)
> **Covers:** FR-027 (bias/fairness/explainability review), FR-028 (save + link to engagement)
> **Builds:** AGENT-20 (Sonnet 4.6), WORKER-08 bias_analyzer, WORKER-09 regulation_mapper
> **Depends on:** 00, 01, 02
> **Blocks:** none
> **Estimated effort:** 2-3 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** User submits a use case description and receives a structured ethics review (bias risks, fairness, explainability, human-oversight, EU AI Act risk tier mapping).

**Build steps:**

1. WORKER-08 bias_analyzer (data bias + representation risks from use case + data types).
2. WORKER-09 regulation_mapper (maps to EU AI Act risk tiers, sector-specific rules).
3. AGENT-20 in ModuleAgentsLambda (Sonnet 4.6, 3 tools).
4. Flip Module 21 enabled.
5. `/modules/ethics-checker` page: form (use case, data types, affected populations, decision type) → review report.
6. Save review to `vault/reviews/ethics/{display_name}/{ts}.md`.

**Files to create/edit:**

- `agents/lambdas/workers/worker_08_bias_analyzer.py`
- `agents/lambdas/workers/worker_09_regulation_mapper.py`
- `agents/lambdas/modules/agent_20_ethics.py`
- `vault/modules.json` — flip Module 21
- `web/app/(authenticated)/modules/ethics-checker/page.tsx`
- `web/app/(authenticated)/modules/ethics-checker/[id]/page.tsx`
- `web/app/(authenticated)/modules/ethics-checker/actions.ts`

**Done when:**

- [ ] FRs 027-028 verified
- [ ] Output covers all 5 areas (bias, fairness, explainability, oversight, regulatory tier)
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **AI Ethics & Bias Checker (Module 21)** for the AI CoE Platform. Tasks 00-08 are done.

#### Worker specs

**WORKER-08 bias_analyzer**: takes use case + data types + affected populations; emits risks across data representation, sample bias, label bias, automation bias.

**WORKER-09 regulation_mapper**: takes use case + decision type + geography; maps to EU AI Act risk tier (minimal / limited / high / unacceptable), HIPAA implications for healthcare, FFIEC for financial.

#### Agent spec (AGENT-20)

```python
class EthicsReviewRequest(BaseModel):
    use_case: str
    data_types: list[str]
    affected_populations: list[str]
    decision_type: Literal["automated", "assisted", "recommendation-only"]
    geography: str
    industry: str

class EthicsReviewResponse(BaseModel):
    review_id: str
    bias_risks: list[Risk]
    fairness_considerations: list[str]
    explainability_requirements: list[str]
    human_oversight_recommendations: list[str]
    regulatory_tier: dict                           # framework -> tier
    summary: str
    vault_file_path: str
```

#### modules.json entry
```json
{
  "id": "module-21",
  "name": "AI Ethics & Bias Checker",
  "wave": 3,
  "purpose": "Pre-deployment ethical and bias review for AI use cases.",
  "when_to_use": ["Before deploying a use case in a regulated industry", "When using AI for decisions affecting individuals", "When facing client questions about responsible AI"],
  "example_queries": ["Run an ethics review for an automated underwriting model", "What bias risks apply to a hiring screener?", "Map this medical imaging classifier to EU AI Act tiers"],
  "agent_id": "AGENT-20",
  "model_tier": "sonnet-4-6",
  "worker_ids": ["WORKER-08", "WORKER-09"],
  "enabled": true
}
```

#### Implementation steps

1. Workers + agent per spec.
2. UI: form + result page with grouped findings.
3. Each risk item with mitigation suggestion.
4. Save to vault.
5. Smoke test: automated lending decision + US + minority populations → high-risk classification + bias risks + EU AI Act unacceptable (since lending may be high-risk depending on parameters) → review file in vault.

#### Definition of done
- [ ] FRs 027-028 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Continuous monitoring of deployed models (post-demo)
- Approval workflow with leadership (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 027-028, AGENT-20, WORKER-08/09
- Design: Section 5.2 AGENT-20
- Foundation: `ai_docs/tasks/00_foundation.md`
