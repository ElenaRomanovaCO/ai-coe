# Task Suite Index

> Project: AI CoE Platform
> Generated: 2026-06-03
> Source brief: ai_docs/brief.md
> Source design: ai_docs/design.md
> Source post-demo plan: ai_docs/post-demo-plan.md
> North-star vision: docs/starters/AI CoE Platform Brief.md

---

## How to use this suite

**Incremental session (Claude already loaded with brief + design):**
Open the next task file. Copy the **A. TL;DR Checklist** section into the running session.

**Fresh session (no prior context):**
Open the next task file. Copy the **B. Standalone Prompt** section (between START and END markers) and paste as the first message of a fresh Claude Code session.

**After completing a task:**
1. Walk the Definition of Done checklist in the task file.
2. Update status in this INDEX from ☐ → ☑.
3. Append decisions or follow-ups to the task's Notes & Decisions Log.

**If a task spawns new requirements not captured:**
- Append to that task's Notes section
- Decide: add a new task file, defer to a later wave, or send it to `ai_docs/post-demo-plan.md` Section 10 (newly discovered items)

---

## Execution Order

Foundation (00) must be completed first. After that, tasks within a wave can be parallelized; waves must run in order (Wave N depends on outputs from Wave N-1 substrate even if not explicitly).

---

## Phase 0 — Foundation

Cross-cutting substrate. Everything else depends on this.

| # | Task File | Covers | Depends On | Status |
|---|---|---|---|---|
| 00 | [00_foundation.md](./00_foundation.md) | FR-001, FR-004, FR-005 (substrate); IAM / observability / CI/CD / cost cap / shared lib | none | ☑ |

**Phase 0 acceptance:** Amplify Hosting preview reachable, password gate works, ReEmbed pipeline indexes new vault files within 60s, all 5 IAM roles created, modules.json + agents.md exist, CloudWatch alarms in place.

---

## Wave 1 — Foundation modules

Demo outcome: login → browse Asset Library → chat about vault contents → see personal dashboard.

| # | Task File | Module | Covers FRs | Agents | Depends On | Status |
|---|---|---|---|---|---|---|
| 01 | [01_wave1_vault_seed_content.md](./01_wave1_vault_seed_content.md) | (substrate) | enables retrieval | none | 00 | ☑ |
| 02 | [02_wave1_chat_orchestrator.md](./02_wave1_chat_orchestrator.md) | Module 9 (Chat) | 002, 003, 006, 007, 008, 009 | AGENT-01 | 00, 01 | ☑ |
| 03 | [03_wave1_asset_library.md](./03_wave1_asset_library.md) | Module 2 | 010, 011, 012, 013 | AGENT-03 | 00, 01, 02 | ☑ |
| 04 | [04_wave1_personal_dashboard.md](./04_wave1_personal_dashboard.md) | Module 17 | 014, 015 | AGENT-16 | 00, 01, 02, 03 | ☑ |

**Wave 1 acceptance:** End-to-end demo: login → dashboard → chat asks a vault question with citations → click citation → open asset → return to dashboard.

---

## Wave 1.5 — UI Substrate (inserted)

Cross-cutting UI gaps found after Wave 1: a persistent navigation shell was never built, and pages 00–06 predate the Praxis design mocks. Do **06b before Task 07** (demo-critical, unblocked); **06c** is gated on uploading the self-contained design mocks for pixel-match.

| # | Task File | Scope | Depends On | Status |
|---|---|---|---|---|
| 06b | [06b_app_shell_navigation.md](./06b_app_shell_navigation.md) | Persistent app shell + module navigation (per `02-app-shell.md`) | 00, 02, 03, 04 | ☑ |
| 06c | [06c_wave1_2_ui_alignment.md](./06c_wave1_2_ui_alignment.md) | Align built pages to the Praxis design system + mocks (coral theme pass done + smoke-passed; full pixel-match gated on self-contained mocks) | 06b | ◐ |

---

## Wave 2 — Assessment & Delivery

Demo outcome: run a maturity assessment, build an engagement kit, chat with any single asset.

