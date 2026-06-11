# Task: Wave 4 — Q&A (Module 8, AGENT-09)

> **Phase:** 4
> **Feature group:** Wave 4 (Specialized Tools)
> **Covers:** FR-039 (post question), FR-040 (answers + upvote), FR-041 (AI-powered Q&A with citations)
> **Builds:** AGENT-09 (Sonnet 4.6)
> **Depends on:** 00, 01, 02
> **Blocks:** none
> **Estimated effort:** 2 days solo
> **Status:** ☑ Done — deployed + live-verified (backend + UI smoke) 2026-06-10

---

## A. TL;DR Checklist

**Goal:** Two modes:
- **Community mode**: post a question, get answers from peers, upvote
- **AI mode**: ask a natural language question, get synthesized answer from across the Knowledge Base with citations

**Build steps:**
1. AGENT-09 (Sonnet 4.6, 4 tools: list_threads, get_thread, answer_with_citations, post_thread).
2. Flip Module 8 enabled.
3. `/modules/qa` browse + `/modules/qa/[id]` thread view + `/modules/qa/ask` AI-mode page.

**Files to create/edit:**

- `agents/lambdas/modules/agent_09_qa.py`
- `vault/modules.json` — flip Module 8
- `web/app/(authenticated)/modules/qa/page.tsx`
- `web/app/(authenticated)/modules/qa/[id]/page.tsx`
- `web/app/(authenticated)/modules/qa/ask/page.tsx`
- `web/app/(authenticated)/modules/qa/actions.ts`

**Done when:**
- [ ] FRs 039-041 verified
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Q&A (Module 8)** for the AI CoE Platform. Tasks 00-13 are done.

#### Agent spec (AGENT-09)

```python
class AnswerWithCitationsRequest(BaseModel):
    question: str
    context_filters: dict | None = None             # e.g. industry, stage

class AnswerWithCitationsResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: Literal["high", "medium", "low"]
    related_threads: list[ThreadSummary]
```

Tools: list_threads, get_thread, post_thread (writes a new thread .md), answer_with_citations.

#### Thread storage
- `vault/qa/{yyyy-mm}/{thread_id}.md` with frontmatter (question, tags, posted_by, posted_at, answers)
- Answers stored as a list inside the same .md (one .md per thread; simpler than separate files)
- Upvotes tracked in sidecar `vault/qa/_metadata/{thread_id}.json`

#### modules.json entry
```json
{
  "id": "module-8",
  "name": "Q&A",
  "wave": 4,
  "purpose": "Async community Q&A plus AI-powered synthesis from across the Knowledge Base.",
  "when_to_use": ["Stuck on something", "Want a synthesized answer with citations", "Sharing institutional knowledge"],
  "example_queries": ["How do I size a Bedrock provisioned throughput?", "What is the right vector DB for a 100k document RAG?", "Find Q&A about HIPAA AI"],
  "agent_id": "AGENT-09",
  "model_tier": "sonnet-4-6",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps

1. Agent + 4 tools.
2. Browse: tags + search + sort (recent / most upvoted / unanswered).
3. Thread page: question + answer list with upvote buttons + answer-this textarea.
4. AI ask page: input box + "Ask" → AGENT-09 streams answer with citations + "Save as community thread" option.
5. Smoke test: ask "What is the EU AI Act risk tier for healthcare imaging classifiers?" → answer cites the seeded EU AI Act + HIPAA entries; save to thread; thread visible in browse.

#### Definition of done
- [ ] FRs 039-041 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Notifications when a question is answered (post-demo)
- Reputation / badges (post-demo / Module 20 territory)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

- **2026-06-10 — Deployed + backend-smoked live; user UI smoke pending.** Commits pushed
  (`2655300..7b280ee`). `cdk deploy AiCoE-Agents` (ModuleAgents +AGENT-09; AiCoE-Iam untouched)
  → synced modules.json + `vault/qa/` seeds → backend smoke → pushed. Live AGENT-09: list → 3
  seed threads; answer_with_citations "EU AI Act risk tier for healthcare imaging?" →
  confidence high, real Sonnet answer ("High-Risk"), cites reg-eu-ai-act + FDA + governance
  reviews; post_thread → wrote new thread; answer_thread → count 1; upvote → 1/voted. (Smoke
  left a benign "How should we chunk long PDFs for RAG?" thread live.)
- **2026-06-10 — DONE ☑.** Amplify build green; user smoked the live Q&A (browse → upvote +
  answer; Ask AI → cited answer + confidence → save-as-thread). Also added starter-question
  chips to both the Ask AI page and the browse landing (commits 7895e14 + 065b0c0, frontend-only)
  on user request. Status + INDEX flipped ☑. FRs 039-041 verified live. **Wave 4 complete
  (8, 11, 12, 13 all LIVE); all 14 tasks done.**
- **New `qa` content type:** `QaThreadFrontmatter`/`QaAnswer` schema added to
  `agents/lib/schemas` + `qa` folder map; **3 seed threads** under `vault/qa/2026-05/`
  (decided w/ user). Threads write to vault → re-embedded → citable in AI mode.
- **AGENT-09** (Sonnet): community = `list_threads` (sort recent/upvotes/unanswered) /
  `get_thread` / `post_thread` + `answer_thread` (write `vault/qa/{yyyy-mm}/{id}.md` via
  `yaml.safe_dump` + rendered body) / `upvote` (answer-level, idempotent — one per user per
  answer via vault `qa/_metadata/{id}.json` sidecar + sessions `qa-votes/{slug}.json`). AI =
  `answer_with_citations` (Titan→S3 Vectors RAG over ALL content types + ONE Sonnet synth;
  citations deep-link by content type via `_ROUTE_BY_TYPE`; deterministic confidence
  high/medium/low; related `qa` threads; deterministic fallback to top sources).
- **Non-streaming** AI answer (established precedent; reframes DoD "streams"). **No new IAM**
  (module role already has vault Get/List/Put, sessions Put, s3vectors Query/Get, Titan +
  Sonnet — AGENT-05/02 already write to vault).
- **Web:** `/modules/qa` browse (QaBrowser: search/sort/tag + inline compose + Ask-AI link) +
  `[id]` thread (AnswerList: idempotent upvotes + answer-this) + `/ask` AI mode (AiAsk:
  answer + citation deep-links + confidence + related threads + Save-as-community-thread).
  React-19-safe.
- **Verified local:** ruff clean, 275 pytest (+14), vault valid (61 files), `cdk synth`
  exit 0, web `pnpm lint` + `build` clean (3 qa routes).
- **Remaining:** deploy (`cdk deploy AiCoE-Agents` → **sync modules.json AND vault/qa/ to the
  vault bucket** → push) + user live smoke (FR-039/040/041). Then flip Status/INDEX ☑.

## D. References
- Brief: FRs 039-041, AGENT-09
- Foundation: `ai_docs/tasks/00_foundation.md`
