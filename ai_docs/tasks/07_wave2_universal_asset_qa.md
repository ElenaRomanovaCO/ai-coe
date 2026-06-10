# Task: Wave 2 — Universal Asset Q&A (Module 26, AGENT-25)

> **Phase:** 2
> **Feature group:** Wave 2 (Assessment & Delivery)
> **Covers:** FR-023 (chat-with-this button), FR-024 (summarize, compare, translate)
> **Builds:** AGENT-25 (Universal Asset Q&A, Sonnet 4.6)
> **Depends on:** 00, 01, 02, 03
> **Blocks:** none (other modules can opt into the chat panel pattern)
> **Estimated effort:** 2 days solo
> **Status:** ☑ Done — deployed + smoke-passed 2026-06-10

---

## A. TL;DR Checklist

**Goal:** Every asset detail page shows a "Chat with this" button that opens a side panel scoped to that asset. User can ask for summaries, comparisons, translations to checklists, role-specific framings.

**Build steps:**

1. AGENT-25 in ModuleAgentsLambda (Sonnet 4.6, 3 tools: read_asset, search_vector_index_scoped, summarize_for_role).
2. Flip Module 26 enabled in modules.json.
3. AssetChatPanel component (side panel with chat UI, asset content baked into system prompt).
4. Wire into Asset Library detail page; expose pattern so later modules (Compliance, Intelligence Feed, Vendor Eval) can reuse the panel.
5. Smoke test: open an asset, click Chat with this, ask 4 things (summary, exec briefing, regulation checklist, comparison with another asset) — all return relevant grounded answers.

**Files to create/edit:**

- `agents/lambdas/modules/agent_25_asset_qa.py`
- `vault/modules.json` — flip Module 26
- `web/components/AssetChatPanel.tsx`
- `web/components/AssetChatPanelHook.tsx` — to embed in any detail page
- `web/app/(authenticated)/modules/asset-library/[id]/page.tsx` — embed panel
- `web/app/actions/asset_qa.ts`

**Done when:**

- [ ] FRs 023-024 verified
- [ ] Panel works on every asset type that has a detail page
- [ ] Conversations scoped to the asset (does not pull random other content)
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Universal Asset Q&A (Module 26, AGENT-25)** for the AI CoE Platform. Tasks 00-06 are done.

#### Project context

- This module reuses the chat UI pattern but scoped to a single asset. The agent's system prompt includes the asset content as context.
- Later modules (Compliance Tracker Wave 3, Vendor Eval Wave 4, Intelligence Feed Wave 5) will embed the same panel.

#### Agent spec (AGENT-25)

```python
class AssetChatRequest(BaseModel):
    asset_id: str
    asset_content: str                              # full markdown body
    asset_frontmatter: dict
    session_id: str
    message: str

class AssetChatResponse(BaseModel):
    assistant_message: str
    citations: list[Citation]                       # may include other assets if user asks to compare
    suggestions: list[str]                          # quick-prompt suggestions for follow-ups
```

Tools (3):
- `read_asset(asset_id)` (used when user asks to compare to another asset)
- `search_vector_index_scoped(query, top_k, exclude_asset_id)` (cross-asset search)
- `summarize_for_role(asset_content, role)` (specialized summarization tool with role-specific framings)

System prompt outline: you are answering questions about ONE specific asset. The full asset content is in context. Answer questions based on it. If user asks for comparison with other assets, retrieve them. Cite sections by heading. Refuse to answer questions unrelated to the asset.

#### modules.json entry
```json
{
  "id": "module-26",
  "name": "Universal Asset Q&A",
  "wave": 2,
  "purpose": "Chat with any single asset or document, scoped to its content.",
  "when_to_use": ["Summarize an asset for a client", "Translate a regulation to a checklist", "Compare two reference architectures"],
  "example_queries": ["Summarize this for an executive", "What compliance considerations does this trigger?", "Compare to the retail pattern"],
  "agent_id": "AGENT-25",
  "model_tier": "sonnet-4-6",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps

1. Agent + 3 tools per spec.
2. AssetChatPanel: shadcn Sheet on the right side; opens via "Chat with this" button.
3. Quick-prompt suggestions: predefined ("Summarize for executive", "Risk checklist", "Compare to similar assets", "Action items").
4. Embed pattern: any detail page can drop `<AssetChatPanelHook assetId={id} />` to wire the panel.
5. Smoke test: 4 prompts on a healthcare clinical-notes asset, plus comparison query.

#### Definition of done
- [ ] FRs 023-024 verified
- [ ] Pattern reusable on any future detail page
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Saving asset chats to vault (optional later)
- Cross-asset bulk synthesis (Chat already handles this via search_knowledge_base)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

- 2026-06-10: Asset Q&A panel transport = non-streaming server action — the panel calls AGENT-25 via `web/app/actions/asset_qa.ts` → `invokeModule`, not the dock's SSE route (AGENT-25 returns one-shot). See `vault/decisions/asset-panel-transport.md`.
- 2026-06-10: Asset-panel module agents run without a Bedrock guardrail — AGENT-25 refuses off-asset/unsafe requests by system-prompt only (module-agents role lacks `bedrock:ApplyGuardrail`); every later panel inherits this posture. See `vault/decisions/asset-panel-no-guardrail.md`.

## D. References
- Brief: FRs 023-024, AGENT-25
- Design: Section 5.2 AGENT-25
- Foundation: `ai_docs/tasks/00_foundation.md`