| # | Task File | Module | Covers FRs | Agents | Depends On | Status |
|---|---|---|---|---|---|---|
| 05 | [05_wave2_maturity_assessment.md](./05_wave2_maturity_assessment.md) | Module 1 | 016, 017, 018, 019 | AGENT-02, WORKER-01/02/03 | 00-04 | ☑ |
| 06 | [06_wave2_kit_builder.md](./06_wave2_kit_builder.md) | Module 3 | 020, 021, 022 | AGENT-04 | 00-05 | ☑ |
| 07 | [07_wave2_universal_asset_qa.md](./07_wave2_universal_asset_qa.md) | Module 26 | 023, 024 | AGENT-25 | 00-06 | ☑ |

**Wave 2 acceptance:** Run assessment via chat → stage + recommendations → build kit from context → download zip → chat with any asset.

---

## Wave 3 — Risk & Governance

Demo outcome: complete pre-delivery risk pass (governance check, ethics review, compliance lookup).

| # | Task File | Module | Covers FRs | Agents | Depends On | Status |
|---|---|---|---|---|---|---|
| 08 | [08_wave3_governance_checker.md](./08_wave3_governance_checker.md) | Module 4 | 025, 026 | AGENT-05, WORKER-04/05 | 00-07 | ☑ |
| 09 | [09_wave3_ethics_checker.md](./09_wave3_ethics_checker.md) | Module 21 | 027, 028 | AGENT-20, WORKER-08/09 | 00-08 | ☑ |
| 10 | [10_wave3_compliance_tracker.md](./10_wave3_compliance_tracker.md) | Module 25 | 029, 030, 031 | AGENT-24, WORKER-12/13 | 00-09 | ☑ |

**Wave 3 acceptance:** Run governance + ethics + compliance flow for a healthcare or fintech use case end-to-end.

---

## Wave 4 — Specialized Tools

Demo outcome: technical-depth surfaces (tools repo, vendor evals, prompts, Q&A).

| # | Task File | Module | Covers FRs | Agents | Depends On | Status |
|---|---|---|---|---|---|---|
| 11 | [11_wave4_skills_tools_repo.md](./11_wave4_skills_tools_repo.md) | Module 7 | 032, 033 | AGENT-08 | 00-10 | ☑ |
| 12 | [12_wave4_vendor_eval.md](./12_wave4_vendor_eval.md) | Module 13 | 034, 035 | AGENT-13 | 00-11 | ☑ |
| 13 | [13_wave4_prompt_studio.md](./13_wave4_prompt_studio.md) | Module 11 | 036, 037, 038 | AGENT-11 | 00-12 | ☑ |
| 14 | [14_wave4_qa.md](./14_wave4_qa.md) | Module 8 | 039, 040, 041 | AGENT-09 | 00-13 | ☑ |

**Wave 4 acceptance:** Tool recommendation by context, vendor comparison side-by-side, prompt fork+diff, AI-powered Q&A with citations.

---

## Wave 5 — Intelligence & Insight

Demo outcome: feed + ideation + decisions + project health + retros + benchmarks.

| # | Task File | Module | Covers FRs | Agents | Depends On | Status |
|---|---|---|---|---|---|---|
| 15 | [15_wave5_intelligence_feed.md](./15_wave5_intelligence_feed.md) | Module 24 | 042, 043, 044 | AGENT-23, WORKER-10/11 | 00-14 | ☑ |
| 16 | [16_wave5_use_case_ideation.md](./16_wave5_use_case_ideation.md) | Module 12 | 045, 046, 047 | AGENT-12 | 00-15 | ☑ |
| **16b** | [16b_wave5_agentic_skills_plugin_exchange.md](./16b_wave5_agentic_skills_plugin_exchange.md) | **Module 28** | 078, 079, 080 | AGENT-27 | 00-16 | ☑ |
| 17 | [17_wave5_decision_log.md](./17_wave5_decision_log.md) | Module 19 | 048, 049, 050 | AGENT-18 | 00-16 | ☐ |
| 18 | [18_wave5_project_health.md](./18_wave5_project_health.md) | Module 18 | 051, 052, 053 | AGENT-17 | 00-17 | ☑ |
| 19 | [19_wave5_retrospective.md](./19_wave5_retrospective.md) | Module 16 | 054, 055 | AGENT-15 | 00-18 | ☐ |
| 20 | [20_wave5_benchmark.md](./20_wave5_benchmark.md) | Module 22 | 056, 057 | AGENT-21 | 00-19 | ☐ |

