# Task: Wave 5 — AI Use Case Ideation Engine (Module 12, AGENT-12)

> **Phase:** 5
> **Feature group:** Wave 5 (Intelligence & Insight)
> **Covers:** FR-045 (5-input form), FR-046 (ranked candidates), FR-047 (export markdown)
> **Builds:** AGENT-12 (Sonnet 4.6)
> **Depends on:** 00, 01, 02
> **Blocks:** none
> **Estimated effort:** 2 days solo
> **Status:** ☑ DONE — deployed + live-verified (2026-06-11). Backend: AiCoE-Agents
> redeployed (image-only diff, no IAM change); live `generate` smoke returned 7 ranked
> candidates, all with AGENT-03 reference assets — confirms Sonnet generation + vector
> search work on the deployed Lambda. Frontend: Amplify build #33 SUCCEED on `73e24d9`;
> ideation form + results routes serve (gated 307 → /login).

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

- 2026-06-11: Tag and scope runtime-generated vault artifacts — runtime vault exports
  (assessment/governance/ideation + future writers) carry `content_type` + `generated:
  true`; ReEmbed flags the vectors and chat search excludes them by default, since
  curated and generated content share folders. See `vault/decisions/runtime-vault-writers.md`.
- **2026-06-11: `generate_candidates` is an LLM call; everything around it is
  deterministic.** Candidate generation is inherently generative, so AGENT-12 calls
  Sonnet (returns a JSON array, parsed leniently — strips code fences, slices the
  outermost `[...]`, also accepts a `{"candidates": [...]}` wrapper — and validated per
  item against `UseCaseCandidate`). This is the same "generation is the whole job"
  carve-out documented for WORKER-11 in `vault/decisions/worker-pattern.md`. The
  remaining "tools" stay deterministic and unit-tested: **score_candidates** =
  `2·impact − effort` plus priors (+1 when the client's available data supports the
  idea, −1 for a high-effort idea at stage ≤1), sorted desc; **reference linking**
  composes AGENT-03 semantic search (best-effort, one search per candidate);
  **export_to_markdown** is templated. Unparseable model output returns a graceful
  `status: error` (no fake fallback — generation can't be faked).
- **2026-06-11: Persistence mirrors AGENT-02/05.** Full result JSON → sessions bucket
  (`ideation/{display_name}/{id}.json`, read back by `get` for the results page);
  human-readable export → vault (`ideation/{display_name}/{ts}.md`, re-embedded,
  searchable) and returned as `vault_file_path`. The UI "Export markdown" button
  downloads that same markdown client-side (blob), so no presigned URL is needed.
- **2026-06-11: No workers, no IAM change.** AGENT-12 owns its single LLM call; the
  module-agents role already grants `bedrock:InvokeModel` + `s3:PutObject` (vault &
  sessions) + `s3vectors:QueryVectors` (AGENT-03 search). `display_name` comes from the
  form (localStorage), as in kit-builder. modules.json: module-12 `enabled` +
  `ui_route: /modules/ideation`; nav enabled + routed.

**Verification (local):** `pytest agents/` 313 passed; `ruff check agents/` clean; web
`tsc --noEmit` clean, `eslint` clean, `next build` succeeds with `/modules/ideation`
and `/modules/ideation/[id]` present. Generate→rank→reference→persist→get round-trip,
markdown export, and LLM-JSON parse (incl. fenced + wrapped) covered by `test_agent_12.py`.

## D. References
- Brief: FRs 045-047, AGENT-12
- Foundation: `ai_docs/tasks/00_foundation.md`
