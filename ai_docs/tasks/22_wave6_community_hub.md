# Task: Wave 6 — Community & Enablement Hub (Module 6, AGENT-07)

> **Phase:** 6
> **Feature group:** Wave 6 (Client-Facing & People)
> **Covers:** FR-061 (learning paths), FR-062 (office hours + threads), FR-063 (expert directory)
> **Builds:** AGENT-07 (Haiku 4.5)
> **Depends on:** 00, 01, 02
> **Blocks:** none
> **Estimated effort:** 2 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** A hub for learning paths (filter by role + stage), office hours signups, community threads, and an expert directory. All read-mostly with light write (post a thread, sign up for office hours).

**Build steps:**
1. AGENT-07 (Haiku 4.5, 4 tools: list_learning_paths, list_office_hours, list_threads, get_expert_directory).
2. Flip Module 6 enabled.
3. `/modules/community` hub home + sub-pages for learning, office hours, threads, experts.
4. Seed: 5 learning paths, 3 upcoming office hours, 5 demo personas in expert directory.

**Files to create/edit:**

- `agents/lambdas/modules/agent_07_community.py`
- `vault/modules.json` — flip Module 6
- `vault/community/learning-paths/*.md`
- `vault/community/office-hours/*.md`
- `vault/community/experts/*.md`
- `web/app/(authenticated)/modules/community/page.tsx`
- `web/app/(authenticated)/modules/community/learning/page.tsx`
- `web/app/(authenticated)/modules/community/office-hours/page.tsx`
- `web/app/(authenticated)/modules/community/experts/page.tsx`
- `web/app/(authenticated)/modules/community/actions.ts`

**Done when:**
- [ ] FRs 061-063 verified
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Community & Enablement Hub (Module 6)** for the AI CoE Platform. Tasks 00-21 are done.

#### Agent spec (AGENT-07)

Tools: list_learning_paths (filter role + stage), list_office_hours, list_threads (delegates to AGENT-09 Module 8 if needed), get_expert_directory.

#### modules.json entry
```json
{
  "id": "module-6",
  "name": "Community Hub",
  "wave": 6,
  "purpose": "Learning paths, office hours, community threads, expert directory.",
  "when_to_use": ["Find someone with expertise", "Pick a learning path", "Sign up for office hours"],
  "example_queries": ["Who knows healthcare AI?", "Learning paths for architects", "Next office hour?"],
  "agent_id": "AGENT-07",
  "model_tier": "haiku-4-5",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent + 4 tools.
2. Hub home: 4 cards linking to sub-pages.
3. Each sub-page: filter sidebar + list view.
4. Signups persist to user profile (`users/{name}.json`).
5. Smoke test: filter learning paths by role=architect → reduced list; sign up for office hours → confirmation visible.

#### Definition of done
- [ ] FRs 061-063 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Real calendar integration (post-demo)
- Real-time chat in threads (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 061-063, AGENT-07
- Foundation: `ai_docs/tasks/00_foundation.md`
