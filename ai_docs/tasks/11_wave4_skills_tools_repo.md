# Task: Wave 4 — Skills & Tools Repository (Module 7, AGENT-08)

> **Phase:** 4
> **Feature group:** Wave 4 (Specialized Tools)
> **Covers:** FR-032 (browse filtered), FR-033 (tool detail)
> **Builds:** AGENT-08 (Skills & Tools, Haiku 4.5)
> **Depends on:** 00, 01 (seeded tools), 02
> **Blocks:** none
> **Estimated effort:** 1-2 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** Browse tools by category, stack, AI stage, cost model; open detail with description, best-fit, ratings, limitations.

**Build steps:**

1. AGENT-08 (Haiku 4.5, 3 tools: list_tools, get_tool, recommend_tools_for_context).
2. Flip Module 7 enabled.
3. `/modules/tools-repo` browse + `/modules/tools-repo/[id]` detail with embedded AssetChatPanel.

**Files to create/edit:**

- `agents/lambdas/modules/agent_08_tools.py`
- `vault/modules.json` — flip Module 7
- `web/app/(authenticated)/modules/tools-repo/page.tsx`
- `web/app/(authenticated)/modules/tools-repo/[id]/page.tsx`
- `web/app/(authenticated)/modules/tools-repo/actions.ts`

**Done when:**
- [ ] FRs 032-033 verified
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Skills & Tools Repository (Module 7)**. Tasks 00-10 done. Seeded tools at `vault/tools/`.

#### Agent spec (AGENT-08)

Tools: list_tools (filters: category, stack, stage, cost), get_tool, recommend_tools_for_context (vector + filter).

#### modules.json entry
```json
{
  "id": "module-7",
  "name": "Skills & Tools Repository",
  "wave": 4,
  "purpose": "Curated directory of AI tools, frameworks, libraries with context.",
  "when_to_use": ["Picking a vector DB", "Choosing an agent framework", "Finding a tool for a specific stage"],
  "example_queries": ["Recommend a vector DB for low-volume RAG", "What orchestration framework should I use?", "Tools for healthcare AI projects"],
  "agent_id": "AGENT-08",
  "model_tier": "haiku-4-5",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent with 3 tools.
2. Reuse AssetCard pattern from Asset Library, adapt frontmatter fields.
3. Detail page reuses MarkdownRenderer + FrontmatterPanel + AssetChatPanel.
4. Smoke test: filter category=vector-db → returns Pinecone + S3 Vectors + pgvector; open S3 Vectors detail → chat panel works.

#### Definition of done
- [ ] FRs 032-033 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Tool ratings aggregation (uses Asset Library's metadata sidecar pattern)
- Tool comparison UI (Module 13 Vendor Eval covers this)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 032-033, AGENT-08
- Foundation: `ai_docs/tasks/00_foundation.md`
