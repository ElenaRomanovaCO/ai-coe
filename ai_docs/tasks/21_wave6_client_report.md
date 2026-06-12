# Task: Wave 6 — Client-Facing Maturity Report Portal (Module 14, AGENT-14 + WORKER-06/07)

> **Phase:** 6
> **Feature group:** Wave 6 (Client-Facing & People)
> **Covers:** FR-058 (auto-generate), FR-059 (edit narrative), FR-060 (PDF export)
> **Builds:** AGENT-14 (Sonnet 4.6), WORKER-06 narrative_writer, WORKER-07 benchmark_lookup
> **Depends on:** 00, 01, 02, 05 (assessment), 20 (benchmark)
> **Blocks:** none
> **Estimated effort:** 3 days solo
> **Status:** ◐ CODE-COMPLETE 2026-06-12 — backend + UI built, tests/lint/synth/build green,
> NOT deployed (deploy + user live smoke pending). See Notes & Decisions Log.

---

## A. TL;DR Checklist

**Goal:** From a completed assessment, generate a polished formatted client report (score, stage, benchmark, recommendations, top 3-5 next steps, high-level use cases). User can edit narrative sections, then export as PDF for sharing (no signed-URL public portal in demo per Q2 decision).

**Build steps:**
1. WORKER-06 narrative_writer (assessment + benchmark → polished narrative sections).
2. WORKER-07 benchmark_lookup (pulls Module 22 peer distribution).
3. AGENT-14 (Sonnet 4.6, 4 tools).
4. Flip Module 14 enabled.
5. `/modules/reports/[assessment_id]` editor + preview + PDF export.

**Files to create/edit:**

- `agents/lambdas/workers/worker_06_narrative_writer.py`
- `agents/lambdas/workers/worker_07_benchmark_lookup.py`
- `agents/lambdas/modules/agent_14_report.py`
- `vault/modules.json` — flip Module 14
- `web/app/(authenticated)/modules/reports/page.tsx`
- `web/app/(authenticated)/modules/reports/[assessment_id]/page.tsx`
- `web/app/(authenticated)/modules/reports/[assessment_id]/actions.ts`
- `web/components/ReportPreview.tsx`
- `web/lib/pdf.ts` — PDF rendering helper (use @react-pdf/renderer or playwright-print via Lambda)

**Done when:**
- [ ] FRs 058-060 verified
- [ ] PDF downloads cleanly
- [ ] Edits persist
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Client-Facing Maturity Report Portal (Module 14)** for the AI CoE Platform. Tasks 00-20 are done.

Per Q2 decision in brief: PDF download only in demo; signed-URL public portal moves to post-demo Section 2.1.

#### Worker specs

- **WORKER-06 narrative_writer**: takes assessment + benchmark → writes polished narrative sections (Executive Summary, Stage Placement, What This Means, Top Next Steps, Recommended Use Cases).
- **WORKER-07 benchmark_lookup**: invokes Module 22's `get_peer_distribution` (via AGENT-21) or reads its output cache.

#### Agent spec (AGENT-14)

```python
class GenerateReportRequest(BaseModel):
    assessment_id: str
    client_context: str | None = None               # branding hints

class ReportSections(BaseModel):
    executive_summary: str
    stage_placement: str
    what_this_means: str
    top_next_steps: list[str]
    recommended_use_cases: list[str]
    benchmark_paragraph: str

class GeneratedReport(BaseModel):
    report_id: str
    assessment_id: str
    sections: ReportSections
    metadata: dict
    vault_file_path: str

class ExportPdfRequest(BaseModel):
    report_id: str

class ExportPdfResponse(BaseModel):
    download_url: str                               # presigned, 1h TTL
```

Tools: invoke_worker (WORKER-06), invoke_worker (WORKER-07), update_section, export_pdf.

#### modules.json entry
```json
{
  "id": "module-14",
  "name": "Client Maturity Report Portal",
  "wave": 6,
  "purpose": "Generate polished client-facing maturity reports from an assessment.",
  "when_to_use": ["Preparing a client readout", "Sharing assessment findings"],
  "example_queries": ["Generate a report from this assessment", "Edit the executive summary"],
  "agent_id": "AGENT-14",
  "model_tier": "sonnet-4-6",
  "worker_ids": ["WORKER-06", "WORKER-07"],
  "enabled": true
}
```

