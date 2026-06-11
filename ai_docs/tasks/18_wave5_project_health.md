# Task: Wave 5 — AI Project Health Monitor (Module 18, AGENT-17)

> **Phase:** 5
> **Feature group:** Wave 5 (Intelligence & Insight)
> **Covers:** FR-051 (register + post updates), FR-052 (flag deviations), FR-053 (portfolio view)
> **Builds:** AGENT-17 (Sonnet 4.6)
> **Depends on:** 00, 01, 02
> **Blocks:** none (but unlocks Active Engagements card on Personal Dashboard)
> **Estimated effort:** 2-3 days solo
> **Status:** ☑ DONE — deployed + live-verified (2026-06-11). Backend AGENT-17 deployed
> (image-only diff, no IAM change). Live smoke: register → post scope-change update →
> Sonnet returned **risk 78 / red** with **3 grounded flags** (refs resolved to real curated
> assets: kickoff-template, roi-template) → list_portfolio shows the banded engagement.
> FRs 051-053 verified. Amplify build #39 SUCCEED on `2d2cca1`; portfolio/new/[id] serve;
> dashboard Active Engagements card now reads live `list_portfolio`.

---

## A. TL;DR Checklist

**Goal:** User registers active engagements, posts text updates over time. AGENT-17 analyzes each update against best-practice patterns and flags deviations, risks, anti-patterns with remediation suggestions. A portfolio view lists all engagements with color-coded health.

**Build steps:**
1. AGENT-17 (Sonnet 4.6, 4 tools: register_engagement, post_update, analyze_update, list_portfolio).
2. Flip Module 18 enabled.
3. UI: list/portfolio view, engagement detail with update timeline + flag history.
4. Wire Personal Dashboard's Active Engagements card to live data.

**Files to create/edit:**

- `agents/lambdas/modules/agent_17_health.py`
- `vault/modules.json` — flip Module 18
- `web/app/(authenticated)/modules/project-health/page.tsx` — portfolio
- `web/app/(authenticated)/modules/project-health/[id]/page.tsx`
- `web/app/(authenticated)/modules/project-health/new/page.tsx`
- `web/app/(authenticated)/modules/project-health/actions.ts`
- `web/components/dashboard/ActiveEngagementsCard.tsx` — replace placeholder

**Done when:**
- [ ] FRs 051-053 verified
- [ ] Dashboard card shows live engagements
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **AI Project Health Monitor (Module 18)** for the AI CoE Platform. Tasks 00-17 are done.

#### Agent spec (AGENT-17)

```python
class RegisterEngagementRequest(BaseModel):
    display_name: str
    name: str
    industry: str
    ai_stage: int
    use_cases: list[str]
    start_date: str

class PostUpdateRequest(BaseModel):
    engagement_id: str
    update_text: str                                # free text
    update_type: Literal["status", "architecture", "scope-change", "blocker", "decision"]

class AnalyzeUpdateResponse(BaseModel):
    flags: list[HealthFlag]                        # severity, description, remediation, references
    risk_score: int                                # 0-100

class PortfolioView(BaseModel):
    engagements: list[EngagementSummary]            # with current risk_score color band
```

Tools: register_engagement, post_update, analyze_update (vector search against patterns + Sonnet reasoning), list_portfolio.

#### Engagement storage
- `vault/engagements/{display_name}/{engagement_id}/meta.md` (frontmatter + summary)
- `vault/engagements/{display_name}/{engagement_id}/updates/{ts}.md` (per update with analysis)
- `vault/engagements/{display_name}/{engagement_id}/health.md` (latest analyzed risk score)

#### modules.json entry
```json
{
  "id": "module-18",
  "name": "AI Project Health Monitor",
  "wave": 5,
  "purpose": "Track active AI engagements; flag risks and deviations from best practices.",
  "when_to_use": ["Daily standup notes", "Post a mid-engagement update", "Review portfolio risk"],
  "example_queries": ["Register a new engagement", "Update my fintech RAG project status", "Show my portfolio"],
  "agent_id": "AGENT-17",
  "model_tier": "sonnet-4-6",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent + 4 tools.
2. UI: portfolio table (engagement name, industry, last update, risk band) + per-engagement detail (timeline of updates, flags grouped).
3. Each posted update triggers `analyze_update`; flags persist in the update's .md.
4. Dashboard card now reads `list_portfolio` instead of stubs.
5. Smoke test: register an engagement, post 3 updates including one with scope-change content → flags appear; portfolio risk band shifts; dashboard card reflects.

#### Definition of done
- [ ] FRs 051-053 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Slack / Teams notifications (post-demo)
- Auto-pulling status from project management tools (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

- **2026-06-11: State model mirrors AGENT-02.** The structured source of truth is a
  per-engagement JSON in the **sessions** bucket (`engagements/{name}/{eid}.json`,
  read back by `get`/`list_portfolio`); human-readable markdown mirrors
  (`meta.md`, `updates/{ts}.md`, `health.md`) are written to the **vault** and tagged
  `generated: true` via the shared `export_frontmatter` helper — another consumer of the
  runtime-vault-writers convention, so engagement data (client-specific) is flagged out
  of curated chat KB search. (No `engagements` schema needed in `validate_vault`: these
  files are runtime-written, never committed.)
- **2026-06-11: `analyze_update` is the one LLM step, vector-grounded.** It embeds the
  update (Titan), vector-searches the **curated** assets (`content_type == "assets"`)
  for best-practice references — deliberately *not* other engagement updates (those are
  generated-flagged) — then asks Sonnet for flags (severity/description/remediation/refs)
  + a 0-100 risk score grounded in those references. Deterministic heuristic fallback
  keyed on `update_type` (blocker 70 / scope-change 55 / …) when Bedrock errors. Risk →
  band: green <34, amber 34-66, red ≥67; portfolio risk = latest update's score.
- **2026-06-11: Dashboard card now live.** `ActiveEngagementsCard` is a client component
  reading `list_portfolio` for the current display name (riskiest first), replacing the
  Wave-1 placeholder. Portfolio + register pages are client (need display_name from
  localStorage); the `[id]` detail is a server component (find-by-id needs no name) with
  a client `PostUpdateForm` that `router.refresh()`es after analysis. No workers, no IAM
  change.

**Verification (local):** `pytest agents/` 357 passed; `ruff` clean; `validate_vault.py`
OK (74 files); web `tsc`/`eslint` clean, `next build` succeeds with `/modules/project-health`,
`/new`, `/[id]`. register, post_update (analysis + flag persistence + band shift),
fallback, get timeline, and list_portfolio sorting covered by `test_agent_17.py`.

## D. References
- Brief: FRs 051-053, AGENT-17
- Foundation: `ai_docs/tasks/00_foundation.md`
