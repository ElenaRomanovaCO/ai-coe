# Task: Wave 6 — Knowledge Contribution (Module 5, AGENT-06)

> **Phase:** 6
> **Feature group:** Wave 6 (Client-Facing & People)
> **Covers:** FR-064 (submit form), FR-065 (curator approve), FR-066 (AI-assisted anonymization)
> **Builds:** AGENT-06 (Sonnet 4.6)
> **Depends on:** 00, 01, 02, 03 (Asset Library)
> **Blocks:** none
> **Estimated effort:** 2-3 days solo
> **Status:** ◐ CODE-COMPLETE 2026-06-12 — backend + UI built, tests/lint/synth/build green,
> NOT deployed (deploy + user live smoke pending). See Notes & Decisions Log.

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

**2026-06-12 — Build (backend-core + UI), code-complete, NOT deployed.**

- **AGENT-06 ContributeAgent** (`agent_06_contribute.py`, Sonnet): ops `submit_asset` (persist +
  inline analysis), `run_anonymization`, `suggest_tags`, `list_pending`, `get_pending`, `approve_asset`,
  `reject_asset`. **One Sonnet call** (`_analyze`) does anonymization (flagged spans + anonymized body) AND
  tag suggestion together; **duplicate check composes AGENT-03's vector search** (Titan→S3 Vectors); offsets
  computed server-side via `body.find(span)`. Deterministic no-op fallback if Sonnet fails.
- **KEY DECISION — pending submissions live in the SESSIONS bucket** (`contributions/{id}.json`), NOT the
  spec's `vault/pending/`. Un-reviewed, un-anonymized content must never reach the vault, where ReEmbed would
  index it into the searchable KB before curation — applies the `curated-content-in-vault` principle (only
  reviewed content enters the vault). `approve_asset` writes the final markdown to
  `vault/assets/{industry}/{ai_stage}/{slug}.md` (valid `AssetFrontmatter` via `yaml.safe_dump`) → ReEmbed
  indexes it → it appears in the Asset Library; the pending record is marked `review_status: approved` (no S3
  delete). **Consequence: NO new IAM** — the module-agents role already has vault+sessions Get/Put + Sonnet +
  Titan + s3vectors (delete was the only thing a vault/pending move would have needed, and it's avoided).
- **Naming fix:** the record's lifecycle field is `review_status` (pending/approved/rejected), not `status`,
  to avoid colliding with the `{"status": "ok"}` response envelope when the record is spread.
- `target_path` guarded to `assets/` (rejects path traversal / writes outside the library).
- Registered AGENT-06 in router; module-5 `enabled:true` + `ui_route:/modules/contribute`.
- Web: `/modules/contribute` (submission form → inline anonymization flags + duplicates + suggested tags) +
  `/modules/contribute/pending` (curator queue) + `/modules/contribute/[id]` (`ContributeReview`: editable
  anonymized body + flagged spans on the left; frontmatter editor + tag chips + duplicates + Approve/Reject on
  the right; approved → links to the new Asset Library page); `actions.ts`, `lib/contribute.ts`; nav module-5 live.
- Gates: 445 pytest (9 new `tests/test_agent_06.py`), ruff clean, synth exit 0, vault valid (107), web lint +
  build clean (3 contribute routes).

**REMAINING:** deploy (`cdk deploy AiCoE-Agents` → re-sync modules.json → push) + user live smoke (FR-064
submit a case study w/ synthetic names → flags; FR-066 anonymize + tag + duplicate; FR-065 approve → asset
appears in Asset Library). Then flip INDEX/header ☑.

## D. References
- Brief: FRs 064-066, AGENT-06
- Foundation: `ai_docs/tasks/00_foundation.md`