#### Implementation steps
1. Workers + agent per spec.
2. Editor UI: split (rendered preview on right, editable sections on left). Use a controlled rich text editor (e.g. TipTap or plain markdown textarea) per section.
3. PDF export options:
   - Option A: @react-pdf/renderer in Next.js server action → returns PDF buffer
   - Option B: Headless chromium in Lambda → screenshot the rendered HTML report
   - Default for demo: @react-pdf/renderer (simpler, no chromium overhead)
4. Save edits to vault/reports/{display_name}/{report_id}.md.
5. Smoke test: from a healthcare stage-2 assessment, generate report → 6 sections render → edit executive summary → preview updates → export PDF → file readable.

#### Definition of done
- [ ] FRs 058-060 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Public signed-URL portal (post-demo-plan.md Section 2.1)
- Branded templates (post-demo Section 2.2)
- View analytics on opened links (post-demo Section 2.1)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

**2026-06-12 — Build (backend-core + UI), code-complete, NOT deployed.** Three deviations from
the written spec, each chosen by the user before coding:

1. **No workers — AGENT-14 is inline (skeleton + one Sonnet call).** The spec listed WORKER-06
   (narrative_writer) + WORKER-07 (benchmark_lookup), but the locked worker-pattern keeps workers
   deterministic/no-LLM and the newest document-generator (AGENT-29 SOW) folded prose into the
   agent's single Sonnet call. AGENT-14 reads the assessment, **composes AGENT-21 BenchmarkAgent
   in-process** for the peer distribution (AGENT-16→AGENT-03 composition precedent — no worker, no
   cross-Lambda hop), builds a deterministic 6-section skeleton, and makes ONE Sonnet call for the
   narrative prose, with a deterministic fallback. Applies `vault/decisions/agent-05-orchestration.md`;
   no new decision file.
2. **PDF export rendered client-side via `@react-pdf/renderer`** (FR-060) — `web/lib/reportPdf.tsx`,
   dynamically imported on click so the lib stays out of the SSR/main bundle. This is the platform's
   **first real PDF export** (SOW/Kit Builder only did presigned markdown). The PDF renders the
   structured sections, not the markdown, so layout is controlled independently of the preview.
   *Candidate for a formal `vault/decisions/` entry (`client-report-pdf-export`) since later
   export-bearing modules may reuse it — run `/log-decision` to formalize.*
3. **Reports persist to the SESSIONS bucket** (`reports/{display_name}/{report_id}.md` + `.json`),
   not `vault/reports/` as the spec said — client-specific deliverables must not enter the searchable
   KB (AGENT-29 storage precedent). `update_section` rewrites both objects (FR-059 persistence).

**What was built:**
- Backend: `agents/lambdas/modules/agent_14_report.py` (ops generate/get/list/update_section),
  registered in `modules/router.py` REGISTRY as AGENT-14; `vault/modules.json` module-14
  `enabled: true` + `ui_route: /modules/reports`, `worker_ids: []`. 11 tests in
  `tests/test_agent_14.py` (compose real AGENT-21 over a seeded assessment + benchmark seed).
- Web: `/modules/reports` landing (generate-from-completed-assessment + past-reports lists),
  `/modules/reports/[report_id]` editor (split: per-section edit + Save → `update_section`, live
  preview, **Export PDF**), `web/lib/reports.ts` + `web/lib/reportPdf.tsx`, `actions.ts`,
  `components/reports/{ReportEditor,GenerateReportButton}.tsx`. Wired the assessment result page's
  "Generate client report" button (was disabled) → `GenerateReportButton`. Flipped nav module-14 live.
  Added `@react-pdf/renderer@4.5.1` (pnpm lockfile updated).
- **No new IAM/infra** — module-agents role already has sessions Get/Put/List + vault Get/List +
  Sonnet (region-wildcarded). Deploy only rebuilds the module image.
- Gates green: 420 pytest, ruff clean (agents), `python app.py` synth exit 0, vault valid (79),
  web pnpm lint + build clean (both report routes compiled).

**REMAINING:** deploy (`cdk deploy AiCoE-Agents` → re-sync modules.json to vault bucket → push;
Amplify auto-builds report pages) + user live smoke (FR-058 generate from a stage-2 healthcare
assessment → 6 sections; FR-059 edit a section → preview updates + persists across reload; FR-060
Export PDF → file opens cleanly). Then flip INDEX/task header ☑.

## D. References
- Brief: FRs 058-060, AGENT-14, WORKER-06/07
- Foundation: `ai_docs/tasks/00_foundation.md`
- Post-demo: `ai_docs/post-demo-plan.md` Section 2
