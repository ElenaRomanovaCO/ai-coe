# Task: Wave 5 (inserted) — Vendor Vetting (Module 31, AGENT-30 + WORKER-20)

> **Phase:** 5 (inserted — planned, not expedited; build order is the user's call)
> **Feature group:** Project's Work — vendor risk & approval
> **Covers:** FR-087 (browse vendors + vetting status), FR-088 (run a vetting assessment → risk tier + checklist), FR-089 (set & track approval status)
> **Builds:** AGENT-30 (Vendor Vetting, Sonnet 4.6 — deterministic catalog + deterministic vetting scorer + ONE Sonnet summary), WORKER-20 vetting_scorer (deterministic)
> **Depends on:** 00, 01 (the 5 seed vendors in `vault/vendors/`), 10 (mirrors AGENT-24's list/get/assess shape)
> **Blocks:** none
> **Estimated effort:** ~1.5 days solo
> **Status:** ☑ Built + verified locally (2026-06-11); commit/deploy pending review

---

## A. TL;DR Checklist

**Goal:** A vendor risk/approval tool that complements **Benchmarks** (capability comparison). Browse AI vendors, run a security/compliance **vetting assessment** against a fixed control checklist → risk tier + gaps, and record an **approval status** (approved / conditional / rejected) that persists for the team.

**The split (important):** Benchmarks (Module 13) answers *"which vendor/model performs best."* Vendor Vetting (this) answers *"are we allowed to use it and is it safe."* Both read `vault/vendors/`; this one focuses on security posture, data handling, certifications, and approval — not capability.

**Build steps:**

1. WORKER-20 vetting_scorer — **deterministic**, no LLM: scores a vendor against a fixed control catalog (data residency, sub-processors, encryption, SOC 2 / ISO 27001 / HIPAA BAA availability, model-training-on-customer-data, retention) → risk tier (low/medium/high) + per-control pass/gap. Pure-compute, trivially testable.
2. AGENT-30 in ModuleAgentsLambda (Sonnet 4.6): ops `list` / `get` / `assess` / `set_status`. `assess` runs WORKER-20 + ONE Sonnet call for the risk narrative (deterministic fallback) — the AGENT-05 / AGENT-24 precedent. Register in `modules/router.py` REGISTRY.
3. Flip Module 31 `enabled=true` + `ui_route=/modules/vendor-vetting` in `modules.json`.
4. UI: `/modules/vendor-vetting` browse (vendors + risk/approval badges) + `[id]` detail (vendor profile + vetting checklist + approval control + reused `AssetChatPanelHook`). Nav stub (`module-31`) → live; dashboard Quick Action.
5. Smoke: open an LLM vendor → run assessment → risk tier + control checklist + narrative; set status = "Conditional" → persists and shows on the browse list.

**Files to create/edit:**

- `agents/lambdas/workers/worker_20_vetting_scorer.py` + register in `workers/router.py`
- `agents/lambdas/modules/agent_30_vendor_vetting.py` + register in `modules/router.py`
- `vault/modules.json` — flip Module 31
- `web/lib/vendorVetting.ts`, `web/app/(authenticated)/modules/vendor-vetting/page.tsx`, `.../[id]/page.tsx`, `.../actions.ts`, `web/components/vetting/VettingChecklist.tsx`
- `web/lib/nav.ts` — set `module-31` route + `enabled:true`

**Done when:**

- [ ] FRs 087–089 verified; DoD from `00_foundation.md` passed
- [ ] Vetting score is deterministic & unit-tested (LLM only writes the narrative)
- [ ] Approval status persists (org-shared) and surfaces on the browse list
- [ ] No new IAM (module-agents + workers roles already cover vault Get/Put/List + Sonnet)

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Vendor Vetting (Module 31, AGENT-30 + WORKER-20)** for the AI CoE Platform. Tasks 00–16 are done.

#### Pattern
Mirror **AGENT-24** (compliance) for the list/get/assess shape and **AGENT-05** for "deterministic worker + ONE Sonnet summary." Reads the existing `vault/vendors/*.md`. The risk tier and per-control results are computed deterministically by WORKER-20; Sonnet only writes the narrative.

#### Control catalog (WORKER-20, deterministic)
Fixed list, e.g.: data residency / region, sub-processor disclosure, encryption at rest & in transit, SOC 2 Type II, ISO 27001, HIPAA BAA available, trains-on-customer-data (flag), data retention window, access controls / SSO. Each control → pass | gap | unknown from the vendor frontmatter/body; risk tier from weighted gaps (any "trains-on-customer-data: yes" or missing BAA for a healthcare context ⇒ high).

#### Inputs / model
```python
class VettingRequest(BaseModel):
    op: Literal["list", "get", "assess", "set_status"]
    vendor_id: str | None = None
    context_industry: str = ""          # e.g. healthcare → BAA becomes load-bearing
    data_sensitivity: str = ""          # public | internal | pii | phi
    status: str | None = None           # for set_status: approved | conditional | rejected
    note: str = ""
    display_name: str = ""

class VettingResult(BaseModel):
    vendor_id: str
    risk_tier: str                      # low | medium | high
    controls: list[dict]                # {control, result, detail}
    gaps: list[str]
    approval_status: str                # approved | conditional | rejected | unvetted
    narrative: str                      # ONE Sonnet call; fallback = templated
```

#### Persistence
Approval/vetting record = an **org-shared JSON sidecar** in the vault bucket `vendors/_vetting/{vendor_id}.json` (NOT a `.md`, so the re-embed pipeline does not index it — same trick as `assets/_metadata/`). This keeps approvals team-wide without polluting the searchable KB.

#### Steps
1. WORKER-20 (deterministic scorer) + register in workers router. AGENT-30 (`list`/`get`/`assess`/`set_status`) — `assess` = WORKER-20 + one Sonnet narrative (fallback); `set_status` writes the sidecar. Register in modules router.
2. Flip Module 31 enabled + ui_route.
3. Web: browse (vendor cards + risk/approval badges) + `[id]` detail (profile + `VettingChecklist` + approval control + "Chat with this" via `AssetChatPanelHook`). Nav + dashboard Quick Action.
4. Tests: WORKER-20 scoring (incl. PHI-without-BAA ⇒ high), fallback narrative, sidecar round-trip, status persistence.

#### Definition of done
- [ ] FRs 087–089; DoD from `00_foundation.md`
- [ ] Deterministic scoring (unit-tested) + ONE Sonnet narrative w/ fallback
- [ ] Org-shared `vendors/_vetting/` JSON sidecar (non-indexed); no new IAM

#### Out of scope
- Automated questionnaire ingestion / vendor portal (post-demo)
- Contract & renewal tracking (later; could extend the sidecar)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
- **2026-06-11:** Created from the nav reorg. Complements Benchmarks (Module 13 = capability) with the risk/approval side. Deterministic scorer + one Sonnet narrative (AGENT-05/AGENT-24 precedent). Approvals persist as a **non-indexed JSON sidecar** in vault (`vendors/_vetting/`, like `assets/_metadata/`) — org-shared, no KB pollution, no new IAM.
- **2026-06-11 (build):** The seed vendors are *capability-comparison* docs and carried no
  security posture, so each `vault/vendors/*.md` was enriched with a **`vetting:` frontmatter
  block** (data residency, sub-processors, encryption, SOC 2 / ISO 27001 / HIPAA BAA,
  trains-on-customer-data, retention, SSO). Pydantic ignores the extra key, so
  `VendorEvalFrontmatter`/`validate_vault` still pass. Postures are varied to demo all tiers
  (cloud + vector-db = low, embeddings = medium, orchestration = unknown-heavy medium,
  llm-document-analysis = **high** via trains-on-customer-data). WORKER-20 scores a fixed
  10-control catalog → tier (hard-high on trains-on-data, or PHI-context without BAA);
  AGENT-30 `assess` = WORKER-20 + one Sonnet narrative (fallback), persisting risk+controls
  to the sidecar; `set_status` records approval; both coexist in one `vendors/_vetting/{id}.json`.
- **2026-06-11: drift reconciliation** — `modules.json` (module-16/29/30/31 `enabled`) and
  `nav.ts` (wired ROI/SOW/Vetting live, was "Coming soon") were committed with this task,
  resolving the repo↔S3 drift from earlier tasks where those files carried in-flight WIP.

**Verification (local):** `pytest agents/` 402 passed; `ruff` clean; `validate_vault.py` OK
(79 files); web `tsc`/`eslint` clean, `next build` succeeds with `/modules/vendor-vetting` +
`/[id]`. WORKER-20 scoring (incl. trains-on-data⇒high, PHI-without-BAA⇒high, unknown-heavy),
AGENT-30 list/get/assess/set_status + sidecar round-trip + fallback covered by
`test_worker_20.py` / `test_agent_30.py`.

## D. References
- Pattern: `ai_docs/tasks/10_wave3_compliance_tracker.md` (AGENT-24 list/get/assess + WORKER scorer), `08_wave3_governance_checker.md` (deterministic + Sonnet), `03_wave1_asset_library.md` (`_metadata` sidecar)
- Foundation: `ai_docs/tasks/00_foundation.md`
