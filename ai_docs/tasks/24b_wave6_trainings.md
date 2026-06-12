# Task: Wave 6 (inserted, expedited) — Trainings (Module 32, AGENT-31)

> **Phase:** 6 (inserted — **expedited ahead of the rest of Wave 6 at the user's request**; build it live now)
> **Feature group:** Learn & Community — enablement
> **Covers:** FR-090 (hosted-trainings catalog), FR-091 (curated external tutorials grouped by theme), FR-092 (browse / filter / detail + save to dashboard)
> **Builds:** AGENT-31 (Trainings, Haiku 4.5 — **mechanical** catalog reads, no LLM loop; mirrors how AGENT-03 ended up)
> **Depends on:** 00 (substrate), 01 (vault seed pattern), 03 (Asset Library — reuse its browse/detail UI + sidecar/save patterns), 04 (dashboard save), 06b (nav shell)
> **Blocks:** nothing — but it **enriches** 24 (Onboarding) and 25 (Certification): both can later link to training `id`s instead of re-inventing learning content.
> **Estimated effort:** ~1 day solo
> **Status:** ◐ CODE-COMPLETE 2026-06-12 — backend + UI built, tests/lint/synth/build green,
> NOT deployed (deploy + user live smoke pending). See Notes & Decisions Log (Build entry).
>
> **🎨 Design references — build to match these (they take precedence over any sketch below):**
> - Design system: `ui-designs/design-system.md` (Praxis wordmark, Hanken Grotesk, indigo)
> - Brief: `ui-designs/pages/30-trainings.md`
> - Reuse the Asset Library browse/detail shell: `ui-designs/pages/04-asset-library.md`, `05-asset-detail.md`

---

## A. TL;DR Checklist

**Goal:** A `/modules/trainings` catalog with two sections — **Hosted Trainings** (sessions
the CoE runs/records) and **Recommended Tutorials** (curated external courses from Udemy /
YouTube / LinkedIn Learning, **grouped by theme**). Users browse, filter by theme / source /
level / format, open a detail page, follow the link (external tutorial or recording), and save
items to their dashboard. Read-only, curated, no agent LLM loop.

**Build steps:**

1. **Seed content** — author ~12–15 training entries under `vault/trainings/*.md` with a new
   `TrainingFrontmatter` schema (below), spread across ~5–6 themes and a mix of `kind: hosted`
   and `kind: tutorial`. Add `trainings` to `validate_vault.py`'s known content types.
2. **AGENT-31** in ModuleAgentsLambda (Haiku 4.5), **mechanical** like AGENT-03: ops
   `list_trainings(filters)`, `get_training(id)`, plus `save_training`/`unsave` writing to the
   user profile (same `users/{slug}.json` pattern as AGENT-03). No chat-LLM loop. Register in
   `modules/router.py`.
3. **Register `module-32`** in `vault/modules.json` (entry below), `enabled: true`,
   `ui_route: /modules/trainings`. **Re-sync `modules.json` to the vault bucket** so the
   orchestrator hot-reloads it (chat can then surface trainings).
4. **UI** — `/modules/trainings` (tabbed: Hosted | Recommended; theme/source/level filters;
   grouped-by-theme view for tutorials) + `/modules/trainings/[id]` (detail: summary, source
   badge, presenter/author, duration, level, "Open" CTA → `url`, materials, `last_verified`).
   Reuse Asset Library's `MarkdownRenderer` / card / filter components.
5. **Nav + dashboard** — flip `module-32` in `web/lib/nav.ts` (Learn & Community group) from
   stub → live link; add a dashboard Quick Action.
6. **Smoke** — browse → filter by theme "RAG & Retrieval" → grid reduces → open a tutorial →
   "Open" links out (new tab, `rel=noopener`) → save → appears on dashboard → a hosted item
   shows presenter + recording link.

**Files to create/edit:**

- `vault/trainings/*.md` (seed) · `vault/schemas/` (TrainingFrontmatter) · `scripts/validate_vault.py` (allow `trainings`)
- `agents/lambdas/modules/agent_31_trainings.py` + register in `modules/router.py`
- `vault/modules.json` — add `module-32`
- `web/app/(authenticated)/modules/trainings/page.tsx`, `.../[id]/page.tsx`, `.../actions.ts`
- `web/components/trainings/*` (reuse AssetCard/filters where possible)
- `web/lib/nav.ts` — set `module-32` route + `enabled:true`

**Done when:**

- [ ] FR-090/091/092 smoke-verified; DoD from `00_foundation.md` passed
- [ ] Grid lists all seed trainings; theme/source/level/format filters work; tutorials group by theme
- [ ] Detail page opens external links safely (`target=_blank rel="noopener noreferrer"`) and recording links for hosted items
- [ ] Save round-trips to the user profile → shows on dashboard
- [ ] `modules.json` re-synced to vault bucket; chat `list_modules` includes Trainings
- [ ] No new IAM (module-agents role already has vault read + sessions read/write)
- [ ] No company names; external course-platform names (Udemy/YouTube/LinkedIn Learning) ARE allowed as catalog sources

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Trainings (Module 32, AGENT-31)** for the AI CoE Platform. Tasks 00–21
and the expedited Wave-5 inserts are done. This is a curated, read-only catalog — model it on
the **Asset Library (Module 2, AGENT-03)**, which is the closest precedent.

#### Pattern
Follow **AGENT-03** (`agent_03_asset_library.py`): a **mechanical** module agent — deterministic
S3 reads for list/get, read-modify-write of the user profile for save. **No chat-LLM loop**
(this is curated content, not generative). Seed content lives in the **vault** (it is general
reference material and SHOULD be indexed so Chat/Q&A can recommend it) — NOT the sessions bucket.

#### Content schema (`TrainingFrontmatter`)
```yaml
id: trn-rag-deeplearning-short        # stable, kebab; Onboarding/Certification will reference these
title: "Building RAG Applications"
summary: "Hands-on intro to retrieval-augmented generation."
kind: tutorial                        # "hosted" | "tutorial"
theme: "RAG & Retrieval"              # one of the curated themes (taxonomy below)
source: "YouTube"                     # "Internal" | "Udemy" | "YouTube" | "LinkedIn Learning" | ...
level: intermediate                   # "beginner" | "intermediate" | "advanced"
url: "https://..."                    # external course (tutorial) OR recording link (hosted)
duration_min: 95
author: "Generic Instructor"          # tutorials: instructor; hosted: use `presenter`
presenter: ""                         # hosted only
session_date: ""                      # hosted only (ISO)
materials: []                         # hosted: list of {label,url} (slides/repo)
tags: ["rag","embeddings"]
last_verified: "2026-06-12"           # link-rot governance — owner re-checks periodically
updated_at: "2026-06-12"
```
Curated **themes** (reuse vault tag vocabulary where it overlaps): `Foundations`,
`Prompt Engineering`, `RAG & Retrieval`, `Agents & Orchestration`, `AWS & Bedrock`,
`Governance, Risk & Ethics`, `Delivery & Consulting`.

#### Agent specification (AGENT-31)
```python
class ListTrainingsRequest(BaseModel):
    op: Literal["list", "get", "save", "unsave"]
    theme: str | None = None
    source: str | None = None
    level: str | None = None
    kind: str | None = None          # hosted | tutorial
    query: str | None = None         # simple substring/tag match (no vector call needed)
    training_id: str | None = None   # get/save/unsave
    display_name: str = ""
    limit: int = 100

class TrainingSummary(BaseModel):
    id: str; title: str; summary: str; kind: str; theme: str
    source: str; level: str; url: str; duration_min: int
    author: str; presenter: str; tags: list[str]; last_verified: str
```
Tools/ops: `list_trainings(filters)` (deterministic read of `vault/trainings/`), `get_training(id)`,
`save_training`/`unsave_training` (read-modify-write `users/{slug}.json` in sessions bucket —
same as AGENT-03). Model tier Haiku 4.5; the agent does NOT call an LLM in any op.

#### modules.json entry (add `module-32`)
```json
{
  "id": "module-32",
  "name": "Trainings",
  "wave": 6,
  "purpose": "Browse CoE-hosted trainings and curated external tutorials (Udemy, YouTube, LinkedIn Learning) grouped by theme.",
  "when_to_use": [
    "User wants to learn a topic and asks for a course or tutorial",
    "User asks what hosted trainings or recordings are available",
    "User needs a recommended learning resource for a theme (RAG, agents, governance, ...)"
  ],
  "example_queries": [
    "What trainings do we have on RAG?",
    "Recommend a beginner course on prompt engineering",
    "Show recorded sessions on Bedrock"
  ],
  "agent_id": "AGENT-31",
  "model_tier": "haiku-4-5",
  "worker_ids": [],
  "ui_route": "/modules/trainings",
  "enabled": true
}
```

#### UI specification
- **`/modules/trainings`**: header + count; tabs **Hosted** / **Recommended Tutorials**;
  left filters (theme, source, level, kind); in the Recommended tab, group cards **by theme**
  (section headers). Card = title, source badge, level, duration, theme chip, save button.
- **`/modules/trainings/[id]`**: title + badges (source, level, theme, duration); summary
  (rendered markdown); **Open** primary CTA → `url` (`target=_blank rel="noopener noreferrer"`);
  for `hosted`: presenter, session date, materials links; footer `last_verified` date; Save.
- **Nav**: flip `module-32` (Learn & Community) to live. **Dashboard**: a Trainings Quick Action.

#### Steps
1. Author `vault/trainings/*.md` seed (~12–15, ≥5 themes, mix hosted/tutorial). Allow `trainings`
   in `validate_vault.py`; add `TrainingFrontmatter` to the vault schemas.
2. `agent_31_trainings.py` (mechanical list/get/save/unsave); register in `router.py`.
3. Add `module-32` to `modules.json`; **re-sync to the vault bucket**.
4. Build the two pages + server actions (`listTrainings`/`getTraining`/`saveTraining` →
   `invokeModule`). Reuse Asset Library components.
5. nav.ts live link + dashboard Quick Action.
6. Smoke per the DoD below.

#### Definition of done
- [ ] FR-090/091/092 verified; DoD from `00_foundation.md`
- [ ] Filters + group-by-theme work; external links open safely; save round-trips to dashboard
- [ ] `modules.json` re-synced; chat `list_modules` includes Trainings
- [ ] No new IAM; `pytest`/`ruff`/`validate_vault.py`/web `tsc`+`eslint`+`next build` clean

#### Out of scope (note for later)
- Onboarding/Certification linking to training `id`s (they consume this; build when those modules land)
- In-app video hosting / SCORM / completion tracking (link-out only for now)
- Automated dead-link checking (manual `last_verified` for now; could be a later cron)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
- **2026-06-12 — BUILD (backend-core + UI), code-complete, NOT deployed.** AGENT-31 `TrainingsAgent`
  (`agent_31_trainings.py`, Haiku, mechanical, no LLM) over `vault/trainings/`: ops `list` (theme/source/
  level/kind/query filters), `get` (body + hosted fields/materials), `save`/`unsave` + `list_saved`
  (read-modify-write `users/{slug}.json` under a dedicated `saved_trainings` list, so it doesn't collide
  with AGENT-03's `saved`). Registered in router; module-32 added to modules.json (enabled + ui_route).
  New `TrainingFrontmatter` schema + `trainings` content type in `CONTENT_TYPE_BY_FOLDER`. **13 seed files**
  (8 tutorials across Foundations/Prompt Eng/RAG/Agents/AWS-Bedrock/Governance/Delivery + 5 hosted with
  presenter/date/materials; generic instructors, external platform names allowed per decision). Web:
  `/modules/trainings` (TrainingsBrowser: Hosted | Recommended tabs, theme/source/level filters, tutorials
  grouped by theme, save toggle) + `/modules/trainings/[id]` (badges, Open CTA `target=_blank rel=noopener`,
  hosted presenter/date/materials, last_verified, Save) + dashboard `SavedTrainingsCard` (self-fetches via
  `list_saved` — no AGENT-16 change) + QuickActions "Browse Trainings" + nav module-32 live. **No new IAM.**
  Gates: 436 pytest (8 new `tests/test_agent_31.py`), ruff clean, synth exit 0, vault valid (107), web
  lint+build clean (2 trainings routes). **REMAINING:** deploy (`cdk deploy AiCoE-Agents` → re-sync
  modules.json + **sync `vault/trainings/`** to vault bucket → push) + user live smoke (FR-090/091/092:
  theme filter; tutorials grouped; Open opens new tab; save → dashboard). Then flip INDEX/header ☑.
- **2026-06-12:** Created (tech-lead enhancement). New `module-32` in Learn & Community —
  distinct from Onboarding (a *journey*) and Certification (a *credential*); this is a content
  **catalog**. Expedited live ahead of the rest of Wave 6 at the user's request: it is
  agent-free (no per-use LLM cost), locally verifiable, and reuses Asset Library patterns.
  Decisions: (1) **mechanical AGENT-31** (no LLM loop, mirrors how AGENT-03 shipped) keeps
  modules.json schema-valid + chat-routable at ~zero cost; (2) **seed into the vault** (not
  sessions) — curated reference content SHOULD be indexed so Chat/Q&A surface it (KB-pollution
  rule is about runtime client-specific writes only); (3) **stable training `id`s** so
  Onboarding/Certification can reference them later (cheap now, costly to retrofit); (4)
  external course-platform names are allowed as catalog `source`s — the no-company-names rule
  is about hiding the consultancy's own identity, not third-party course providers; (5)
  `last_verified` field for external link-rot governance. No new IAM.

- 2026-06-12: Curated reference content is seeded into the vault, not the sessions bucket — curated catalog content is indexed (unflagged) so chat/Q&A surface it; the KB-pollution rule applies only to runtime/client/transient writes. See `vault/decisions/curated-content-in-vault.md`.
- 2026-06-12: Third-party provider names are allowed as source/attribution values — the "no company names" rule hides the consultancy's own identity (and real clients), not third-party platforms (Udemy/YouTube/LinkedIn Learning) referenced as sources. See `vault/decisions/third-party-names-as-sources.md`.

## D. References
- Pattern: `ai_docs/tasks/03_wave1_asset_library.md` (mechanical read-only module, sidecar/save, modules.json re-sync)
- Related Learn & Community modules: `24_wave6_onboarding.md`, `25_wave6_certification.md`
- Foundation: `ai_docs/tasks/00_foundation.md`
