# Task: Wave 5 (inserted) — AI SOW Generator (Module 30, AGENT-29)

> **Phase:** 5 (inserted — planned, not expedited; build order is the user's call)
> **Feature group:** Project's Work — engagement documents
> **Covers:** FR-084 (SOW inputs form), FR-085 (generate structured SOW), FR-086 (review/edit + export)
> **Builds:** AGENT-29 (AI SOW Generator, Sonnet 4.6 — template scaffolding + Sonnet generation for narrative sections)
> **Depends on:** 00, 01, 03 (can seed scope from an asset/reference), 16c (shares the engagement-economics inputs; optional)
> **Blocks:** none
> **Estimated effort:** ~1.5 days solo
> **Status:** ☑ DONE — deployed + live-verified (2026-06-11). AGENT-29 deployed (image-only
> diff, no IAM change); module-30 synced to S3. Live smoke: generate (6-week fraud-scoring
> pilot) → SOW with 7-section TOC, deliverables/milestones/pricing **verbatim**, a grounded
> Sonnet objectives narrative; **presigned export GET returned HTTP 200 (text/markdown, 3.4KB)**
> — FR-086 verified. Amplify #45 SUCCEED (commit `4450ff8`, bundled with the UI rebrand);
> sow-generator + [id] serve; dashboard Quick Action live.

---

## A. TL;DR Checklist

**Goal:** A form that takes engagement context and generates a draft Statement of Work — objectives, scope, deliverables, timeline/milestones, assumptions, pricing model, acceptance criteria — that the consultant can review, edit, and export.

**Build steps:**

1. AGENT-29 in ModuleAgentsLambda (Sonnet 4.6). **Deterministic section scaffold** (fixed SOW skeleton + any structured inputs placed verbatim) **+ Sonnet generation for the prose sections** (objectives, scope description, assumptions). Unlike AGENT-05's single-summary call, SOW is generation-heavy, so the Sonnet call produces the narrative sections in one structured pass; deterministic fallback = a skeleton SOW from the raw inputs.
2. Flip Module 30 `enabled=true` + `ui_route=/modules/sow-generator` in `modules.json`.
3. UI: `/modules/sow-generator` input form → result page rendering the SOW markdown with an **Export** (download `.md`; reuse the kit-builder presign-from-sessions pattern). Nav stub (`module-30`) → live; dashboard Quick Action.
4. Persist to the **sessions** bucket `sow/{slug(display_name)}/{id}.md` + JSON state (engagement-scoped, **not** vault — client-specific, must not enter the searchable KB). `list`/`get` read it back.
5. Smoke: enter a 6-week fraud-scoring engagement → SOW renders all sections, scope/deliverables reflect inputs, export downloads a coherent `.md`.

**Files to create/edit:**

- `agents/lambdas/modules/agent_29_sow.py` + register in `modules/router.py`
- `vault/modules.json` — flip Module 30
- `web/lib/sow.ts`, `web/app/(authenticated)/modules/sow-generator/page.tsx`, `.../[id]/page.tsx`, `.../actions.ts`, `web/components/sow/SowForm.tsx`
- `web/lib/nav.ts` — set `module-30` route + `enabled:true`

**Done when:**

- [ ] FRs 084–086 verified; DoD from `00_foundation.md` passed
- [ ] Deterministic skeleton + Sonnet narrative with fallback; structured inputs appear verbatim
- [ ] Saved + exported from the **sessions** bucket (not vault) — no KB pollution
- [ ] No new IAM (module-agents role already has Sonnet InvokeModel + sessions Put/Get + presign)

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **AI SOW Generator (Module 30, AGENT-29)** for the AI CoE Platform. Tasks 00–16 are done.

#### Pattern
A document generator: deterministic SOW skeleton (fixed section order; structured inputs — client, dates, pricing, named deliverables — placed verbatim) + ONE Sonnet call that fills the prose sections (objectives, scope description, assumptions, acceptance criteria). Deterministic fallback = skeleton populated from raw inputs only. Sonnet generation must be grounded in the supplied inputs (no invented commitments).

#### Inputs / model
```python
class SowRequest(BaseModel):
    op: Literal["generate", "get", "list"]
    client_context: str = ""
    engagement_type: str = ""        # assessment | pilot | build | advisory
    objectives: list[str] = []
    scope_items: list[str] = []
    deliverables: list[str] = []
    timeline_weeks: int = 0
    milestones: list[str] = []
    pricing_model: str = ""          # fixed | T&M | milestone
    assumptions: list[str] = []
    display_name: str = ""
    sow_id: str | None = None        # for get

class SowResult(BaseModel):
    title: str
    markdown: str                    # full rendered SOW
    sections: list[str]              # section headings (for the result-page TOC)
    download_url: str | None         # presigned from sessions, 1h
```

#### Steps
1. `agent_29_sow.py`: build the skeleton (deterministic); one `bedrock.converse` to draft the prose sections grounded in inputs (fallback = skeleton-only). Assemble final markdown. ops `generate`/`get`/`list`; register in router.
2. Flip Module 30 enabled + ui_route.
3. Web: multi-field form → result page (rendered SOW + section TOC + Export button) ; actions `generateSow`/`getSow`/`listSow`. Nav + dashboard Quick Action.
4. Persist `.md` + JSON to **sessions** bucket `sow/{slug}/...`; Export = presigned GET (reuse `06_kit_builder` pattern). Do NOT write to vault.
5. Tests: skeleton assembly, structured inputs verbatim, fallback path, sessions round-trip + presign.

#### Definition of done
- [ ] FRs 084–086; DoD from `00_foundation.md`
- [ ] Deterministic skeleton + grounded Sonnet prose + fallback
- [ ] Sessions persistence + presigned export; no new IAM

#### Out of scope
- E-signature / contract execution (post-demo)
- DOCX/PDF export (later; `.md` for the demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
- **2026-06-11:** Created from the nav reorg (Project's Work). Generation-heavy but grounded in supplied inputs with a deterministic skeleton fallback. Writes to **sessions** (engagement-scoped, not indexed) + presigned export, reusing the kit-builder artifact pattern — avoids the runtime-vault-writers KB-pollution issue. No new IAM.
- **2026-06-11 (build):** `_assemble` builds the fixed 7-section skeleton with structured
  inputs (deliverables, milestones, scope, pricing) placed **verbatim**; one Sonnet call
  drafts the prose sections (objectives narrative, scope description, acceptance criteria,
  extra assumptions) as a JSON object grounded in the inputs, parsed leniently. Skeleton-
  only fallback (default narrative + acceptance derived from deliverables) when Bedrock
  errors. Persisted to **sessions** `sow/{slug}/{id}.md` + `.json`; `get`/`generate` return
  a fresh 1h presigned GET for the **Export .md** button (kit-builder pattern). Never the
  vault → no KB pollution, no generated flag. Entry point: dashboard Quick Action.
  module-30 enabled synced to S3 (not committed — carries the 16e WIP entry).

**Verification (local):** `pytest agents/` 384 passed; `ruff` clean; `validate_vault.py`
OK (74 files); web `tsc`/`eslint` clean, `next build` succeeds with `/modules/sow-generator`
+ `/[id]`. skeleton assembly + verbatim inputs, Sonnet prose + skeleton fallback, and
sessions generate→get round-trip + presign covered by `test_agent_29.py`.

## D. References
- Pattern: `ai_docs/tasks/06_wave2_kit_builder.md` (sessions artifact + presigned export), `08_wave3_governance_checker.md` (deterministic + Sonnet)
- Foundation: `ai_docs/tasks/00_foundation.md`
