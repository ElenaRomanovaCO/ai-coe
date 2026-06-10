# Task: Wave 3 — Global AI Regulation & Compliance Tracker (Module 25, AGENT-24 + WORKER-12/13)

> **Phase:** 3
> **Feature group:** Wave 3 (Risk & Governance)
> **Covers:** FR-029 (browse filtered), FR-030 (per-reg detail), FR-031 (apply to use case)
> **Builds:** AGENT-24 (Sonnet 4.6), WORKER-12 reg_summarizer, WORKER-13 applicability_checker
> **Depends on:** 00, 01 (seeded regulations critical), 02, 07 (Universal Asset Q&A pattern reused)
> **Blocks:** Module 4 enrichment (Module 4 will link here once both exist)
> **Estimated effort:** 2-3 days solo
> **Status:** ☑ Done — deployed + live-verified (backend + UI smoke) 2026-06-10

---

## A. TL;DR Checklist

**Goal:** User can browse regulations (filter by geography, industry, status, AI use case type), open any one to read summary + checklist, or ask Chat to apply a regulation to a specific use case.

**Build steps:**

1. WORKER-12 reg_summarizer (regulation → plain language summary).
2. WORKER-13 applicability_checker (regulation + use case → applicability checklist).
3. AGENT-24 in ModuleAgentsLambda (Sonnet 4.6).
4. Flip Module 25 enabled.
5. `/modules/compliance-tracker` browse + detail pages. Embed Universal Asset Q&A panel on each regulation detail.
6. Cross-link from Governance Checker (Module 4): regulation links in checklists now route here.

**Files to create/edit:**

- `agents/lambdas/workers/worker_12_reg_summarizer.py`
- `agents/lambdas/workers/worker_13_applicability_checker.py`
- `agents/lambdas/modules/agent_24_compliance.py`
- `vault/modules.json` — flip Module 25
- `web/app/(authenticated)/modules/compliance-tracker/page.tsx`
- `web/app/(authenticated)/modules/compliance-tracker/[id]/page.tsx` — embed AssetChatPanel
- `web/app/(authenticated)/modules/compliance-tracker/actions.ts`

**Done when:**

- [ ] FRs 029-031 verified
- [ ] Browse filters work across seeded regulations
- [ ] Detail page renders + Q&A panel works
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Global AI Regulation & Compliance Tracker (Module 25)** for the AI CoE Platform. Tasks 00-09 are done. Seeded regulations exist under `vault/regs/`.

#### Worker specs
- **WORKER-12 reg_summarizer**: regulation full text → plain language summary + key requirements + sector implications
- **WORKER-13 applicability_checker**: regulation + use case description → list of applicability items (which clauses apply, which do not)

#### Agent spec (AGENT-24)

```python
class ListRegulationsRequest(BaseModel):
    geography: str | None
    industry: str | None
    status: str | None
    use_case_type: str | None
    query: str | None

class RegulationDetailRequest(BaseModel):
    reg_id: str

class ApplyRegulationRequest(BaseModel):
    reg_id: str
    use_case_description: str
    industry: str
    geography: str
```

Tools: list_regulations, get_regulation, invoke_worker (WORKER-12), invoke_worker (WORKER-13).

#### modules.json entry
```json
{
  "id": "module-25",
  "name": "Compliance Tracker",
  "wave": 3,
  "purpose": "Browse, search, and apply AI regulations across geographies and industries.",
  "when_to_use": ["Before delivery in a regulated industry", "When a new regulation may apply", "When a client asks about specific compliance"],
  "example_queries": ["What does the EU AI Act say about high-risk use cases?", "Find regulations for healthcare AI in the US", "Apply HIPAA to this clinical decision tool"],
  "agent_id": "AGENT-24",
  "model_tier": "sonnet-4-6",
  "worker_ids": ["WORKER-12", "WORKER-13"],
  "enabled": true
}
```

#### Implementation steps

