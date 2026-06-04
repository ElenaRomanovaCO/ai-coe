# Task: Wave 6 — Knowledge Contribution (Module 5, AGENT-06)

> **Phase:** 6
> **Feature group:** Wave 6 (Client-Facing & People)
> **Covers:** FR-064 (submit form), FR-065 (curator approve), FR-066 (AI-assisted anonymization)
> **Builds:** AGENT-06 (Sonnet 4.6)
> **Depends on:** 00, 01, 02, 03 (Asset Library)
> **Blocks:** none
> **Estimated effort:** 2-3 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** User submits a new asset (case study, pattern, lesson learned) via structured form. AGENT-06 runs anonymization + tag suggestion + duplicate check. Goes into `pending/` for curator review. Curator approves → moves to live vault path.

**Build steps:**
1. AGENT-06 (Sonnet 4.6, 4 tools: submit_asset, run_anonymization, suggest_tags, approve_asset).
2. Flip Module 5 enabled.
3. `/modules/contribute` submission form + `/modules/contribute/pending` curator queue + `/modules/contribute/[id]` review page.

**Files to create/edit:**

- `agents/lambdas/modules/agent_06_contribute.py`
- `vault/modules.json` — flip Module 5
- `web/app/(authenticated)/modules/contribute/page.tsx`
- `web/app/(authenticated)/modules/contribute/pending/page.tsx`
- `web/app/(authenticated)/modules/contribute/[id]/page.tsx`
- `web/app/(authenticated)/modules/contribute/actions.ts`

**Done when:**
- [ ] FRs 064-066 verified
- [ ] Approval moves file from pending/ to live path
- [ ] Anonymization flags potential identifying details
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Knowledge Contribution (Module 5)** for the AI CoE Platform. Tasks 00-22 are done.

#### Agent spec (AGENT-06)

```python
class SubmitAssetRequest(BaseModel):
    display_name: str
    title: str
    type: str
    industry: str
    ai_stage: int
    body_markdown: str
    contributor_notes: str | None = None

class AnonymizationResponse(BaseModel):
    flagged_spans: list[FlaggedSpan]                # offset, span, suggested_replacement, reason
    suggested_anonymized_body: str

class TagSuggestionsResponse(BaseModel):
    tags: list[str]
    duplicates: list[AssetSummary]                  # existing assets with high similarity

class ApproveAssetRequest(BaseModel):
    pending_id: str
    final_frontmatter: dict
    final_body: str
    target_path: str
```

Tools: submit_asset (writes to `vault/pending/{pending_id}.md`), run_anonymization, suggest_tags, approve_asset (moves from pending/ to target path, triggers re-embed).

#### modules.json entry
```json
{
  "id": "module-5",
  "name": "Knowledge Contribution",
  "wave": 6,
  "purpose": "Submit new knowledge with AI-assisted anonymization and curator review.",
  "when_to_use": ["After an engagement closes", "Sharing a lesson learned", "Adding a new tool entry"],
  "example_queries": ["Submit a new case study", "What's in the pending queue?", "Anonymize this content"],
  "agent_id": "AGENT-06",
  "model_tier": "sonnet-4-6",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent + 4 tools.
2. Submission form: title, type, industry, stage, free markdown editor; on save submit → AGENT-06 runs anonymization + duplicate check inline, shows results inline.
3. Pending queue: list view with submitter, title, age, status.
4. Review page: side-by-side (anonymized body + flagged spans on left, frontmatter editor + tag suggestions on right) + Approve/Reject buttons. Approve calls `approve_asset` → file moves to live path → re-embed indexes it.
5. Smoke test: submit a sample case study with synthetic names → flags identifying details → anonymize → review → approve → file appears in Asset Library.

#### Definition of done
- [ ] FRs 064-066 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Multi-curator workflow with vote (post-demo)
- Auto-publishing with no review (post-demo per policy)
- Contributor reputation scoring (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 064-066, AGENT-06
- Foundation: `ai_docs/tasks/00_foundation.md`
