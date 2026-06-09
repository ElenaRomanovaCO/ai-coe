# Task: Wave 2 — AI Maturity Assessment (Module 1, AGENT-02 + WORKER-01/02/03)

> **Phase:** 2
> **Feature group:** Wave 2 (Assessment & Delivery)
> **Covers:** FR-016 (start from Chat or page), FR-017 (adaptive Q&A), FR-018 (stage + recommendations), FR-019 (save to vault)
> **Builds:** AGENT-02 (Sonnet 4.6), WORKER-01 question_picker, WORKER-02 scorer, WORKER-03 recommender
> **Depends on:** 00, 01, 02, 03
> **Blocks:** 21 (Client Report uses assessment data), 26 (Analytics uses assessment distributions)
> **Estimated effort:** 3-4 days solo
> **Status:** ☐ Not started
>
> **🎨 Design references — build the assessment UI to match these (they take precedence over any UI sketch in the prose below):**
> - Design system: `ui-designs/design-system.md` · Brief: `ui-designs/pages/07-maturity-assessment.md`
> - Mockup: `ui-designs/designs/AI Maturity Assessment.html`

---

## A. TL;DR Checklist

**Goal:** User can run a conversational AI maturity assessment from Chat or `/modules/assessment`. Adaptive 8-12 question flow, outputs stage 0-5 with plain-language explanation and 3-5 recommended assets. Result saved as `vault/assessments/{display_name}/{timestamp}.md`.

**Build steps:**

1. **WORKER-01 question_picker** (chooses next question based on history) → Verify: unit tests cover all 6 stages.
2. **WORKER-02 scorer** (computes stage 0-5 from answer set) → Verify: deterministic for known inputs.
3. **WORKER-03 recommender** (vector similarity from stage + industry) → Verify: stage 2 healthcare returns relevant assets.
4. **AGENT-02 in ModuleAgentsLambda** (Sonnet 4.6, orchestrates 3 workers) → Verify: end-to-end run returns valid AssessmentResult.
5. **Module 1 enabled=true in modules.json**.
6. **`/modules/assessment` page** with start button + conversational UI + result page → Verify: full demo run works.
7. **Chat handoff**: when user says "assess my client", Chat invokes AGENT-02 and streams the question flow inline in the chat dock.
8. **Result persistence**: AGENT-02 writes `vault/assessments/{display_name}/{ts}.md` with assessment frontmatter; re-embed picks it up automatically.

**Files to create/edit:**

- `agents/lambdas/workers/worker_01_question_picker.py`
- `agents/lambdas/workers/worker_02_scorer.py`
- `agents/lambdas/workers/worker_03_recommender.py`
- `agents/lambdas/workers/router.py` — register workers
- `agents/lambdas/modules/agent_02_assessment.py`
- `vault/modules.json` — flip Module 1
- `web/app/(authenticated)/modules/assessment/page.tsx`
- `web/app/(authenticated)/modules/assessment/[id]/page.tsx` — result view
- `web/app/(authenticated)/modules/assessment/actions.ts`
- `web/components/AssessmentChat.tsx` — embedded conversational UI (reused from ChatDock for consistency)

**Done when:**

- [ ] FRs 016-019 verified
- [ ] Adaptive flow asks 8-12 questions (not always exactly 10)
- [ ] Stage placement deterministic for the same inputs
- [ ] Recommendations relevant to industry + stage
- [ ] Result file appears in vault, searchable by Chat
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **AI Maturity Assessment (Module 1, AGENT-02 + WORKER-01/02/03)** for the AI CoE Platform. Tasks 00-04 are done.

#### Project context

- This is the first task introducing the Layer 3 worker pattern. Module agents call `invoke_worker` to break down complex work.
- AGENT-02 (Sonnet 4.6) runs the conversation. WORKER-01/02/03 (Haiku 4.5) do the decomposed work.
- The assessment covers 6 dimensions: data readiness, org culture, existing AI tooling, use case clarity, governance maturity, budget/sponsorship.

#### Worker specs

**WORKER-01: question_picker**

```python
class PickQuestionRequest(BaseModel):
    history: list[QAExchange]                       # prior Q&A pairs
    dimensions_covered: list[str]                   # which of 6 dimensions answered

class PickQuestionResponse(BaseModel):
    question_text: str
    dimension: str
    is_final: bool                                  # True when enough coverage to score
```