1. Workers + agent per spec.
2. Browse page: filter sidebar, list view with status badges and effective dates.
3. Detail page: full markdown render + frontmatter sidebar + AssetChatPanel for scoped Q&A.
4. Apply-to-use-case modal: opens from regulation detail; takes use case description; calls AGENT-24 → returns applicability checklist.
5. Smoke test: filter EU + healthcare → EU AI Act + HIPAA equivalents appear; open EU AI Act → ask "summarize for executive" → useful answer; apply EU AI Act to "clinical imaging classifier" → applicability checklist.

#### Definition of done
- [ ] FRs 029-031 verified
- [ ] AssetChatPanel embedded on every regulation
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Live regulatory monitoring (post-demo Section 3.2)
- Email alerts on regulation changes (post-demo Section 3.2)
- Subscriber lists per regulation (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

- **2026-06-10 — Deployed + backend-smoked live; user UI smoke pending.** Commits
  `00388e0` (backend-core) + `a6f49d1` (UI) pushed. `cdk deploy AiCoE-Agents` (Workers +
  ModuleAgents + Orchestrator UPDATE_COMPLETE; AiCoE-Iam untouched) → synced modules.json
  → pushed. Live AGENT-24: `list` EU+healthcare → EU AI Act + GDPR; `get` reg-eu-ai-act →
  body + WORKER-12 summary; `apply` "clinical imaging classifier" → applies + Sonnet
  narrative + clause checklist. Remaining: user UI smoke (reg-badge deep-link lands on
  detail not 404; filter; Chat-with-this; Apply), then flip Status/INDEX ☑.
- **2026-06-10 — DONE ☑.** User UI smoke passed (reg-badge deep-link lands on the real
  detail page across Governance/Ethics → Compliance, plus filter / Chat-with-this / Apply).
  Status + INDEX flipped to ☑. FRs 029-031 verified live.
- **Orchestration follows the AGENT-05/20 precedent** (`vault/decisions/agent-05-orchestration.md`),
  not the spec's "Tools: …" Converse-tool-loop wording: WORKER-12 (reg_summarizer) and
  WORKER-13 (applicability_checker) are deterministic/extractive (no LLM, no AWS); AGENT-24
  dispatches `list`/`get`/`apply` mechanically and makes exactly ONE Sonnet call — the
  plain-language narrative on the `apply` path — with a deterministic fallback. No new
  decision file (reuses the precedent, like Task 09 did). Decided with the user.
- **Apply is ephemeral/inline** — no vault or sessions write, no get/list of past
  applications (matches the spec's three request models exactly). Decided with the user.
- **Detail-page Q&A reuses Task 07's `AssetChatPanelHook`/AGENT-25 verbatim** — the panel is
  content-agnostic, so the regulation's body+frontmatter ground the scoped chat (satisfies
  "AssetChatPanel embedded on every regulation").
- **Cross-links wired:** governance `RegulationRow` + checklist reg badges and ethics
  `FrameworkRow` now deep-link to `/modules/compliance-tracker/{reg_id}` (resolved by
  frontmatter id). The deferred `<span>`→`<Link>` work from Tasks 08/09 is done.
- **No IAM/infra change** — module-agents role already has vault Get/List + Sonnet
  (region-wildcarded) + Titan; workers role has vault ListBucket; WORKER-12/13 use no AWS.
- **Verified local:** ruff clean, 224 pytest pass (+23), vault valid (58 files),
  `cdk synth` exit 0, web `pnpm lint` + `build` clean.
- **Remaining:** deploy (`cdk deploy AiCoE-Agents` → re-sync `modules.json` → push) + user
  live smoke (FR-029/030/031). Then flip Status/INDEX to ☑.

## D. References
- Brief: FRs 029-031, AGENT-24, WORKER-12/13
- Design: Section 5.2 AGENT-24
- Foundation: `ai_docs/tasks/00_foundation.md`
- Reuses pattern from: `07_wave2_universal_asset_qa.md`
