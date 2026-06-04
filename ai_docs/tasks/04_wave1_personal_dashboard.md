# Task: Wave 1 — Personal Dashboard (Module 17, AGENT-16)

> **Phase:** 1
> **Feature group:** Wave 1 (Foundation)
> **Covers:** FR-014 (saved + recent + active engagements), FR-015 (recommendations)
> **Builds:** AGENT-16 (Personal Dashboard, Haiku 4.5)
> **Depends on:** 00_foundation, 01_wave1_vault_seed_content, 02_wave1_chat_orchestrator, 03_wave1_asset_library
> **Blocks:** none (other modules add cards to dashboard but dashboard works standalone)
> **Estimated effort:** 2 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** After login the user lands on `/dashboard` and sees saved assets, recent Chat conversations, active engagements (placeholder until module 18), learning progress (placeholder until module 20), recommendations based on activity, and a one-click resume for the last conversation.

**Build steps:**

1. **AGENT-16 in ModuleAgentsLambda** (Haiku 4.5, 3 tools: read_profile, recommend, list_recent) → Verify: unit tests.
2. **Register Module 17 enabled=true in modules.json** → Verify: Chat's list_modules shows it.
3. **Build `/dashboard` page** with 6 cards (Saved Assets, Recent Chats, Active Engagements, Learning Progress, Recommendations, Quick Actions) → Verify: all cards render with seeded sample data.
4. **Resume Last Chat button** → Verify: clicking opens last session in dock.
5. **Recommendations engine** (vector similarity over saved/visited assets, fed to AGENT-16) → Verify: after saving 3 healthcare assets, recommendations skew healthcare.

**Files to create/edit:**

- `agents/lambdas/modules/agent_16_dashboard.py`
- `agents/lambdas/modules/router.py` — register
- `vault/modules.json` — flip Module 17
- `web/app/(authenticated)/dashboard/page.tsx` — replace placeholder from task 00
- `web/components/dashboard/SavedAssetsCard.tsx`
- `web/components/dashboard/RecentChatsCard.tsx`
- `web/components/dashboard/ActiveEngagementsCard.tsx`
- `web/components/dashboard/LearningProgressCard.tsx`
- `web/components/dashboard/RecommendationsCard.tsx`
- `web/components/dashboard/QuickActionsCard.tsx`
- `web/app/(authenticated)/dashboard/actions.ts`

**Done when:**

- [ ] FR-014, FR-015 verified
- [ ] All 6 cards render
- [ ] Resume Last Chat works
- [ ] Recommendations shift based on activity
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Personal Dashboard (Module 17, AGENT-16)** for the AI CoE Platform. Tasks 00-03 are done.

#### Project context

- Dashboard is the landing page after login. It is read-only, populated by activity from other modules.
- Some cards depend on modules not yet built (Active Engagements → Module 18 Wave 5; Learning Progress → Module 20 Wave 6). For Wave 1, those cards show seeded sample data and a "Coming soon" tooltip.

#### Agent specification (AGENT-16)

```python
class DashboardSummaryRequest(BaseModel):
    display_name: str

class DashboardSummary(BaseModel):
    saved_assets: list[AssetSummary]              # last 10
    recent_chats: list[ChatSession]               # last 5 with first-user-message snippet
    active_engagements: list[EngagementStub]      # placeholder list, empty until Module 18
    learning_progress: list[LearningPathStub]     # placeholder list, empty until Module 20
    recommendations: list[AssetSummary]           # top 5 from AGENT-16's recommender
    last_session_id: str | None
```

Tools (3):
- `read_profile(display_name)` → UserProfile (from `users/{name}.json`)
- `recommend(display_name, top_k)` → list[AssetSummary] (vector similarity from recent activity)
- `list_recent_chats(display_name, limit)` → list[ChatSession] (S3 list under `sessions/{name}/`)

Recommender logic (in `recommend`):
1. Read user profile, gather last 10 saved + last 10 viewed asset IDs
2. For each, get its embedding from S3 Vectors (or recompute centroid from chunks)
3. Average the embeddings → query vector
4. Query S3 Vectors with `content_type=asset`, exclude already-saved, top_k

#### UI specification

- **`/dashboard`**:
  - Hero: "Hi, {display_name}" + Resume Last Chat button (large)
  - Grid: 6 cards (responsive 2×3 on desktop, stacked on mobile)
  - Each card: title, content, "See all" link if applicable
- **SavedAssetsCard**: list 5 saved with title + type, "See all" → filtered Asset Library
- **RecentChatsCard**: list 5 with first user-message snippet, "Resume" buttons
- **ActiveEngagementsCard**: empty state in Wave 1 ("No active engagements. Start one when Module 18 is enabled.")
- **LearningProgressCard**: empty state in Wave 1
- **RecommendationsCard**: 5 asset cards from AGENT-16
- **QuickActionsCard**: buttons "Run Assessment" (disabled until Module 1), "Build Kit" (disabled until Module 3), "Browse Assets" (enabled → Asset Library)

#### IAM deltas
No changes from task 03.

#### modules.json entry
```json
{
  "id": "module-17",
  "name": "Personal Dashboard",
  "wave": 1,
  "purpose": "Personalized home view of saved items, recent activity, recommendations.",
  "when_to_use": ["Resume work", "See what is new and relevant", "One-click access to common actions"],
  "example_queries": ["What did I work on yesterday?", "Recommend assets for me"],
  "agent_id": "AGENT-16",
  "model_tier": "haiku-4-5",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps

1. AGENT-16 with 3 tools per spec.
2. Recommender uses centroid-of-embeddings approach; if user has no activity, return random sample of 5 highly-tagged assets.
3. `/dashboard/page.tsx` (Server Component) calls `get_dashboard_summary_action` once, passes to cards.
4. Each card is a Server Component for first paint, with optional client-side refresh.
5. Resume Last Chat: route is `/dashboard?session={id}` → ChatDock opens with that session loaded.
6. Smoke test:
   - Fresh login → dashboard renders, cards show seeded sample
   - Save 3 assets in Asset Library → return to dashboard → SavedAssetsCard updates, RecommendationsCard adjusts
   - Click Resume Last Chat → dock opens with prior history

#### Definition of done

- [ ] FR-014 + FR-015 verified
- [ ] All 6 cards render
- [ ] Recommendations engine returns sensible items after seeding activity
- [ ] DoD from 00_foundation.md passed

#### Behavioral guardrails
Same as task 00.

#### Out of scope
- Active Engagements live data (Module 18, Wave 5)
- Learning Progress live data (Module 20, Wave 6)
- Contribution count card (Module 5, Wave 6)
- Cross-user analytics (Module 10, Wave 6)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
- 2026-06-03: created. Empty-state cards for cross-wave dependencies (engagements, learning).

## D. References
- Brief: FRs 014-015, AGENT-16
- Design: Section 5.2 AGENT-16
- Foundation: `ai_docs/tasks/00_foundation.md`