Logic: pick the next question by maximizing dimension coverage diversity, with adaptive phrasing based on prior answers. Stop when 8-12 questions reached AND all 6 dimensions touched at least once.

**WORKER-02: scorer**

```python
class ScoreRequest(BaseModel):
    history: list[QAExchange]

class ScoreResponse(BaseModel):
    stage: int                                      # 0-5
    dimension_scores: dict[str, int]                # per dimension
    rationale: str                                  # plain-language explanation
```

Deterministic scoring rubric (no LLM for the final number; LLM only writes rationale): each dimension scored 0-5 by keyword + sentiment rules. Final stage = round(mean(dimension_scores)).

**WORKER-03: recommender**

```python
class RecommendRequest(BaseModel):
    stage: int
    industry: str
    weak_dimensions: list[str]

class RecommendResponse(BaseModel):
    recommendations: list[AssetSummary]             # 3-5 items
```

Logic: filter Asset Library by industry + stage range (stage-1 to stage+1), boost by weak dimension tags, top 5.

#### Agent spec (AGENT-02)

```python
class StartAssessmentRequest(BaseModel):
    display_name: str
    session_id: str
    client_context: str | None                      # optional pre-fill

class AssessmentTurnRequest(BaseModel):
    assessment_id: str
    user_answer: str

class AssessmentTurnResponse(BaseModel):
    is_complete: bool
    next_question: str | None
    result: AssessmentResult | None

class AssessmentResult(BaseModel):
    assessment_id: str
    stage: int
    rationale: str
    dimension_scores: dict[str, int]
    recommendations: list[AssetSummary]
    vault_file_path: str                            # vault/assessments/...
```

Tools (4):
- `invoke_worker(WORKER-01, args)`
- `invoke_worker(WORKER-02, args)`
- `invoke_worker(WORKER-03, args)`
- `write_assessment_file(result)` (writes markdown to vault)

System prompt outline: friendly consultant tone, plain language, 1 question at a time, acknowledge each answer briefly before next question, summarize and stage at the end.

#### modules.json entry
```json
{
  "id": "module-1",
  "name": "AI Maturity Assessment",
  "wave": 2,
  "purpose": "Conversational assessment placing a client on AI adoption stages 0-5 with recommendations.",
  "when_to_use": ["Start a new client engagement", "Baseline a client's AI readiness", "Refresh an existing client's stage"],
  "example_queries": ["Assess my client", "Run a maturity assessment for a healthcare insurer", "What stage is my fintech client at?"],
  "agent_id": "AGENT-02",
  "model_tier": "sonnet-4-6",
  "worker_ids": ["WORKER-01", "WORKER-02", "WORKER-03"],
  "enabled": true
}
```

#### Assessment markdown frontmatter (output file)
```yaml
id: assess-{uuid}
type: assessment
display_name: {sanitized}
client_context: {free text}
industry: {if inferred}
stage: 2
dimension_scores:
  data_readiness: 2
  org_culture: 1
  ai_tooling: 3
  use_case_clarity: 2
  governance: 1
  budget_sponsorship: 3
created_at: 2026-06-03T14:23:45Z
```

#### Implementation steps

1. WORKER-01/02/03 in `agents/lambdas/workers/`. Register in worker router.
2. AGENT-02 in `agents/lambdas/modules/`. Register.
3. Flip Module 1 enabled.
4. UI:
   - `/modules/assessment` landing page: explainer + "Start Assessment" + list of past assessments for this display_name
   - On Start: open AssessmentChat (full-page chat) that streams the question/answer flow
   - On Complete: redirect to `/modules/assessment/{id}` showing stage card + rationale + recommendations + downloadable .md
5. Chat handoff: Chat orchestrator's `invoke_module` for module-1 starts the same flow inline in the chat dock instead of redirecting.
6. Smoke test:
   - From Chat: "Assess my healthcare insurance client" → 8-12 questions → stage + recommendations + saved file
   - From page: Start → complete → result page shows stage, scores, recs
   - Run the assessment twice with same inputs → same stage (WORKER-02 deterministic)
   - Search Chat for the saved assessment → it is retrievable

