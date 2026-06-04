# Task: Wave 5 — Client Benchmark Comparator (Module 22, AGENT-21)

> **Phase:** 5
> **Feature group:** Wave 5 (Intelligence & Insight)
> **Covers:** FR-056 (benchmark view), FR-057 (slide-ready export)
> **Builds:** AGENT-21 (Haiku 4.5)
> **Depends on:** 00, 01, 02, 05 (Maturity Assessment)
> **Blocks:** Module 14 (Client Report uses benchmarks)
> **Estimated effort:** 1-2 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** After a maturity assessment, user sees a benchmark view: where this client sits vs anonymized peers in their industry. Each stage shows typical patterns and common next moves. Export as slide-ready markdown.

**Build steps:**
1. AGENT-21 (Haiku 4.5, 3 tools: get_peer_distribution, write_benchmark_narrative, export_benchmark_slide).
2. Flip Module 22 enabled.
3. UI: benchmark view on assessment result page (extends task 05 result view) + standalone `/modules/benchmark/[assessment_id]`.
4. Seeded peer distribution: anonymized aggregate data from seeded assessments + synthetic.

**Files to create/edit:**

- `agents/lambdas/modules/agent_21_benchmark.py`
- `vault/modules.json` — flip Module 22
- `vault/benchmarks/_seed_peer_distribution.json` — seeded aggregate data
- `web/app/(authenticated)/modules/benchmark/[assessment_id]/page.tsx`
- `web/app/(authenticated)/modules/assessment/[id]/page.tsx` — add Benchmark section
- `web/app/(authenticated)/modules/benchmark/actions.ts`

**Done when:**
- [ ] FRs 056-057 verified
- [ ] DoD from 00_foundation.md passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **Client Benchmark Comparator (Module 22)** for the AI CoE Platform. Tasks 00-19 are done.

#### Agent spec (AGENT-21)

```python
class GetBenchmarkRequest(BaseModel):
    assessment_id: str

class BenchmarkResponse(BaseModel):
    assessment_id: str
    client_stage: int
    industry: str
    peer_distribution: dict[int, float]             # stage -> percent of peers
    typical_use_cases_at_stage: dict[int, list[str]]
    common_next_moves: list[str]
    narrative: str
    export_url: str | None
```

Tools: get_peer_distribution (reads `_seed_peer_distribution.json` plus any real assessments for the same industry), write_benchmark_narrative (Haiku call), export_benchmark_slide (renders markdown).

#### modules.json entry
```json
{
  "id": "module-22",
  "name": "Client Benchmark Comparator",
  "wave": 5,
  "purpose": "Place a client's AI maturity vs anonymized industry peers; produce executive-friendly benchmarks.",
  "when_to_use": ["Right after a maturity assessment", "Preparing a client readout"],
  "example_queries": ["Benchmark this assessment", "How does my client compare to peers?", "Generate a benchmark slide"],
  "agent_id": "AGENT-21",
  "model_tier": "haiku-4-5",
  "worker_ids": [],
  "enabled": true
}
```

#### Implementation steps
1. Agent + 3 tools.
2. Seed `_seed_peer_distribution.json` with synthetic distributions for each of the 8 industries (8 stages each → 48 cells).
3. Benchmark view: bar chart (stage distribution), client marker, narrative paragraph, common-next-moves list.
4. Export → vault/benchmarks/{display_name}/{ts}.md.
5. Smoke test: complete a healthcare stage-2 assessment, view benchmark → distribution shown, narrative reads sensibly, export downloads.

#### Definition of done
- [ ] FRs 056-057 verified
- [ ] DoD from 00_foundation.md passed

#### Out of scope
- Live benchmark refresh as new assessments come in (Module 10 Analytics could later aggregate)
- Per-firm anonymization (post-demo when multi-tenancy lands)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
## D. References
- Brief: FRs 056-057, AGENT-21
- Foundation: `ai_docs/tasks/00_foundation.md`
