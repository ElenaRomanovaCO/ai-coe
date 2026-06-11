# Task: Wave 5 — Decision Log (Module 19, AGENT-18)

> **Phase:** 5
> **Feature group:** Wave 5 (Intelligence & Insight)
> **Covers:** FR-048 (log decision), FR-049 (search across decisions), FR-050 (related-decisions via vector similarity)
> **Builds:** AGENT-18 (Haiku 4.5)
> **Depends on:** 00, 01, 02
> **Blocks:** none
> **Estimated effort:** 1-2 days solo
> **Status:** ☑ Built + deployed as an **internal CoE tool** (2026-06-11). The whole app
> is password-gated (nothing public), so: backend AGENT-18 deployed (required to function);
> **visible in the app sidebar** (nav `enabled: true`) so the team can log decisions; but
> kept **out of the chat assistant's live module set** (`modules.json enabled: false`) so the
> Copilot doesn't surface it as a client-facing capability. Not gitignored — the `enabled`
> flag is the right off-switch; gitignore wouldn't control deploy and would cost history/CI.

---

## A. TL;DR Checklist

**Goal:** User logs decisions (decision, context, alternatives, rationale, outcome). Searchable across engagements; opening one shows similar past decisions via vector similarity.

**Build steps:**
1. AGENT-18 (Haiku 4.5, 3 tools: write_decision, search_decisions, get_similar).
2. Flip Module 19 enabled.
3. `/modules/decisions` browse + `/modules/decisions/new` form + `/modules/decisions/[id]` detail with Similar Decisions panel.

**Files to create/edit:**

- `agents/lambdas/modules/agent_18_decisions.py`
- `vault/modules.json` — flip Module 19
- `web/app/(authenticated)/modules/decisions/page.tsx`
- `web/app/(authenticated)/modules/decisions/new/page.tsx`
- `web/app/(authenticated)/modules/decisions/[id]/page.tsx`
- `web/app/(authenticated)/modules/decisions/actions.ts`

**Done when:**
- [ ] FRs 048-050 verified
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Decision Log (Module 19)** for the AI CoE Platform. Tasks 00-16 are done.

#### Agent spec (AGENT-18)

```python
class WriteDecisionRequest(BaseModel):
    display_name: str
    decision: str
    context: str
    alternatives: list[str]
    rationale: str
    outcome: str | None = None                      # filled later
    tags: list[str]
    engagement_id: str | None = None

class SearchDecisionsRequest(BaseModel):
    query: str
    tags: list[str] | None
    industry: str | None

class GetSimilarRequest(BaseModel):
    decision_id: str
    top_k: int = 5
```

Tools: write_decision (suggests tags via Haiku call), search_decisions, get_similar (vector similarity in S3 Vectors filtered by content_type=decision).

#### Decision storage
- `vault/decisions/{display_name}/{decision_id}.md` with frontmatter (decision_id, decision, context, alternatives, rationale, outcome, tags, engagement_id, created_at, updated_at)

#### modules.json entry
```json
{
  "id": "module-19",
  "name": "Decision Log",
  "wave": 5,
  "purpose": "Capture and search engagement decisions for continuity and onboarding.",
  "when_to_use": ["Log an architectural choice", "Find precedent for a similar decision", "Onboard a new consultant to past reasoning"],
  "example_queries": ["What decisions did we make about vector DBs in healthcare projects?", "Log this LLM provider choice", "Find similar decisions to this one"],
  "agent_id": "AGENT-18",
  "model_tier": "haiku-4-5",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent + 3 tools.
2. UI: list view (filter tags, industry), new-decision form with tag suggestions auto-filled by AGENT-18, detail view with rendered fields + Similar Decisions panel.
3. Smoke test: log 3 decisions in healthcare RAG space, open one, similar panel shows the other two.

#### Definition of done
- [ ] FRs 048-050 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Decision approval / sign-off workflow (post-demo)
- Decision graph visualization (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

- **2026-06-11: First consumer of the runtime-vault-writers convention.** Logged
  decisions are written to `vault/decisions/{display_name}/{id}.md` — the *same*
  top-level folder as the curated architecture-decision docs. `write_decision` tags
  each export `content_type: decision` + `generated: true` via the shared
  `export_frontmatter` helper, so chat's `search_knowledge_base` scopes user decisions
  out while curated docs keep surfacing (see `vault/decisions/runtime-vault-writers.md`).
- **2026-06-11: `get_similar` relies on the `generated` flag as its discriminator.**
  It embeds the source decision (Titan) and queries S3 Vectors, then keeps only hits
  with `content_type == "decisions"` (folder-derived) **AND** `generated` truthy,
  excluding the source itself — i.e. *other logged decisions*, never the curated
  arch-docs in the same folder. Mirrors AGENT-03's over-fetch + client-side filter.
- **2026-06-11: AGENT-18 is Haiku-tier; one LLM call.** Only `write_decision` calls the
  model (Haiku tag suggestion, merged with user tags), with a graceful fallback to the
  user's tags if it errors. `search` (keyword/tag/industry over logged decisions) and
  `get` are deterministic. No separate sessions state — the vault md (rich frontmatter
  + rendered body) is the record, read back by `get`/`search`. No workers, no IAM change.
- **2026-06-11: modules.json model_tier corrected to `haiku-4-5`** (was `sonnet-4-6`) to
  match the AGENT-18 spec; `enabled` + `ui_route: /modules/decisions`; nav routed.

**Verification (local):** `pytest agents/` 334 passed; `ruff` clean; `validate_vault.py`
OK (62 files); web `tsc`/`eslint` clean, `next build` succeeds with `/modules/decisions`,
`/new`, and `/[id]`. write (generated frontmatter + tag merge), search filters, get, and
`get_similar` scoping (logged-only, excludes self + curated + non-decision) covered by
`test_agent_18.py`.

## D. References
- Brief: FRs 048-050, AGENT-18
- Foundation: `ai_docs/tasks/00_foundation.md`