#### Definition of done
- [ ] FRs 016-019 verified
- [ ] Adaptive question flow within 8-12
- [ ] Deterministic scoring
- [ ] Recommendations relevant
- [ ] Result persisted + re-embedded
- [ ] DoD from 00_foundation.md passed

#### Behavioral guardrails
Same as task 00. Plus: AGENT-02 must invoke WORKER-02 for scoring, never score directly (determinism requirement).

#### Out of scope
- Client-facing report PDF (Module 14, Wave 6)
- Peer benchmarks (Module 22, Wave 5)
- Multi-client portfolio view (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
- 2026-06-03: created. First task using Layer 3 workers. Scoring is deterministic in WORKER-02; LLM only used for rationale text.
- 2026-06-09: **Backend-core DONE** (synth/test/ruff clean, NOT deployed). First Layer 3 worker pattern: new `aicoe-workers-lambda` (`agents/lambdas/workers/`) with static-dispatch router (WORKER-01/02/03), mirroring the module router. **Whole assessment loop is DETERMINISTIC, no LLM in workers** (question bank w/ adaptive-but-deterministic 8-12 length; keyword-rule scorer; filter-based recommender) — satisfies the hard determinism guardrail + fully testable. Rationale is a template in WORKER-02 (not LLM); conversational phrasing deferred to AGENT-02 (mechanical for now). Decision: `vault/decisions/worker-pattern.md`.
- 2026-06-09: AGENT-02 (Module 1, registered in module router; module-1 enabled=true) = first **stateful** module agent. In-progress state → `assessments/{slug}/{id}.json` (sessions bucket, AD-04); final result md → `vault/assessments/{slug}/{ts}.md` (re-embedded/searchable). ops: start/answer/get/list. `invoke_worker` via new `WorkerInvoker` (lambda:Invoke {worker_id,args}); `module-agents-role` already had lambda:Invoke on workers fn. Industry inferred from client_context keywords.
- 2026-06-09: **IAM: `workers-lambda-role` += `s3:ListBucket` on vault** (WORKER-03 enumerates assets; spec's "no IAM change" was wrong — same gap pattern as before). CDK: `WorkersFunction` (container, x86_64, 512MB) added to `infra/stacks/agents.py`; app.py passes `workers_role`. **Contract proven locally** (`test_agent_02.py`: WorkerInvoker→workers.router.route fake-Lambda + full start→answer→complete flow via real workers). 143 pytest pass.
- 2026-06-09: **UI slice + chat handoff DONE** (lint/build/synth/test clean, NOT deployed). Built to the design refs (`ui-designs/pages/07-maturity-assessment.md` + `design-system.md`; the mock HTML's CSS/JSX assets were missing so worked from the brief — indigo accent, slate, rounded-lg, reusable 0-5 `StageIndicator`). Route = **`/modules/maturity-assessment`** (per design brief, NOT spec's `/modules/assessment`). Pages: landing (intro + 6-dimension explainer + client-context + past-assessments rail) → `AssessmentChat` (conversational, request/response per answer, progress bar) → `[id]` result (hero stage card + dimension bars + binding-constraint callout + recommended assets + disabled "Generate client report"). actions.ts (start/answer/get/list). Dashboard "Run Assessment" quick action now live. **Chat handoff = navigate UIAction, NOT inline multi-turn** (`vault/decisions/chat-module-handoff.md`): added `ModuleEntry.ui_route`; orchestrator `invoke_module` for a ui_route module emits `UIAction(navigate)` + skips the Lambda; `ChatResponse.ui_actions` flows through SSE done; ChatDock renders an "Open …" button. module-1 ui_route set. 144 pytest pass.
- 2026-06-09: REMAINING = deploy only: UI: `/modules/assessment` (start + past list), AssessmentChat (conversational), `[id]` result page, actions.ts. Chat handoff: orchestrator invoke_module(module-1) starts the flow inline in the dock (multi-turn — needs the dock to carry assessment_id across turns). Deploy: `cdk deploy AiCoE-Iam AiCoE-Agents` (Iam changed: workers ListBucket; Agents: new workers fn + AGENT-02 in module image) → re-sync modules.json → push.

## D. References
- Brief: FRs 016-019, AGENT-02 + WORKER-01/02/03, Wave 2 in 15.2
- Design: Section 5.2 AGENT-02, Section 6 Flow 1
- Foundation: `ai_docs/tasks/00_foundation.md`
