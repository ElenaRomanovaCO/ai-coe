# Task: Wave 6 — Analytics Dashboard (Module 10, AGENT-10)

> **Phase:** 6
> **Feature group:** Wave 6 (Client-Facing & People)
> **Covers:** FR-072 (CoE-lead view), FR-073 (drill-in + export)
> **Builds:** AGENT-10 (Haiku 4.5)
> **Depends on:** 00, 01, 02, plus everything in earlier waves (data sources)
> **Blocks:** none
> **Estimated effort:** 2-3 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** CoE-style dashboard with: asset usage (most accessed by industry / by time), maturity assessment distribution, contribution health, learning path completions, CoE ROI indicators (time saved estimates).

**Build steps:**
1. AGENT-10 (Haiku 4.5, 3 tools: aggregate_usage, get_distribution, summarize_metrics).
2. Flip Module 10 enabled.
3. `/modules/analytics` with tabs for the 5 views.

**Files to create/edit:**

- `agents/lambdas/modules/agent_10_analytics.py`
- `vault/modules.json` — flip Module 10
- `web/app/(authenticated)/modules/analytics/page.tsx`
- `web/app/(authenticated)/modules/analytics/actions.ts`
- `web/components/analytics/*.tsx` — charts (recharts)

**Done when:**
- [ ] FRs 072-073 verified
- [ ] All 5 tab views render with current data
- [ ] Export produces markdown summary
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Analytics Dashboard (Module 10)** for the AI CoE Platform. Tasks 00-25 are done.

#### Agent spec (AGENT-10)

Tools:
- `aggregate_usage(time_range)` → reads CloudWatch metrics + S3 inventory for usage stats
- `get_distribution(metric, dimension)` → e.g. assessment stage distribution by industry
- `summarize_metrics(metrics_snapshot)` → narrative summary for export

#### Data sources
- CloudWatch metrics (agent invocations, latency, cost) emitted per task 00 observability conventions
- S3 inventory (asset count, assessment count, decision count, retro count)
- User profiles (contribution count, learning progress, badges)
- All read-only

#### modules.json entry
```json
{
  "id": "module-10",
  "name": "Analytics Dashboard",
  "wave": 6,
  "purpose": "CoE leadership view of platform usage, maturity distributions, contribution health, ROI indicators.",
  "when_to_use": ["Weekly CoE review", "Quarterly leadership update", "Identify gaps in the library"],
  "example_queries": ["Show this month's usage", "Maturity distribution by industry", "Top contributors"],
  "agent_id": "AGENT-10",
  "model_tier": "haiku-4-5",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent + 3 tools.
2. Tabs:
   - Asset Usage (top assets, by team, by industry, by time series)
   - Maturity Assessments (stage distribution by industry, count over time)
   - Contribution Health (who's contributing, gap areas)
   - Enablement (learning path completions, office hours attendance)
   - ROI Indicators (time saved estimates, engagement acceleration)
3. Charts: recharts bar/line/heatmap.
4. Export: AGENT-10 writes a `analytics/{ts}.md` summary in vault.
5. Smoke test: open dashboard, all tabs render, export produces a valid markdown file.

#### Definition of done
- [ ] FRs 072-073 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Real BI tool integration (Power BI, Tableau) post-demo
- Per-firm or per-tenant filtering (post-demo, ties to multi-tenancy)
- Auto-emailed weekly digests (post-demo)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 072-073, AGENT-10
- Foundation: `ai_docs/tasks/00_foundation.md`
