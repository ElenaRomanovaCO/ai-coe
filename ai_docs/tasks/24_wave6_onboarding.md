# Task: Wave 6 — Consultant Onboarding Journey (Module 23, AGENT-22)

> **Phase:** 6
> **Feature group:** Wave 6 (Client-Facing & People)
> **Covers:** FR-067 (personalized path), FR-068 (guided tour + 30-day checklist)
> **Builds:** AGENT-22 (Haiku 4.5)
> **Depends on:** 00, 01, 02, 04 (Personal Dashboard)
> **Blocks:** none
> **Estimated effort:** 1-2 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** A new user fills out a profile (role, experience, industry focus, AI background). System generates a personalized onboarding path: top assets to know, recommended first learning modules, suggested community connections, key tools for the role. Guided tour with tooltips. 30-day checklist tracks progress.

**Build steps:**
1. AGENT-22 (Haiku 4.5, 3 tools: generate_path, list_first_actions, recommend_connections).
2. Flip Module 23 enabled.
3. `/modules/onboarding/profile` form + `/modules/onboarding/path` personalized path view.
4. First-time-login hook: after login if user has no `onboarding_completed=true` in profile, route to onboarding.
5. Guided tour: tooltip overlay on first visit to each module.

**Files to create/edit:**

- `agents/lambdas/modules/agent_22_onboarding.py`
- `vault/modules.json` — flip Module 23
- `web/app/(authenticated)/modules/onboarding/profile/page.tsx`
- `web/app/(authenticated)/modules/onboarding/path/page.tsx`
- `web/app/(authenticated)/modules/onboarding/actions.ts`
- `web/components/GuidedTour.tsx`

**Done when:**
- [ ] FRs 067-068 verified
- [ ] First-time user lands on profile capture
- [ ] Personalized path renders based on profile
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Consultant Onboarding Journey (Module 23)** for the AI CoE Platform. Tasks 00-23 are done.

#### Agent spec (AGENT-22)

```python
class OnboardingProfile(BaseModel):
    role: Literal["consultant", "architect", "data-engineer", "pm", "executive"]
    experience_years: int
    industry_focus: list[str]
    ai_background: Literal["novice", "intermediate", "advanced"]
    goals: list[str]

class OnboardingPath(BaseModel):
    user: str
    top_assets: list[AssetSummary]                  # 5-7
    learning_paths: list[LearningPathSummary]
    suggested_connections: list[ExpertSummary]
    key_tools: list[ToolSummary]
    first_actions: list[ActionItem]                 # 30-day checklist items
```

Tools: generate_path, list_first_actions, recommend_connections.

#### modules.json entry
```json
{
  "id": "module-23",
  "name": "Consultant Onboarding",
  "wave": 6,
  "purpose": "Personalized first-30-days onboarding path for new consultants.",
  "when_to_use": ["First login", "After role change", "Refresh after a long break"],
  "example_queries": ["Set up my profile", "Show my onboarding path"],
  "agent_id": "AGENT-22",
  "model_tier": "haiku-4-5",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent + 3 tools.
2. Profile form: 5 inputs, save to `users/{name}.json`.
3. Path page: 5 sections, each with cards linking to module pages.
4. 30-day checklist: checkboxes that update user profile.
5. Guided tour: an opt-in tooltip overlay when a module page is opened for the first time per user.
6. Smoke test: complete profile as architect + healthcare focus → personalized path emphasizes healthcare assets + architect-tier learning + tool repo.

#### Definition of done
- [ ] FRs 067-068 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Buddy / mentor matching workflow (post-demo)
- LMS integration (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

**2026-06-12 — CODE-COMPLETE (backend + UI), NOT deployed.** AGENT-22
(`agents/lambdas/modules/agent_22_onboarding.py`, Haiku, fully mechanical — no
chat-LLM loop) **composes three existing agents in-process** (AGENT-03 assets,
AGENT-07 learning paths + experts, AGENT-08 tools) and persists to the shared
`users/{slug}.json` profile (read-modify-write, never clobbers saved assets /
office-hour signups). Ops: `generate_path` (default, the full personalized
OnboardingPath — FR-067), `save_profile` (validates the OnboardingProfile,
sets `onboarding_completed=true`), `get_profile`/`read_profile`,
`list_first_actions` (the 30-day checklist with done-state merged — FR-068),
`recommend_connections` (experts by industry), `update_checklist` (toggle one
item, persisted). Personalization is deterministic: top assets ranked by
industry-focus + goal-tag overlap (backfilled so the path is never empty),
learning paths matched on a role→learning-role map, tools ranked by an
ai_background→stage band, experts filtered by industry_focus. **No Titan / S3
Vectors call → no new IAM** (module-agents role already has vault Get/List +
sessions Get/Put). Registered AGENT-22 in `modules/router.py`; flipped
module-23 `enabled:true` + `ui_route:/modules/onboarding` in `modules.json`.

Web: `/modules/onboarding` landing (intro + highlights + CTA), `/profile`
(role / experience / AI-background / industry-focus / goals form → `save_profile`
→ routes to path), `/path` (5 sections — top assets, learning, key tools,
people, each linking into its module — plus a grouped Week 1–4 **30-day checklist**
with optimistic, persisted checkboxes + progress bar). New reusable
`web/components/GuidedTour.tsx` (opt-in tooltip-overlay walkthrough, per-tour
localStorage dismissal, re-triggerable via "Take a tour") mounted on the path
page (FR-068 guided tour). `web/lib/onboarding.ts` types + `actions.ts` server
actions. Nav module-23 flipped live; dashboard QuickActions adds "Start
Onboarding"; **first-time hook**: the dashboard redirects a user with no
`onboarding_completed` to `/profile` once (guarded by an `onboarding_prompted`
localStorage flag so it never hijacks return visits).

Gates: 459 pytest (14 new in `tests/test_agent_22.py`), ruff clean, `python app.py`
synth exit 0, vault valid 108, web lint + build clean (3 onboarding routes).
**REMAINING:** commit (held per hand-off-deploy rule) → `cdk deploy AiCoE-Agents`
→ re-sync `modules.json` to vault bucket → push (Amplify auto-builds onboarding
pages) → user live smoke (FR-067 profile → personalized path; FR-068 guided tour +
30-day checklist persists) → flip INDEX/header ☑.

## D. References
- Brief: FRs 067-068, AGENT-22
- Foundation: `ai_docs/tasks/00_foundation.md`
