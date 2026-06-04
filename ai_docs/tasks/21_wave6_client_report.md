# Task: Wave 6 — Client-Facing Maturity Report Portal (Module 14, AGENT-14 + WORKER-06/07)

> **Phase:** 6
> **Feature group:** Wave 6 (Client-Facing & People)
> **Covers:** FR-058 (auto-generate), FR-059 (edit narrative), FR-060 (PDF export)
> **Builds:** AGENT-14 (Sonnet 4.6), WORKER-06 narrative_writer, WORKER-07 benchmark_lookup
> **Depends on:** 00, 01, 02, 05 (assessment), 20 (benchmark)
> **Blocks:** none
> **Estimated effort:** 3 days solo
> **Status:** ☐ Not started

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
## D. References
- Brief: FRs 058-060, AGENT-14, WORKER-06/07
- Foundation: `ai_docs/tasks/00_foundation.md`
- Post-demo: `ai_docs/post-demo-plan.md` Section 2
