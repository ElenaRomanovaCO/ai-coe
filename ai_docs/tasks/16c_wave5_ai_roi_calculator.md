# Task: Wave 5 (inserted) — AI Project ROI Calculator (Module 29, AGENT-28)

> **Phase:** 5 (inserted — planned, not expedited; build order is the user's call)
> **Feature group:** Project's Work — engagement economics
> **Covers:** FR-081 (ROI inputs form), FR-082 (cost/value/ROI/payback computation), FR-083 (business-case narrative + saved result)
> **Builds:** AGENT-28 (AI Project ROI Calculator, Sonnet 4.6 — deterministic math + ONE Sonnet narrative, per `agent-05-orchestration` precedent)
> **Depends on:** 00, 01, 04 (dashboard surfaces it)
> **Blocks:** none
> **Estimated effort:** ~1 day solo
> **Status:** ☑ Built + verified locally (2026-06-11); commit/deploy pending review

---

## A. TL;DR Checklist

**Goal:** A form that takes an AI project's parameters and returns a defensible ROI estimate — total cost, expected annual value, ROI %, and payback period — plus a short business-case narrative. Result is saved per-engagement and viewable later.

**Build steps:**

1. AGENT-28 in ModuleAgentsLambda (Sonnet 4.6). **Deterministic financial model** (the numbers are computed in code, never by the LLM) **+ exactly ONE Sonnet call** to write the business-case narrative from the computed figures (deterministic fallback on failure) — mirrors AGENT-05 (`agent-05-orchestration.md`).
2. Flip Module 29 `enabled=true` + `ui_route=/modules/roi-calculator` in `modules.json`.
3. UI: `/modules/roi-calculator` input form → result page (headline metrics + cost/value breakdown + narrative). Nav stub (`module-29`) → live; dashboard Quick Action.
4. Persist the result to the **sessions** bucket `roi/{slug(display_name)}/{id}.json` (engagement-scoped, **not** vault — these are client-specific, must not enter the searchable KB). `list`/`get` read it back.
5. Smoke: enter a healthcare doc-processing project → cost, value, ROI %, payback months all compute; narrative reflects the figures; result re-loads via `get`.

**Files to create/edit:**

- `agents/lambdas/modules/agent_28_roi.py` + register in `modules/router.py`
- `vault/modules.json` — flip Module 29
- `web/lib/roi.ts`, `web/app/(authenticated)/modules/roi-calculator/page.tsx`, `.../[id]/page.tsx`, `.../actions.ts`, `web/components/roi/RoiForm.tsx`
- `web/lib/nav.ts` — set `module-29` route + `enabled:true`

**Done when:**

- [ ] FRs 081–083 verified; DoD from `00_foundation.md` passed
- [ ] Math is deterministic & unit-tested (LLM only writes prose); fallback narrative works
- [ ] Result saved to **sessions** bucket (not vault) — no KB pollution
- [ ] No new IAM (module-agents role already has Sonnet InvokeModel + sessions Put/Get)

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **AI Project ROI Calculator (Module 29, AGENT-28)** for the AI CoE Platform. Tasks 00–16 are done.

#### Pattern
Follow **AGENT-05** (`agent_05_governance.py`): deterministic core + ONE Sonnet summary call with a deterministic fallback. The ROI numbers MUST be computed in Python; the LLM only writes the narrative.

#### Inputs / model
```python
class RoiRequest(BaseModel):
    op: Literal["calculate", "get", "list"]
    project_name: str = ""
    industry: str = ""
    # cost drivers
    build_cost_usd: float = 0        # one-time build / delivery cost
    run_cost_usd_yr: float = 0       # annual run/licensing/infra
    team_size: int = 0
    duration_weeks: int = 0
    # value drivers (annualized)
    hours_saved_yr: float = 0
    loaded_hourly_rate_usd: float = 0
    revenue_uplift_usd_yr: float = 0
    other_benefit_usd_yr: float = 0
    horizon_years: int = 3
    display_name: str = ""
    roi_id: str | None = None        # for get

class RoiResult(BaseModel):
    total_cost_usd: float            # build + run*horizon
    annual_value_usd: float          # hours_saved*rate + revenue_uplift + other
    net_value_usd: float             # value*horizon - total_cost
    roi_pct: float                   # net_value / total_cost * 100
    payback_months: float | None     # build_cost / (annual_value - run_cost) *12 ; None if never
    narrative: str                   # ONE Sonnet call; fallback = templated summary
```

#### Steps
1. `agent_28_roi.py`: pure-function `compute(req) -> RoiResult` (deterministic; guard divide-by-zero → payback None). Then one `bedrock.converse` call: "Write a 2–3 paragraph business case from these figures" (fallback = templated string). ops `calculate`/`get`/`list`; register in router.
2. Flip Module 29 enabled + ui_route.
3. Web: form (cost + value driver inputs) → result page (headline ROI %, payback, cost vs value bars, narrative); actions `calculateRoi`/`getRoi`/`listRoi` → `invokeModule`. Nav + dashboard Quick Action.
4. Persist to **sessions** bucket `roi/{slug}/{id}.json`. Do NOT write to vault.
5. Tests: `compute` math (incl. payback edge cases / zero-cost guard), fallback narrative, sessions round-trip.

#### Definition of done
- [ ] FRs 081–083; DoD from `00_foundation.md`
- [ ] Deterministic math (unit-tested) + ONE Sonnet narrative w/ fallback
- [ ] Sessions-bucket persistence (not vault); no new IAM

#### Out of scope
- Multi-scenario / sensitivity analysis (later)
- PDF export (later; could reuse the kit-builder presign pattern)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
- **2026-06-11:** Created from the nav reorg (Project's Work). Deterministic-math + one-Sonnet-narrative per `agent-05-orchestration.md`. Writes to **sessions** (engagement-scoped, not indexed) to avoid the runtime-vault-writers KB-pollution issue. No new IAM.
- **2026-06-11 (build):** `compute(req) -> RoiResult` is a pure function (no LLM, no AWS):
  total_cost = build + run·horizon; annual_value = hours_saved·rate + uplift + other;
  net = value·horizon − cost; roi% guarded against zero cost; payback = build /
  (annual_value − run_cost)·12, with None when it never pays back and 0 when build is
  free. One Sonnet call writes the business case from those figures (templated fallback
  embeds the numbers). Persisted to **sessions** `roi/{slug}/{id}.json` only — never the
  vault, so no KB pollution and no generated-flag needed. Entry point is a dashboard
  Quick Action (nav.ts left to the design-pass owner). modules.json `module-29` enabled
  synced to S3 (not committed — it also carries the 16d/16e WIP entries).

**Verification (local):** `pytest agents/` 378 passed; `ruff` clean; `validate_vault.py`
OK (74 files); web `tsc`/`eslint` clean, `next build` succeeds with `/modules/roi-calculator`
+ `/[id]`. compute math (incl. payback edge cases + zero-cost divide guard), Sonnet
narrative + fallback, and sessions calculate→get→list round-trip covered by
`test_agent_28.py`.

## D. References
- Pattern: `ai_docs/tasks/08_wave3_governance_checker.md` (AGENT-05 deterministic+summary), `06_wave2_kit_builder.md` (sessions-bucket artifacts)
- Foundation: `ai_docs/tasks/00_foundation.md`
