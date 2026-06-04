# Task: Wave 6 — Certification & Badging (Module 20, AGENT-19)

> **Phase:** 6
> **Feature group:** Wave 6 (Client-Facing & People)
> **Covers:** FR-069 (browse certs), FR-070 (complete + earn badge), FR-071 (team capability map)
> **Builds:** AGENT-19 (Haiku 4.5)
> **Depends on:** 00, 01, 02, 04, 22 (Community Hub learning paths)
> **Blocks:** none
> **Estimated effort:** 2 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** Browse certifications by role and AI domain. Complete required learning + assessments + practical exercises. Earn badge displayed on Personal Dashboard. Leadership sees team capability map.

**Build steps:**
1. AGENT-19 (Haiku 4.5, 4 tools: list_certs, get_cert, evaluate_submission, capability_map).
2. Flip Module 20 enabled.
3. `/modules/certifications` browse + `/modules/certifications/[id]` detail + `/modules/certifications/[id]/exercise` practical exercise + `/modules/certifications/team` capability map.
4. Seed 6 certifications: AI Foundations, AI Solution Architecture, AI Delivery & Implementation, AI Governance & Risk, Industry AI (Healthcare), Prompt Engineering Practitioner.

**Files to create/edit:**

- `agents/lambdas/modules/agent_19_certification.py`
- `vault/modules.json` — flip Module 20
- `vault/certifications/*.md` — 6 seed cert definitions
- `web/app/(authenticated)/modules/certifications/page.tsx`
- `web/app/(authenticated)/modules/certifications/[id]/page.tsx`
- `web/app/(authenticated)/modules/certifications/[id]/exercise/page.tsx`
- `web/app/(authenticated)/modules/certifications/team/page.tsx`
- `web/app/(authenticated)/modules/certifications/actions.ts`
- `web/components/dashboard/LearningProgressCard.tsx` — wire live data

**Done when:**
- [ ] FRs 069-071 verified
- [ ] Earning a badge shows on dashboard
- [ ] Capability map renders for seeded users
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Certification & Badging (Module 20)** for the AI CoE Platform. Tasks 00-24 are done.

#### Agent spec (AGENT-19)

```python
class CertificationDefinition(BaseModel):
    id: str
    name: str
    role_targets: list[str]
    domain: str
    required_learning_paths: list[str]
    required_assessments: list[str]
    practical_exercises: list[str]                  # exercise IDs

class EvaluateSubmissionRequest(BaseModel):
    user: str
    cert_id: str
    exercise_id: str
    submission: dict                                # exercise-specific

class EvaluateSubmissionResponse(BaseModel):
    score: int                                      # 0-100
    pass_threshold: int
    passed: bool
    feedback: list[str]
```

Tools: list_certs, get_cert, evaluate_submission, capability_map.

#### modules.json entry
```json
{
  "id": "module-20",
  "name": "Certification & Badging",
  "wave": 6,
  "purpose": "Internal AI competency certifications tied to learning paths.",
  "when_to_use": ["Demonstrate AI skill in a domain", "Build team capability", "Track learning progress"],
  "example_queries": ["What certifications are available?", "Start AI Foundations", "Show team capability"],
  "agent_id": "AGENT-19",
  "model_tier": "haiku-4-5",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent + 4 tools.
2. Seed 6 cert definitions with frontmatter (id, name, role_targets, domain, required components).
3. Browse: filter role/domain.
4. Detail: required checklist with progress indicators (read from user profile).
5. Exercise page: structured input (code review submission, multiple choice, scenario response).
6. Earning a badge writes to `users/{name}.json` and surfaces on Personal Dashboard LearningProgressCard.
7. Team capability map: aggregates across all `users/*.json` (no auth-based filtering in demo per Q1).
8. Smoke test: complete AI Foundations → badge on dashboard → team map updates.

#### Definition of done
- [ ] FRs 069-071 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- LinkedIn export (post-demo Section 3.3)
- Externally accredited certifications (post-demo)
- Auto-recommended next certification (mini-feature, can be a later polish)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 069-071, AGENT-19
- Foundation: `ai_docs/tasks/00_foundation.md`