**Wave 5 acceptance:** Feed personalization shifts with profile; ideation produces ranked candidates; decision similarity surfaces precedent; project health flags risks; retros extract insights; benchmark renders + exports.

---

## Wave 6 — Client-Facing & People

Demo outcome: client report PDF, community, contributions, onboarding, certifications, analytics.

| # | Task File | Module | Covers FRs | Agents | Depends On | Status |
|---|---|---|---|---|---|---|
| 21 | [21_wave6_client_report.md](./21_wave6_client_report.md) | Module 14 | 058, 059, 060 | AGENT-14, WORKER-06/07 | 00-20 | ☐ |
| 22 | [22_wave6_community_hub.md](./22_wave6_community_hub.md) | Module 6 | 061, 062, 063 | AGENT-07 | 00-21 | ☐ |
| 23 | [23_wave6_knowledge_contribution.md](./23_wave6_knowledge_contribution.md) | Module 5 | 064, 065, 066 | AGENT-06 | 00-22 | ☐ |
| 24 | [24_wave6_onboarding.md](./24_wave6_onboarding.md) | Module 23 | 067, 068 | AGENT-22 | 00-23 | ☐ |
| 25 | [25_wave6_certification.md](./25_wave6_certification.md) | Module 20 | 069, 070, 071 | AGENT-19 | 00-24 | ☐ |
| 26 | [26_wave6_analytics.md](./26_wave6_analytics.md) | Module 10 | 072, 073 | AGENT-10 | 00-25 | ☐ |

**Wave 6 acceptance:** Generate client report PDF → community hub functional → contribute + curate flow → onboarding personalizes → certifications earnable → analytics renders.

---

## Wave 7 — Development Accelerator

Demo outcome: generate scaffolded codebase from any reference architecture.

| # | Task File | Module | Covers FRs | Agents | Depends On | Status |
|---|---|---|---|---|---|---|
| 27 | [27_wave7_code_accelerator.md](./27_wave7_code_accelerator.md) | Module 27 | 074, 075, 076, 077 | AGENT-26 (Opus 4.7), WORKER-14/15/16 | 00-26 | ☐ |

**Wave 7 acceptance:** From a healthcare RAG reference architecture, generate AWS + Python + FastAPI + Lambda starter code → zip extracts → README references the architecture → daily Opus cap is enforced.

---

## Cross-task summary

- **Total tasks:** 28 (1 foundation + 27 modules)
- **Total agents built:** 26 (AGENT-01 through AGENT-26)
- **Total task workers built:** 16 (WORKER-01 through WORKER-16)
- **Total FRs covered:** 77 (FR-001 through FR-077)
- **Estimated effort:** ~12-13 weeks solo full-time
- **Build pattern:** wave-by-wave; each wave produces a demoable slice

---

## Status Legend

- ☐ Not started
- ◐ In progress
- ☑ Done
- ⊘ Blocked (note why in the task file's Notes section)

---

## Critical reminders (carry into every task)

- **No company names anywhere.** Use generic "an AI-focused IT consulting firm" or omit.
- **No real PII or client data.** Seeded demo content only.
- **Use the observability conventions from task 00.** Every agent invocation emits the standard log line and metrics.
- **Use the cost cap pattern from task 00.** Opus calls always go through `cost_cap.check_and_reserve` → `commit`.
- **AD-01 through AD-04 are locked.** Do not introduce DynamoDB, API Gateway, FastAPI, per-agent Lambdas, or per-module IAM roles without explicit user approval.
- **When ambiguity surfaces, ask before coding.** Karpathy guidelines apply.

---

## When you finish all tasks

Run the demo end-to-end. Record a walkthrough. Then move to `ai_docs/post-demo-plan.md` Section 9 (prospect interviews).
