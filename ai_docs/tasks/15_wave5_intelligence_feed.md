# Task: Wave 5 — AI Intelligence Feed & Release Radar (Module 24, AGENT-23 + WORKER-10/11)

> **Phase:** 5
> **Feature group:** Wave 5 (Intelligence & Insight)
> **Covers:** FR-042 (personalized feed), FR-043 (chat with feed item), FR-044 (quarterly radar)
> **Builds:** AGENT-23 (Sonnet 4.6), WORKER-10 item_classifier, WORKER-11 commentary_writer
> **Depends on:** 00, 01 (seeded feed items), 02, 07 (Universal Asset Q&A pattern)
> **Blocks:** none
> **Estimated effort:** 2-3 days solo
> **Status:** ☑ DONE — deployed + live-verified (2026-06-11). Backend: AiCoE-Agents
> redeployed (3 Lambdas, image-only diff, no IAM change); live `get` smoke returned a
> real Sonnet WORKER-11 note (`tailored: true`) — confirms the workers-role cross-region
> Bedrock grant holds. Frontend: Amplify build #31 SUCCEED on `94cebbb`; feed + radar
> routes serve (gated 307 → /login).

---

## A. TL;DR Checklist

**Goal:** A user opens the feed and sees personalized items (filtered by their profile's industries and tech focus). Each item has a "what this means" note and a Chat-with-this option. A separate Radar view shows Adopt/Trial/Assess/Hold.

**Build steps:**

1. WORKER-10 item_classifier (raw item → category + relevance score + industry tags).
2. WORKER-11 commentary_writer (item + user profile → "what this means" note tailored to industry/stage).
3. AGENT-23 (Sonnet 4.6, 4 tools).
4. Flip Module 24 enabled.
5. `/modules/intelligence-feed` browse + `/modules/intelligence-feed/[id]` detail with Q&A panel.
6. `/modules/intelligence-feed/radar` Adopt/Trial/Assess/Hold view.

**Files to create/edit:**

- `agents/lambdas/workers/worker_10_item_classifier.py`
- `agents/lambdas/workers/worker_11_commentary_writer.py`
- `agents/lambdas/modules/agent_23_feed.py`
- `vault/modules.json` — flip Module 24
- `web/app/(authenticated)/modules/intelligence-feed/page.tsx`
- `web/app/(authenticated)/modules/intelligence-feed/[id]/page.tsx`
- `web/app/(authenticated)/modules/intelligence-feed/radar/page.tsx`
- `web/app/(authenticated)/modules/intelligence-feed/actions.ts`

**Done when:**
- [ ] FRs 042-044 verified
- [ ] Personalization works (changing profile industries changes feed)
- [ ] Radar renders 4 quadrants from seed data
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **AI Intelligence Feed & Release Radar (Module 24)** for the AI CoE Platform. Tasks 00-14 are done. Seeded feed items exist at `vault/feed/`.

#### Worker specs

- **WORKER-10 item_classifier**: takes raw feed item → assigns category, industries, relevance score (0-1).
- **WORKER-11 commentary_writer**: takes item + user profile (industries, stage focus) → writes a "what this means for {industry} at {stage}" note (2-4 paragraphs).

For demo: workers operate on seeded items at view time, generating commentary lazily. Real ingestion (RSS, arXiv, news APIs) is post-demo per Section 3.1 of `post-demo-plan.md`.

#### Agent spec (AGENT-23)

```python
class ListFeedRequest(BaseModel):
    display_name: str
    category: str | None
    industry: str | None
    radar_status: str | None

class GetFeedItemRequest(BaseModel):
    item_id: str
    user_profile: UserProfile

class RadarViewResponse(BaseModel):
    adopt: list[FeedItemSummary]
    trial: list[FeedItemSummary]
    assess: list[FeedItemSummary]
    hold: list[FeedItemSummary]
```

Tools: list_feed_items, get_feed_item (lazily invokes WORKER-11 if commentary absent), invoke_worker (WORKER-10/11), get_radar.

#### modules.json entry
```json
{
  "id": "module-24",
  "name": "Intelligence Feed & Radar",
  "wave": 5,
  "purpose": "Curated AI intelligence feed personalized by industry and stage focus, plus quarterly tech radar.",
  "when_to_use": ["Stay current on AI landscape", "See what is relevant to my engagements", "Reference the radar for tech advice"],
  "example_queries": ["What's new in AI for healthcare?", "Show me the latest LLM releases", "What's on the radar right now?"],
  "agent_id": "AGENT-23",
  "model_tier": "sonnet-4-6",
  "worker_ids": ["WORKER-10", "WORKER-11"],
  "enabled": true
}
```

#### Implementation steps
1. Workers + agent per spec.
2. Browse: filter by category/industry/radar status; show category badges, date, source link.
3. Detail page: full item + WORKER-11 commentary + AssetChatPanel.
4. Radar: 4-column grid (Adopt/Trial/Assess/Hold) with cards.
5. Smoke test: change profile industries → feed reorders; open an item → commentary tailored to profile; radar shows seeded entries.

#### Definition of done
- [ ] FRs 042-044 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Real ingestion from RSS / arXiv / news (post-demo-plan.md Section 3.1)
- Subscribe-by-email digests (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

- **2026-06-10: WORKER-11 makes its own Bedrock call.** The spec scopes commentary
  generation to WORKER-11 and the workers Lambda role already grants
  `bedrock:InvokeModel` (`infra/stacks/iam.py`), so WORKER-11 is the first LLM-backed
  worker (Sonnet 4.6). It degrades to a deterministic note (the item's own "What this
  means" section, or its lede) when Bedrock errors, so the detail page always renders
  and tests run offline. AGENT-23 stays mechanical (list/get/radar) per the AGENT-24
  precedent and invokes WORKER-11 lazily on `get`.
- **2026-06-10: Personalization via UI selectors, not a stored profile.** The app has
  no persistent user profile (kit-builder / ethics / governance all use local industry
  + stage selectors). The feed follows suit: the browse page's "Personalize" selectors
  pass `user_profile.industries` + `ai_stage` to `list`, which re-ranks server-side via
  WORKER-10 (relevance = industry overlap + tech-focus tag overlap + radar weight; no
  recency in the worker — AGENT-23 applies the date tie-break across the batch). The
  active profile is carried to the detail page via query params and re-tailorable there.
- **2026-06-10: Chat-with-item reuses `AssetChatPanelHook` (AGENT-25).** That component
  is explicitly documented for Intelligence Feed reuse; it grounds a scoped Q&A in the
  item body, satisfying FR-043 without AGENT-23 needing its own chat loop.
- **2026-06-10: modules.json `model_tier` set to `sonnet-4-6`** (was `haiku-4-5`) to
  match the AGENT-23 spec, plus `enabled: true` and `ui_route: /modules/intelligence-feed`
  (mirroring the compliance-tracker entry). Nav entry enabled + routed in `web/lib/nav.ts`.

**Verification (local):** `pytest agents/` 298 passed; `ruff check agents/` clean;
web `tsc --noEmit` clean, `eslint` clean, `next build` succeeds with all three
`/modules/intelligence-feed*` routes present (dynamic). Personalization, lazy
commentary + fallback, and radar grouping are covered by `test_agent_23.py`,
`test_worker_10.py`, and `test_worker_11.py`.

## D. References
- Brief: FRs 042-044, AGENT-23, WORKER-10/11
- Foundation: `ai_docs/tasks/00_foundation.md`
- Post-demo ingestion: `ai_docs/post-demo-plan.md` Section 3.1
