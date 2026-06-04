# Task: Wave 4 — Prompt Engineering Studio (Module 11, AGENT-11)

> **Phase:** 4
> **Feature group:** Wave 4 (Specialized Tools)
> **Covers:** FR-036 (create/fork/version/run), FR-037 (live test), FR-038 (side-by-side diff)
> **Builds:** AGENT-11 (Sonnet 4.6)
> **Depends on:** 00, 01, 02
> **Blocks:** none
> **Estimated effort:** 3-4 days solo (most complex UI in Wave 4)
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** A consultant can author prompts, fork existing ones, version them, run live against Bedrock models, and compare versions side-by-side with diff.

**Build steps:**
1. AGENT-11 (Sonnet 4.6, 4 tools: list_prompts, get_prompt, run_prompt, suggest_improvements).
2. Flip Module 11 enabled.
3. Studio UI: list view, edit view with model selector + variables + run button, version history, diff view.
4. Prompt storage: each prompt is a .md file with frontmatter (version, parent_id) under `vault/prompts/`.

**Files to create/edit:**

- `agents/lambdas/modules/agent_11_prompts.py`
- `vault/modules.json` — flip Module 11
- `web/app/(authenticated)/modules/prompt-studio/page.tsx`
- `web/app/(authenticated)/modules/prompt-studio/[id]/page.tsx` — editor
- `web/app/(authenticated)/modules/prompt-studio/[id]/diff/[other]/page.tsx`
- `web/components/PromptEditor.tsx`
- `web/components/PromptRunner.tsx`
- `web/components/PromptDiff.tsx`
- `web/app/(authenticated)/modules/prompt-studio/actions.ts`

**Done when:**
- [ ] FRs 036-038 verified
- [ ] Versions tracked correctly
- [ ] Live run streams response
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Prompt Engineering Studio (Module 11)** for the AI CoE Platform. Tasks 00-12 are done.

#### Agent spec (AGENT-11)

```python
class RunPromptRequest(BaseModel):
    prompt_text: str
    variables: dict[str, str]
    model_id: str
    max_tokens: int = 1000
    temperature: float = 0.7

class RunPromptResponse(BaseModel):
    output: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_ms: int
```

Tools: list_prompts, get_prompt, run_prompt (calls Bedrock directly via shared bedrock_client), suggest_improvements (analyzes prompt, returns suggestions + anti-pattern flags).

#### Prompt storage layout
- `vault/prompts/{prompt_id}.md` with frontmatter: id, title, use_case, model_targets, variables, version, parent_id, created_by, created_at
- Versions: new version creates new file with incremented version + parent_id link
- Forks: new file with new id, parent_id = source, version reset to 1

#### modules.json entry
```json
{
  "id": "module-11",
  "name": "Prompt Engineering Studio",
  "wave": 4,
  "purpose": "Author, version, test, and compare prompts collaboratively.",
  "when_to_use": ["Building new prompts for a use case", "Iterating on an existing prompt", "Comparing two prompt versions"],
  "example_queries": ["Find prompts for client briefing", "Improve this prompt", "Compare these two prompt versions"],
  "agent_id": "AGENT-11",
  "model_tier": "sonnet-4-6",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps

1. Agent + 4 tools.
2. Studio list page: search + filter by use case, model target.
3. Editor page: split view (editor on left, runner on right), variable substitution, model selector (Sonnet 4.6 / Haiku 4.5 / Opus 4.7 — Opus subject to daily cap), Save = creates new version.
4. Diff page: side-by-side text diff (use diff-match-patch or similar) + side-by-side last-known outputs if both have been run.
5. Suggest improvements button: calls AGENT-11 with current prompt; returns suggestions + anti-pattern list.
6. Smoke test: load a seed prompt, edit it, save as v2, run against Haiku, compare v1 vs v2 → diff visible.

#### Definition of done
- [ ] FRs 036-038 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Eval harness with auto-grading (post-demo)
- External prompt sharing (post-demo)
- A/B testing with traffic split (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 036-038, AGENT-11
- Foundation: `ai_docs/tasks/00_foundation.md`
