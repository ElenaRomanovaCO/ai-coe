# Task: Wave 7 — Claude Code Development Accelerator (Module 27, AGENT-26 + WORKER-14/15/16)

> **Phase:** 7
> **Feature group:** Wave 7 (Development Accelerator)
> **Covers:** FR-074 (generate from reference architecture), FR-075 (target inputs), FR-076 (scaffolded codebase), FR-077 (code review)
> **Builds:** AGENT-26 (Opus 4.7), WORKER-14 scaffolder, WORKER-15 iac_generator, WORKER-16 code_reviewer
> **Depends on:** 00 (Opus cap pattern is critical here), 01 (reference architectures), 02
> **Blocks:** none
> **Estimated effort:** 3-4 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** From any reference architecture in the Asset Library, generate scaffolded code (folder structure, IaC, API stubs, README, CI/CD) targeted at a chosen cloud + language + deployment context. Plus: review pasted existing code against CoE best practices.

**Critical:** This module uses Opus 4.7 which is the most expensive. Daily Opus cap (set in task 00) is enforced on every invocation. Without cap, a single demo run can hit $1+.

**Build steps:**
1. WORKER-14 scaffolder (folder structure + boilerplate).
2. WORKER-15 iac_generator (CDK / Terraform from arch).
3. WORKER-16 code_reviewer (review existing code against CoE patterns).
4. AGENT-26 (Opus 4.7, 4 tools).
5. Flip Module 27 enabled.
6. `/modules/code-accelerator/generate/[asset_id]` + `/modules/code-accelerator/review`.
7. UI shows current daily Opus cost vs cap; disables Generate when cap hit.

**Files to create/edit:**

- `agents/lambdas/workers/worker_14_scaffolder.py`
- `agents/lambdas/workers/worker_15_iac_generator.py`
- `agents/lambdas/workers/worker_16_code_reviewer.py`
- `agents/lambdas/modules/agent_26_code.py`
- `vault/modules.json` — flip Module 27
- `web/app/(authenticated)/modules/code-accelerator/page.tsx`
- `web/app/(authenticated)/modules/code-accelerator/generate/[asset_id]/page.tsx`
- `web/app/(authenticated)/modules/code-accelerator/review/page.tsx`
- `web/app/(authenticated)/modules/code-accelerator/actions.ts`
- `web/components/code/CostMeter.tsx` — shows daily Opus cost vs cap

**Done when:**
- [ ] FRs 074-077 verified
- [ ] Opus cap blocks invocation when hit
- [ ] Generated zip extracts to a runnable scaffold
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Claude Code Development Accelerator (Module 27)** for the AI CoE Platform. Tasks 00-26 are done. This module uses Opus 4.7 and is subject to the daily Opus cost cap implemented in task 00 (`agents/lib/cost_cap.py`).

#### Worker specs

- **WORKER-14 scaffolder**: takes reference architecture + targets → folder structure + boilerplate files (README, base config, sample components)
- **WORKER-15 iac_generator**: takes architecture + cloud target → CDK Python or Terraform code
- **WORKER-16 code_reviewer**: takes pasted code → review against CoE patterns (security, structure, anti-patterns), returns annotated findings

All three workers use Opus 4.7. Each invocation checks the daily cap first.

#### Agent spec (AGENT-26)

```python
class GenerateRequest(BaseModel):
    reference_asset_id: str
    cloud_target: Literal["aws", "gcp", "azure"]
    language: Literal["python", "typescript", "go"]
    framework_pref: str | None                       # e.g. fastapi, langchain
    deployment_context: Literal["lambda", "fargate", "ec2", "kubernetes"]

class GenerateResponse(BaseModel):
    generation_id: str
    download_url: str                                # presigned, 1h
    file_manifest: list[FileEntry]
    estimated_cost_usd: float
    daily_opus_remaining_usd: float

class ReviewRequest(BaseModel):
    code_text: str
    language: str
    context: str | None

class ReviewResponse(BaseModel):
    findings: list[ReviewFinding]                   # severity, file/line, suggestion
    overall_score: int                              # 0-100
    references: list[str]                           # asset IDs
```

Tools: invoke_worker (WORKER-14), invoke_worker (WORKER-15), invoke_worker (WORKER-16), zip_generation.

#### modules.json entry
```json
{
  "id": "module-27",
  "name": "Claude Code Development Accelerator",
  "wave": 7,
  "purpose": "Generate scaffolded code, IaC, and reviews from reference architectures using Opus 4.7.",
  "when_to_use": ["Bootstrapping a new project from a known pattern", "Generating IaC from an architecture diagram", "Reviewing code against CoE best practices"],
  "example_queries": ["Generate starter code from this reference architecture", "Review this Lambda code", "Create CDK from this diagram"],
  "agent_id": "AGENT-26",
  "model_tier": "opus-4-7",
  "worker_ids": ["WORKER-14", "WORKER-15", "WORKER-16"],
  "enabled": true
}
```

#### Implementation steps

1. Workers + agent per spec. Each Opus call is wrapped in `cost_cap.check_and_reserve` before invocation; settled with `cost_cap.commit(actual_cost)` after.
2. Generate page: shows reference architecture summary, target form (cloud / language / framework / deployment), estimated cost preview, CostMeter (daily cap usage). Submit triggers AGENT-26 → workers → manifest + download URL.
3. Review page: large code paste area + context input + Review button. Same cap logic. Output is annotated findings grouped by severity.
4. CostMeter component: reads cost_cap state from S3; refreshes every 60s. Disables Generate button at 80% of cap with a warning; blocks at 100%.
5. Smoke test:
   - Pick a reference architecture for healthcare RAG → generate with aws + python + fastapi + lambda → zip with 10-15 files extracts cleanly
   - Open the generated README → confirms reference architecture
   - Paste sample code with anti-patterns → review surfaces them
   - Lower daily cap to $0.10 → second generation blocked with clear message

#### Definition of done
- [ ] FRs 074-077 verified
- [ ] Opus cap enforced (manually verified by lowering cap)
- [ ] DoD from 00_foundation.md passed

#### Behavioral guardrails
Same as task 00. Plus: every Opus invocation MUST go through cost_cap; never bypass.

#### Out of scope
- IDE plugin (post-demo)
- Live code execution / sandboxing (post-demo)
- Architecture diagram OCR (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
- 2026-06-03: Opus cap pattern from task 00 is load-bearing for this module.

## D. References
- Brief: FRs 074-077, AGENT-26, WORKER-14/15/16, NFR-006, RISK-05
- Design: Section 5.2 AGENT-26
- Foundation: `ai_docs/tasks/00_foundation.md` (cost_cap, observability)
