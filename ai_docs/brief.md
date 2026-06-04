# Project Brief: AI CoE Platform

> Generated: 2026-06-03
> Status: Locked
> Source template: docs/templates/01_brainstorm_brief.md
> North-star vision: docs/starters/AI CoE Platform Brief.md (27-module roadmap, authoritative)

---

## 1. Project Identity

- **Name:** AI CoE Platform
- **One-line pitch:** Internal platform for consultants at AI-focused IT consulting firms to orient on engagements, assess client AI maturity, assemble delivery kits, and access curated AI knowledge through a hierarchical multi-agent conversational interface over a markdown knowledge base.
- **Project type:** agentic-ai-multi-agent (3-layer hierarchical: orchestrator, module agents, task workers)
- **Repo/workspace:** c:\Users\rev19\kiro-projects\ai-coe\ai-coe\
- **Scope posture:** full functional scope (all 27 modules from north-star brief), downscoped on security/SLA/resilience/volume only. Cost-efficient.

---

## 2. End Goal & Problem

### 2.1 End Goal (North Star)

> "This platform helps **consultants at AI-focused IT consulting firms** achieve **faster, more consistent AI engagement delivery and client maturity assessment** using **a hierarchical multi-agent system over a curated markdown knowledge base**."

### 2.2 Root Problem

- **Pain:** Consultants rebuild kickoff materials per engagement, client AI assessments are inconsistent, AI delivery knowledge lives in silos, and there is no single place to orient, accelerate, or learn.
- **Quantified consequence:** Assumed, not validated. This build is exploratory. Pain validation is RISK-01 below.
- **Urgency:** AI engagements are accelerating across consulting firms. Firms without shared infrastructure will fall behind.

### 2.3 Success Definition

How do we know this project succeeded 90 days post-launch?

- Demo runs cleanly end-to-end for 2-3 IT consulting firm contacts
- At least one of them says "I would actually use this" with a concrete use case
- Identify which 3-5 modules out of 27 generate the strongest reaction (signal for what to productize)

---

## 3. Users & Roles

### 3.1 Primary User

- **Who:** The developer (single user, standing in for "consultant at any AI-focused IT consulting firm")
- **Frustrations:** Rebuilds engagement assets from scratch, no shared maturity framework, scattered tool knowledge
- **Urgent goals:** Orient fast on new engagement, assess client AI stage, assemble starter kit, find prior knowledge

### 3.2 Future Users (post-demo, captured in post-demo-plan.md)

- Consultant / Architect: primary user when productized
- CoE Lead / Curator: manages library, reviews contributions
- Practice Lead / Leadership: views adoption metrics, ROI
- Client Stakeholder: limited read-only portal access to their maturity report

### 3.3 System Actor (autonomous behavior)

- **Trigger conditions:** Knowledge Base file change in S3 triggers re-embedding pipeline
- **Permitted autonomous actions:** Re-embed changed files, update vector index, refresh module registry cache
- **Human-in-the-loop boundaries:** No autonomous content publishing, no autonomous client-facing outputs

---

## 4. MVP Scope

### 4.1 In Scope (demo ships with all 27 modules functional)

All 27 modules from the north-star brief, full functional behavior, demo-scale data:

**Wave 1 - Foundation**
- Module 9: Chat (basic orchestrator)
- Knowledge Base substrate (S3 vault)
- Module 2: Asset Library
- Module 17: Personal Dashboard

**Wave 2 - Assessment & Delivery**
- Module 1: AI Maturity Assessment
- Module 3: Engagement Kit Builder
- Module 26: Universal Asset Q&A (Chat with Anything)

**Wave 3 - Risk & Governance**
- Module 4: Governance & Risk Checker
- Module 21: AI Ethics & Bias Checker
- Module 25: Global AI Regulation & Compliance Tracker

**Wave 4 - Specialized Tools**
- Module 7: Skills & Tools Repository
- Module 13: Vendor & Model Evaluation Center
- Module 11: Prompt Engineering Studio
- Module 8: Q&A (async + AI-powered)

**Wave 5 - Intelligence & Insight**
- Module 24: AI Intelligence Feed & Release Radar (Module 15 merged in)
- Module 12: AI Use Case Ideation Engine
- Module 19: Decision Log
- Module 18: AI Project Health Monitor
- Module 16: Engagement Retrospective Tracker
- Module 22: Client Benchmark Comparator

**Wave 6 - Client-Facing & People**
- Module 14: Client-Facing Maturity Report Portal (demo: PDF download only)
- Module 6: Community & Enablement Hub
- Module 5: Knowledge Contribution
- Module 23: Consultant Onboarding Journey
- Module 20: Certification & Badging
- Module 10: Analytics Dashboard

**Wave 7 - Development Accelerator**
- Module 27: Claude Code Development Accelerator

### 4.2 Explicitly Downscoped (operational only, not functional)

- **Auth:** Single shared password + name field in localStorage (no real identity). Post-demo: Cognito.
- **Module 14 portal:** PDF download instead of shareable signed-URL portal. Post-demo: signed-URL public portal.
- **Modules 24 & 25 ingestion:** Seeded with curated demo content (fintech, healthcare, PII focus). No live RSS / arXiv / regulatory feeds. Post-demo: real ingestion engine.
- **SLA:** No uptime guarantee, no DR, no multi-AZ, no failover. Single-region, snapshot-only backups.
- **Volume:** Demo-scale only (1-2 concurrent users, ~50-100 chat turns per day).
- **Compliance:** No SOC 2, HIPAA, GDPR posture. Demo content only, no real PII or client data.
- **Per-user data isolation:** Not enforced (single shared password means everyone sees everyone's content).

### 4.3 Non-Goals (will never build in this version)

- Anything that names a specific consulting firm
- Anything requiring real client data or PII
- Public-facing marketing site
- Billing or time tracking
- Real-time model inference infrastructure (we call Bedrock, we do not host models)

---

## 5. Functional Requirements

Organized by module and wave. Each FR is testable. Format: `FR-NNN: <role> can <action> so that <outcome>` with acceptance.

### 5.1 Cross-Cutting (auth, app shell)

- **FR-001:** User can enter the app via a single shared password gate and provide a display name stored in browser localStorage.
  - Acceptance: wrong password blocks all routes; correct password + name persists across page reloads.
- **FR-002:** User can navigate to any module from a persistent sidebar.
  - Acceptance: sidebar lists all 27 modules grouped by wave; clicking each loads the module page.
- **FR-003:** User can open the Chat from any page via a persistent chat dock.
  - Acceptance: chat dock visible on every authenticated route; conversation state persists across navigation within a session.

### 5.2 Wave 1 - Foundation

**Knowledge Base (substrate)**

- **FR-004:** System auto-embeds every markdown file in the S3 Knowledge Base bucket on file change.
  - Acceptance: uploading a new .md file to the vault produces a vector record retrievable by Chat within 60 seconds.
- **FR-005:** The agents.md file at the Knowledge Base root controls Chat orchestrator behavior without code redeploy.
  - Acceptance: editing agents.md changes Chat's routing behavior on the next chat turn.

**Module 9: Chat (orchestrator)**

- **FR-006:** Chat retrieves from the Knowledge Base, cites source files by name, and links inline to Asset Library entries.
  - Acceptance: chat response includes at least one citation linking to a vault file when a relevant doc exists.
- **FR-007:** Chat can describe any of the 27 modules ("what does Module 4 do?") using the module registry.
  - Acceptance: describing a module returns purpose, when-to-use, and example invocations from the registry.
- **FR-008:** Chat can list available modules filtered by wave, purpose, or keyword.
  - Acceptance: "show me risk-related modules" returns Modules 4, 21, 25.
- **FR-009:** Chat invokes the correct module agent when user intent matches that module.
  - Acceptance: "assess my client's AI maturity" invokes the Module 1 agent, not Module 4.

**Module 2: Asset Library**

- **FR-010:** User can browse Asset Library filtered by industry, AI adoption stage, asset type.
  - Acceptance: filter chips reduce the visible asset list to matching frontmatter values.
- **FR-011:** User can open a single Asset Library entry and view its markdown rendered, with frontmatter shown alongside.
  - Acceptance: opening an asset shows rendered markdown + a sidebar panel with all frontmatter fields.
- **FR-012:** User can save an asset to their Personal Dashboard.
  - Acceptance: saved assets appear in Personal Dashboard for the logged-in user's display name.
- **FR-013:** User can rate or flag an asset.
  - Acceptance: rating persists; flagged assets show a flag indicator.

**Module 17: Personal Dashboard**

- **FR-014:** User sees their saved assets, recent Chat conversations, active engagements on the dashboard.
  - Acceptance: dashboard reflects user's session activity scoped by display name.
- **FR-015:** Dashboard shows recommended items based on recent activity.
  - Acceptance: after browsing 3 healthcare assets, dashboard surfaces healthcare-relevant recommendations.

### 5.3 Wave 2 - Assessment & Delivery

**Module 1: AI Maturity Assessment**

- **FR-016:** User can start an AI Maturity Assessment from Chat or directly from the module page.
  - Acceptance: both entry points reach the same assessment flow.
- **FR-017:** The Assessment runs as a conversational back-and-forth with adaptive questions (roughly 10 questions).
  - Acceptance: each question's phrasing adapts to prior answers; total turn count between 8-12.
- **FR-018:** The Assessment outputs a stage placement (0-5) and 3-5 recommended Asset Library entries.
  - Acceptance: result page shows stage, plain-language explanation, and clickable asset recommendations.
- **FR-019:** Assessment results are saved as a markdown file in the Knowledge Base under assessments/.
  - Acceptance: completed assessment produces a timestamped .md file searchable by Chat.

**Module 3: Engagement Kit Builder**

- **FR-020:** User can request an Engagement Kit from Chat by stating engagement context.
  - Acceptance: "build a kit for healthcare, stage 2, discovery workshop" produces a kit.
- **FR-021:** Kit Builder assembles a zip containing selected markdown files, a one-page kit README, and a structure folder.
  - Acceptance: downloaded zip extracts to a labeled folder with README.md and source files.
- **FR-022:** User can review the suggested kit before download and swap or add items.
  - Acceptance: a preview UI lists kit items with add/remove controls before zip is generated.

**Module 26: Universal Asset Q&A**

- **FR-023:** Every asset page displays a "Chat with this" button that opens a contextual chat panel.
  - Acceptance: chat panel is scoped to the current asset's content as RAG context.
- **FR-024:** User can ask the asset chat to summarize, compare to other assets, or translate to a checklist.
  - Acceptance: each of these intents returns a relevant answer with citations.

### 5.4 Wave 3 - Risk & Governance

**Module 4: Governance & Risk Checker**

- **FR-025:** User can input industry, data types, geography, and AI use case type into the Governance Checker.
  - Acceptance: form captures all 4 inputs and triggers analysis.
- **FR-026:** Checker outputs a structured risk checklist with regulation links.
  - Acceptance: output includes flags tagged to relevant Module 25 regulation entries.

**Module 21: AI Ethics & Bias Checker**

- **FR-027:** User can submit a use case description and receive a bias/fairness/explainability review.
  - Acceptance: output covers bias risks, fairness considerations, explainability requirements, human-oversight recommendations.
- **FR-028:** Ethics review can be saved to the Knowledge Base and linked to an engagement.
  - Acceptance: saved review appears as a .md file under reviews/ethics/.

**Module 25: Global AI Regulation & Compliance Tracker**

- **FR-029:** User can browse regulations filtered by geography, industry, status, AI use case type.
  - Acceptance: filters reduce regulation list; demo data covers fintech, healthcare, PII themes.
- **FR-030:** Each regulation entry shows status, effective date, scope, requirements, implications, source link.
  - Acceptance: clicking a regulation shows all fields rendered from its markdown frontmatter.
- **FR-031:** User can ask Chat to apply a regulation to a specific use case.
  - Acceptance: "how does HIPAA AI guidance apply to a medical imaging classifier?" returns a checklist.

### 5.5 Wave 4 - Specialized Tools

**Module 7: Skills & Tools Repository**

- **FR-032:** User can browse tools by category, stack, use case, AI stage, cost model.
  - Acceptance: filters reduce the visible tool list.
- **FR-033:** User can view a tool detail page with description, best-fit scenarios, ratings, limitations, links.
  - Acceptance: tool detail page renders from markdown with frontmatter sidebar.

**Module 13: Vendor & Model Evaluation Center**

- **FR-034:** User can browse vendor/model evaluations by category (LLM providers, vector DBs, cloud platforms, frameworks).
  - Acceptance: category navigation reveals all evaluations under it.
- **FR-035:** User can build a custom side-by-side comparison from selected evaluations.
  - Acceptance: comparison builder accepts 2-4 entries and produces a comparison table.

**Module 11: Prompt Engineering Studio**

- **FR-036:** User can create, fork, version, and run prompts in a workspace UI.
  - Acceptance: prompt creation persists; fork creates a child version; version history is visible.
- **FR-037:** User can test a prompt live against a selected Bedrock model and see output.
  - Acceptance: clicking "Run" sends the prompt to the chosen model and streams the response.
- **FR-038:** User can compare prompt versions side-by-side with diff view.
  - Acceptance: side-by-side comparison highlights changes between two versions.

**Module 8: Q&A**

- **FR-039:** User can post a question tagged by topic, industry, stage.
  - Acceptance: posted question appears in the Q&A feed.
- **FR-040:** User can post answers and upvote them.
  - Acceptance: upvote counts persist; sort by votes works.
- **FR-041:** AI-powered Q&A returns synthesized answers from across the Knowledge Base with citations.
  - Acceptance: a natural language question returns an answer with at least one source citation.

### 5.6 Wave 5 - Intelligence & Insight

**Module 24: AI Intelligence Feed & Release Radar**

- **FR-042:** User sees a feed of AI items (model releases, tool launches, research, news) filtered by their profile.
  - Acceptance: feed items have CoE-authored "what this means" notes (seeded for demo).
- **FR-043:** User can chat with any feed item.
  - Acceptance: clicking "Discuss" opens chat scoped to that item's content.
- **FR-044:** Feed shows a quarterly AI Radar (Adopt / Trial / Assess / Hold) view.
  - Acceptance: radar entries render from seeded data with category and rationale.

**Module 12: AI Use Case Ideation Engine**

- **FR-045:** User inputs industry, pain points, goals, available data, current maturity stage.
  - Acceptance: form captures all 5 fields.
- **FR-046:** Engine generates a prioritized list of AI use case candidates with effort, impact, prerequisites, examples.
  - Acceptance: output table shows at least 5 candidates ranked by effort/impact.
- **FR-047:** User can export the ideation result as a markdown deliverable.
  - Acceptance: export produces a downloadable .md file.

**Module 19: Decision Log**

- **FR-048:** User can log an architectural decision with context, alternatives, rationale, outcome.
  - Acceptance: decision entry persists as a .md file under decisions/.
- **FR-049:** User can search decisions across all past engagements.
  - Acceptance: full-text search returns matching decision entries.
- **FR-050:** Decisions surface similar past decisions via vector similarity.
  - Acceptance: opening a decision shows a "Related decisions" panel.

**Module 18: AI Project Health Monitor**

- **FR-051:** User can register an active engagement with context and post updates.
  - Acceptance: engagement record persists; updates are timestamped.
- **FR-052:** Monitor flags deviations from best practices with remediation suggestions.
  - Acceptance: posting an update triggers an analysis pass that returns 0+ flags.
- **FR-053:** Portfolio view shows all active engagements with risk indicators.
  - Acceptance: dashboard lists all engagements with color-coded status.

**Module 16: Engagement Retrospective Tracker**

- **FR-054:** User can complete a structured retrospective at engagement close.
  - Acceptance: retro form captures use cases, patterns, what worked, what failed, stage reassessment.
- **FR-055:** Retro outputs are extracted into reusable insights and saved to the Knowledge Base.
  - Acceptance: extracted insights appear as new vault entries linked to source retro.

**Module 22: Client Benchmark Comparator**

- **FR-056:** User can see a benchmark view after a maturity assessment showing peer distribution.
  - Acceptance: benchmark shows stage distribution from anonymized assessment data (seeded for demo).
- **FR-057:** Benchmark export produces a slide-ready deliverable.
  - Acceptance: export produces a downloadable .md / .pdf with benchmark data.

### 5.7 Wave 6 - Client-Facing & People

**Module 14: Client-Facing Maturity Report Portal**

- **FR-058:** User can generate a formatted maturity report from a completed assessment.
  - Acceptance: report is auto-generated with score, stage, benchmark, recommendations, use cases.
- **FR-059:** User can edit narrative sections of the report before publishing.
  - Acceptance: edits persist; preview reflects edits.
- **FR-060:** User can export the report as a PDF for sharing.
  - Acceptance: PDF download produces a polished, branded document.
  - Note: signed-URL public portal is deferred to post-demo per post-demo-plan.md.

**Module 6: Community & Enablement Hub**

- **FR-061:** User can browse learning paths by role and AI adoption stage.
  - Acceptance: learning paths filter by role/stage.
- **FR-062:** User can sign up for office hours and post to community threads.
  - Acceptance: signup persists; community posts appear in the thread feed.
- **FR-063:** User can view an expert directory.
  - Acceptance: directory lists demo personas with expertise tags.

**Module 5: Knowledge Contribution**

- **FR-064:** User can submit a new asset via a structured form.
  - Acceptance: submission produces a .md file in a pending/ folder.
- **FR-065:** Curator can review, tag, and approve submissions.
  - Acceptance: approval moves the file from pending/ to the live Knowledge Base path.
- **FR-066:** AI-assisted anonymization runs on submitted content.
  - Acceptance: agent flags potential identifying details before publish.

**Module 23: Consultant Onboarding Journey**

- **FR-067:** New user gets a personalized onboarding path based on profile.
  - Acceptance: completing profile generates a tailored onboarding checklist.
- **FR-068:** Onboarding includes a guided tour, recommended assets, key tools.
  - Acceptance: tour walks through the top 5 modules; checklist tracks progress.

**Module 20: Certification & Badging**

- **FR-069:** User can browse available certifications by role and AI domain.
  - Acceptance: cert catalog filters by role and domain.
- **FR-070:** User can complete a learning path, take assessments, and earn a badge.
  - Acceptance: badge appears on Personal Dashboard after completion.
- **FR-071:** Leadership view shows team capability map.
  - Acceptance: capability dashboard summarizes badges across users.

**Module 10: Analytics Dashboard**

- **FR-072:** CoE lead can view asset usage, maturity assessment distribution, contribution health.
  - Acceptance: dashboard renders the three views with seeded analytics data.
- **FR-073:** Lead can drill into specific metrics and export a summary.
  - Acceptance: drill-downs reveal time-series; export produces a .md / .pdf summary.

### 5.8 Wave 7 - Development Accelerator

**Module 27: Claude Code Development Accelerator**

- **FR-074:** User can select a reference architecture from the Asset Library and click "Generate Starter Code".
  - Acceptance: a code generation flow starts with reference architecture as input.
- **FR-075:** User specifies target cloud, language/framework, deployment context.
  - Acceptance: form captures all 3 inputs.
- **FR-076:** System generates a scaffolded codebase (folder structure, IaC, API stubs, README, CI/CD).
  - Acceptance: output is a downloadable zip with required files.
- **FR-077:** User can paste existing code for review against CoE best practices.
  - Acceptance: review output lists anti-patterns, suggestions, links to relevant reference architectures.

---

## 6. Multi-Agent Architecture

### 6.1 Orchestration Pattern

- **Framework:** AWS Strands Agents (Python)
- **Pattern:** 3-layer hierarchical (orchestrator → module agents → task workers)
- **State persistence:** S3 (per-session JSON files) + Knowledge Base for content state
- **Checkpoint strategy:** per session turn, written to S3 conversation log

### 6.2 Layer 1 - Orchestrator

#### AGENT-01: Chat Orchestrator

- **Role:** Front-door conversational agent. Routes user intent to module agents, composes their outputs, narrates results.
- **Model:** Bedrock Claude Sonnet 4.6 (reasoning needed for routing across 27 modules)
- **Inputs:** ChatRequest schema (user_message, session_id, display_name, current_route)
- **Outputs:** ChatResponse schema (assistant_message, citations, invoked_modules, ui_actions)
- **Tools:**
  - `search_knowledge_base(query, top_k)` - RAG over the markdown vault via S3 Vectors
  - `describe_module(module_id)` - meta-query against module registry
  - `list_modules(filter)` - browse the module registry
  - `invoke_module(module_id, payload)` - hand off to a Layer 2 module agent
  - `read_agents_md()` - read the live agents.md file from S3 vault root
- **Triggers:** every user chat turn
- **Failure mode:** if invoke_module fails, return the error inline with a fallback retrieval-only answer

### 6.3 Layer 2 - Module Agents (27 agents, one per module)

For brevity, the brief lists each agent's id, model, and one-line role. Full system prompts and tool schemas are defined in the implementation plan.

| Agent ID | Module | Model | Role |
|---|---|---|---|
| AGENT-02 | Module 1: AI Maturity Assessment | Sonnet 4.6 | Runs the 10-question adaptive assessment, scores stage 0-5 |
| AGENT-03 | Module 2: Asset Library | Haiku 4.5 | Filters and retrieves assets, returns structured results |
| AGENT-04 | Module 3: Engagement Kit Builder | Sonnet 4.6 | Selects assets, drafts kit README, returns zip manifest |
| AGENT-05 | Module 4: Governance & Risk Checker | Sonnet 4.6 | Maps context to risks and regulations |
| AGENT-06 | Module 5: Knowledge Contribution | Sonnet 4.6 | Assists anonymization, tagging, duplicate detection |
| AGENT-07 | Module 6: Community Hub | Haiku 4.5 | Surfaces threads, summarizes discussions |
| AGENT-08 | Module 7: Skills & Tools Repo | Haiku 4.5 | Recommends tools by context |
| AGENT-09 | Module 8: Q&A | Sonnet 4.6 | Synthesizes answers from Knowledge Base with citations |
| AGENT-10 | Module 10: Analytics Dashboard | Haiku 4.5 | Generates summaries of usage data |
| AGENT-11 | Module 11: Prompt Studio | Sonnet 4.6 | Suggests improvements, detects anti-patterns |
| AGENT-12 | Module 12: Use Case Ideation | Sonnet 4.6 | Generates ranked use case candidates |
| AGENT-13 | Module 13: Vendor Eval Center | Sonnet 4.6 | Builds comparisons, flags stale entries |
| AGENT-14 | Module 14: Client Report Portal | Sonnet 4.6 | Generates narrative report sections |
| AGENT-15 | Module 16: Retrospective Tracker | Sonnet 4.6 | Extracts insights from retro free-text |
| AGENT-16 | Module 17: Personal Dashboard | Haiku 4.5 | Generates personalized recommendations |
| AGENT-17 | Module 18: Project Health Monitor | Sonnet 4.6 | Detects risks from update text |
| AGENT-18 | Module 19: Decision Log | Haiku 4.5 | Tags decisions, finds similar past decisions |
| AGENT-19 | Module 20: Certification & Badging | Haiku 4.5 | Recommends next certification, assesses exercises |
| AGENT-20 | Module 21: Ethics & Bias Checker | Sonnet 4.6 | Identifies bias/fairness/explainability risks |
| AGENT-21 | Module 22: Client Benchmark | Haiku 4.5 | Generates benchmark narratives |
| AGENT-22 | Module 23: Onboarding Journey | Haiku 4.5 | Generates personalized onboarding paths |
| AGENT-23 | Module 24: Intelligence Feed | Sonnet 4.6 | Generates "what this means" commentary |
| AGENT-24 | Module 25: Compliance Tracker | Sonnet 4.6 | Summarizes regulations, maps applicability |
| AGENT-25 | Module 26: Universal Asset Q&A | Sonnet 4.6 | RAG scoped to a single asset |
| AGENT-26 | Module 27: Claude Code Accelerator | Opus 4.7 | Generates code, IaC, reviews existing code |

Note: Module 9 (Chat) is AGENT-01 (Layer 1, orchestrator). Module 15 is merged into Module 24.

### 6.4 Layer 3 - Task Workers (sparse, only for modules that benefit from decomposition)

| Worker ID | Parent Module | Role |
|---|---|---|
| WORKER-01 | Module 1 | question_picker (chooses next adaptive question) |
| WORKER-02 | Module 1 | scorer (computes stage 0-5 from answers) |
| WORKER-03 | Module 1 | recommender (picks 3-5 assets for the stage) |
| WORKER-04 | Module 4 | regulation_finder (finds applicable regulations) |
| WORKER-05 | Module 4 | checklist_generator (produces actionable checklist) |
| WORKER-06 | Module 14 | narrative_writer (writes report narrative sections) |
| WORKER-07 | Module 14 | benchmark_lookup (pulls peer distribution data) |
| WORKER-08 | Module 21 | bias_analyzer (analyzes data bias risks) |
| WORKER-09 | Module 21 | regulation_mapper (maps to EU AI Act risk tiers, etc.) |
| WORKER-10 | Module 24 | item_classifier (classifies feed items by topic/relevance) |
| WORKER-11 | Module 24 | commentary_writer (writes "what this means" notes) |
| WORKER-12 | Module 25 | reg_summarizer (plain-language regulation summary) |
| WORKER-13 | Module 25 | applicability_checker (maps reg to use case) |
| WORKER-14 | Module 27 | scaffolder (generates folder structure + boilerplate) |
| WORKER-15 | Module 27 | iac_generator (generates Terraform / CDK from arch) |
| WORKER-16 | Module 27 | code_reviewer (reviews code against CoE best practices) |

All workers use Haiku 4.5 except WORKER-14/15/16 (Opus 4.7 for code).

### 6.5 Inter-Agent Routing

```
User → Chat (UI dock)
      ↓
   AGENT-01 (Orchestrator, Sonnet 4.6)
      ↓ (decides via tool: invoke_module)
   AGENT-NN (Module specialist, Haiku 4.5 or Sonnet 4.6 or Opus 4.7)
      ↓ (only if module decomposes work)
   WORKER-NN (Task worker, Haiku 4.5 or Opus 4.7)
      ↓
   Result bubbles back up to Chat, which composes and streams to user
```

Module registry lives at `vault/modules.json`. Chat reads it on every conversation start.

### 6.6 Hard Gates & Deterministic Rules (pre-LLM)

- Password check on every request before any agent is invoked
- Module registry validation: invoke_module fails fast if module_id not in registry
- Per-session token budget: if session exceeds 100K tokens, Chat refuses further invocations until reset
- Daily Opus token cap: Module 27 calls blocked if daily Opus tokens exceed configured limit (cost control)
- Frontmatter schema validation: any markdown file with invalid frontmatter is excluded from embeddings

---

## 7. Data & State

### 7.1 Core Entities

- **VaultFile:** markdown file in S3 with YAML frontmatter (id, type, industry, stage, tags, owner, updated_at). Owned by Knowledge Base.
- **VectorRecord:** embedding + metadata, stored in S3 Vectors index. Written by re-embedding pipeline.
- **Session:** chat conversation state, stored as JSON in S3 under `sessions/{display_name}/{session_id}.json`. Includes message history, invoked agents, citations.
- **Assessment:** completed maturity assessment, stored as `vault/assessments/{display_name}/{timestamp}.md` with frontmatter (score, stage, recommendations).
- **Kit:** generated engagement kit, stored as `vault/kits/{display_name}/{timestamp}/` folder. Zipped on download.
- **DecisionEntry, RetroEntry, EthicsReview, GovernanceReview:** all stored as markdown files in their respective vault folders.
- **ModuleRegistry:** single `vault/modules.json` file listing all 27 modules with metadata.
- **AgentsConfig:** single `vault/agents.md` file controlling Chat orchestrator behavior.
- **UserProfile:** display name + saved items + recent activity, stored as JSON at `users/{display_name}.json` in S3.

### 7.2 Storage Decisions

- **Relational (Postgres):** none in this version. All state is files-on-S3 + JSON.
  - Rationale: simplifies infra; markdown vault pattern fits S3 natively; demo volume does not justify Postgres ops overhead.
  - Post-demo: introduce Aurora Serverless v2 for analytics aggregation, user accounts, multi-tenancy. Captured in post-demo-plan.md.
- **Vector store:** S3 Vectors (one index per content type: assets, decisions, regs, feed, prompts).
- **Embedding model:** Bedrock Titan Embed v2 (1024 dimensions).
- **Cache:** none in this version (cost discipline; demo latency acceptable).
- **Object storage:** single S3 bucket with prefixed folders (`vault/`, `sessions/`, `users/`, `kits/`).
- **Secrets:** AWS Secrets Manager for Bedrock API keys (if needed beyond IAM), Vercel deploy hook tokens. Shared app password in Vercel/Lambda env var (acceptable for demo per scope decision).

### 7.3 State & Session Management

- **Agent state:** Strands Agents holds in-memory state per request; persistent state lives in S3 session files
- **User session:** browser localStorage holds display name + auth flag; no JWT, no refresh tokens (demo-grade)
- **Idempotency:** chat requests use a client-generated request_id; duplicate request_ids return cached response from session file

---

## 8. Integrations & External APIs

### 8.1 In Scope (demo)

#### INT-01: AWS Bedrock

- **Purpose:** All LLM inference (Sonnet 4.6, Haiku 4.5, Opus 4.7, Titan Embed v2)
- **Auth:** IAM role
- **Endpoints used:** InvokeModel, InvokeModelWithResponseStream
- **Trigger direction:** we call Bedrock
- **Rate limits:** Bedrock account quotas; demo volume far below
- **Error handling:** exponential backoff on throttling; on persistent failure, return user-visible error
- **Secrets location:** none (IAM role)

#### INT-02: S3 (Knowledge Base + sessions + users + kits)

- **Purpose:** primary content storage
- **Auth:** IAM role
- **Endpoints used:** GetObject, PutObject, ListObjectsV2, DeleteObject, GetObjectAttributes
- **Trigger direction:** we call S3; S3 EventBridge triggers re-embedding Lambda on file change
- **Rate limits:** S3 default request rate; far below for demo
- **Error handling:** retry on transient 5xx
- **Secrets location:** none (IAM role)

#### INT-03: S3 Vectors

- **Purpose:** vector storage + similarity search
- **Auth:** IAM role
- **Endpoints used:** PutVectors, QueryVectors, DeleteVectors
- **Trigger direction:** we call S3 Vectors
- **Rate limits:** service default
- **Error handling:** retry on transient errors
- **Secrets location:** none

### 8.2 Out of Scope (deferred to post-demo)

- RSS feed ingestion (Module 24)
- arXiv polling (Module 24)
- Regulatory database APIs (Module 25)
- News APIs (Module 24)
- LinkedIn integration for certification export (Module 20)
- SharePoint, Salesforce, project management tools (north-star Open Questions)

### 8.3 MCP Servers

- Context7, AWS Docs, Strands Agents docs recommended at implementation time (per template MCP pre-flight). Not part of runtime.

---

## 9. Non-Functional Requirements

### 9.1 Performance

- **NFR-001:** Chat first-token latency p95 < 3 seconds.
- **NFR-002:** Asset Library page load (LCP) < 3 seconds.
- **NFR-003:** Module page navigation < 1 second after initial app load.
- **NFR-004:** Re-embedding latency: new vault file searchable within 60 seconds of upload.

### 9.2 Scale & Volume (demo)

- **Expected volume at launch:** 1-2 concurrent users, ~50-100 chat turns per day, ~20-30 module agent invocations per day.
- **Expected volume at 12 months:** same (this is exploration, not production rollout).
- **Hard ceiling assumption:** 10 concurrent users. Above this, post-demo scale work is required.

### 9.3 Availability & SLA

- **Target uptime:** best-effort. No formal SLA.
- **Critical user journeys:** none classified as critical (demo-only).

### 9.4 Disaster Recovery

- **RTO:** 24 hours (rebuild from IaC + S3 snapshot)
- **RPO:** 24 hours (daily S3 snapshot to a backup bucket)
- **Backup strategy:** S3 versioning enabled on the Knowledge Base bucket; daily lifecycle snapshot.
- **Failover scope:** none (single AZ, single region)

### 9.5 Other NFRs

- **NFR-005:** Monthly cloud cost ceiling: $50/month at demo usage. Hard alert at $30/month.
- **NFR-006:** Per-Opus-call cost ceiling: $1.00 per invocation (Module 27); daily Opus token cap enforced.
- **Accessibility:** not formally targeted for demo.
- **i18n / locale:** English only.

---

## 10. Security, Compliance & Guardrails

### 10.1 Compliance Posture

- **Frameworks in scope:** none formally targeted (demo-only, no real client data).
- **Data classification:** internal/demo only. No regulated data.
- **PII handling:** no real PII in vault. Demo content references PII-handling regulations but contains no actual PII.

### 10.2 Auth & Authorization

- **AuthN:** single shared password (env var) + display name (localStorage). Per Q1 decision.
- **AuthZ model:** no row-level isolation. All users see all content. Demo-grade.
- **Tenancy:** single-tenant (single instance, one user at a time effectively).
- **Post-demo plan:** Cognito email signup with per-user content isolation. Captured in post-demo-plan.md.

### 10.3 LLM / Agent Guardrails

- **Prompt injection defense:** input length cap (10K chars), system prompts use explicit role boundaries, no system prompt leakage in tool error messages.
- **Output validation:** every agent returns Pydantic-validated output; retry once on schema failure; fall back to safe default on second failure.
- **PII redaction:** not implemented in this version (no real PII in vault). Hook present for post-demo enablement.
- **Bedrock Guardrails:** one default guardrail policy (PII detection, prompt attack detection) applied to AGENT-01 only. Not applied to other agents to keep cost down for demo; full coverage post-demo.
- **Cost controls:** per-session token cap (100K), daily Opus token cap configurable, per-module daily invocation cap.

### 10.4 Secrets & Key Management

- **Storage:** AWS Secrets Manager for any non-IAM secret. Env vars for app password and feature flags.
- **Rotation policy:** none (demo).
- **Access:** Lambda execution role + Vercel deploy token. Minimal IAM policies per service.

---

## 11. Observability & Evals

### 11.1 Logging

- **What we log:** every chat turn (request_id, session_id, display_name_hash, user_message, invoked_module_id, latency_ms, tokens_in, tokens_out, model, cost_estimate). Tool calls logged separately.
- **PII handling in logs:** display name hashed (SHA-256). User message content logged as-is for demo debugging; post-demo: scrubbing pass.
- **Retention:** 30 days in CloudWatch.

### 11.2 Metrics

- **Business:** chat turns per day, module invocations per module per day, average session length.
- **System:** p50/p95 first-token latency, agent invocation count per agent, error rate, daily Bedrock cost.

### 11.3 Tracing

- **Tool:** CloudWatch + Bedrock model invocation logs. OpenTelemetry deferred to post-demo.
- **Trace scope:** per chat turn, per agent invocation, per tool call.

### 11.4 LLM Evals

- **Offline eval set:** 30 hand-picked Q&A pairs (5 per major workflow: chat retrieval, assessment, kit, governance, compliance, ethics). Seeded.
- **Eval cadence:** manual, pre-demo. No CI gate for demo.
- **Quality metrics:** accuracy (judged by developer), citation correctness, latency, cost per task.
- **Regression gate:** none for demo (manual review only). Post-demo: pre-deploy CI gate.

### 11.5 Alerting

- **Critical:** daily Bedrock cost > $5 → email to developer.
- **Warning:** chat error rate > 5% over 1 hour → email.
- **No paging / on-call** (demo).

---

## 12. Tech Stack (confirmed)

### 12.1 Languages & Frameworks

- **Backend / Agents:** Python 3.12, AWS Strands Agents (latest stable), Pydantic v2
- **Backend API:** Next.js 16 server actions + a small FastAPI service for agent execution if Strands cold-start latency on Lambda is problematic (decided at design time)
- **Frontend:** Next.js 16 (App Router) + Tailwind CSS + shadcn/ui
- **IaC:** AWS CDK (Python)

### 12.2 LLM Providers & Models

- **Primary:** AWS Bedrock
  - Claude Sonnet 4.6 (`claude-sonnet-4-6`) - default reasoning model for orchestrator and most module agents
  - Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) - cheap path for retrieval, classification, summary
  - Claude Opus 4.7 (`claude-opus-4-7`) - Module 27 code generation only
- **Embedding model:** Bedrock Titan Embed v2 (1024 dimensions)

### 12.3 Data Layer

- **Primary content store:** S3 (one bucket, prefixed folders)
- **Vector store:** S3 Vectors
- **No relational DB in demo**

### 12.4 Cloud Services Used

- AWS Bedrock: LLM inference
- S3: content + sessions + users + kits + vault
- S3 Vectors: vector storage and search
- Lambda: agent execution runtime, re-embedding pipeline
- API Gateway: HTTP entry for backend (if separated from Next.js server actions)
- EventBridge: S3 file-change events → re-embedding Lambda
- Secrets Manager: any non-env secrets
- CloudWatch: logs, metrics, alarms
- Vercel: Next.js hosting (free tier)

### 12.5 Dev Tooling

- **Package manager:** uv (Python), pnpm (JS)
- **Test framework:** pytest (Python), vitest (JS)
- **Linter/formatter:** ruff (Python), eslint + prettier (JS)
- **Type checking:** pyright (Python), tsc (JS)

---

## 13. Infrastructure & Deployment

### 13.1 Environments

- **Dev:** local Next.js + local Strands agents calling real Bedrock. Local S3 mock (LocalStack optional, real S3 dev bucket preferred).
- **Demo:** Vercel (Next.js) + AWS (everything else) in us-east-1, single environment.
- **No staging, no prod** (demo only).

### 13.2 IaC

- **Tool:** AWS CDK (Python)
- **Module organization:** per-service stacks (`storage`, `agents`, `compute`, `events`, `monitoring`)

### 13.3 CI/CD

- **Platform:** GitHub Actions
- **Pipeline:** push → lint → tests → CDK synth → CDK deploy (manual approval) → Vercel deploy (auto from main)
- **Deploy strategy:** in-place updates (no blue-green for demo)

### 13.4 Region & Network

- **Primary region:** us-east-1 (Bedrock model availability + S3 Vectors)
- **Multi-region:** no
- **VPC:** none (Lambda runs in default no-VPC mode for cost)

---

## 14. Business Model & GTM

Skipped. This is an exploration build to determine fit. GTM thinking captured separately if a target prospect engages.

---

## 15. Phasing & Milestones

Build sequence: 7 waves, all 27 modules. Each wave produces a demoable slice. Modules within a wave can be built in any order; waves are sequential.

### 15.1 Wave 1 - Foundation (target: 2 weeks solo)

- **Goal:** User can log in, browse the Asset Library, chat about vault contents.
- **Includes:** Knowledge Base substrate, Module 2 (Asset Library), Module 9 (Chat orchestrator basic), Module 17 (Personal Dashboard)
- **Covers FRs:** 001-015
- **Covers agents:** AGENT-01, AGENT-03, AGENT-16

### 15.2 Wave 2 - Assessment & Delivery (target: 1.5 weeks)

- **Goal:** User can complete a maturity assessment, build an engagement kit, chat with any asset.
- **Includes:** Module 1, 3, 26
- **Covers FRs:** 016-024
- **Covers agents:** AGENT-02, AGENT-04, AGENT-25; WORKER-01, 02, 03

### 15.3 Wave 3 - Risk & Governance (target: 1.5 weeks)

- **Goal:** User can run a full pre-delivery risk pass.
- **Includes:** Module 4, 21, 25
- **Covers FRs:** 025-031
- **Covers agents:** AGENT-05, 20, 24; WORKER-04, 05, 08, 09, 12, 13

### 15.4 Wave 4 - Specialized Tools (target: 2 weeks)

- **Goal:** Technical-depth surfaces (tools, vendors, prompts, Q&A).
- **Includes:** Module 7, 8, 11, 13
- **Covers FRs:** 032-041
- **Covers agents:** AGENT-08, 09, 11, 13

### 15.5 Wave 5 - Intelligence & Insight (target: 2 weeks)

- **Goal:** Feed + ideation + decisions + project health + retros + benchmarks.
- **Includes:** Module 12, 16, 18, 19, 22, 24
- **Covers FRs:** 042-057
- **Covers agents:** AGENT-12, 15, 17, 18, 21, 23; WORKER-10, 11

### 15.6 Wave 6 - Client-Facing & People (target: 2 weeks)

- **Goal:** Client reports, community, contributions, onboarding, certification, analytics.
- **Includes:** Module 5, 6, 10, 14, 20, 23
- **Covers FRs:** 058-073
- **Covers agents:** AGENT-06, 07, 10, 14, 19, 22; WORKER-06, 07

### 15.7 Wave 7 - Development Accelerator (target: 1.5 weeks)

- **Goal:** Code generation from reference architectures.
- **Includes:** Module 27
- **Covers FRs:** 074-077
- **Covers agents:** AGENT-26; WORKER-14, 15, 16

**Estimated total: 12-13 weeks solo, full-time.** Stretch on integration/polish.

---

## 16. Acceptance Criteria / Definition of Done

Project-level DoD (every wave must pass these before being called done):

- [ ] All FRs in the wave have at least smoke tests passing
- [ ] All agents in the wave return valid Pydantic schemas
- [ ] Module pages render with seeded demo data
- [ ] Chat can describe + invoke every module in the wave
- [ ] Logs present for every agent invocation
- [ ] Daily cost under budget for the wave
- [ ] One demo recording walking through the wave's added flows

Per-wave additional DoD lives in plan.md.

---

## 17. Open Questions & Risks Register

### 17.1 Open Questions

- **Q-01:** Strands Agents cold-start latency on Lambda for the Chat orchestrator. If first-token p95 exceeds 3s due to cold start, do we move orchestrator to Fargate (warmer) or accept latency? Decide at design time.
  - Owner: developer | Needed by: Wave 1 start
- **Q-02:** Module registry format: single modules.json or one .md per module with frontmatter aggregated?
  - Owner: developer | Needed by: Wave 1 start
- **Q-03:** Seed content sourcing. Where do the ~20-30 initial vault files come from (hand-authored, synthesized from public references, mix)?
  - Owner: developer | Needed by: Wave 1 start
- **Q-04:** Compliance/regulation seed data scope. Confirmed: fintech + healthcare + general PII. How many entries per category for demo?
  - Owner: developer | Needed by: Wave 3 start
- **Q-05:** Module 27 Opus daily cap. What absolute dollar value before blocking calls?
  - Owner: developer | Needed by: Wave 7 start

### 17.2 Risks

- **RISK-01:** Pain is unvalidated. The entire premise is based on assumption, not consultant interviews. Even a great build may discover the problem does not resonate.
  - Likelihood: medium | Impact: high
  - Mitigation: build the demo, then interview prospects. Pivot scope based on response. Captured as a post-demo plan action.

- **RISK-02:** Solo developer scope. 27 modules in ~12 weeks is aggressive.
  - Likelihood: high | Impact: medium
  - Mitigation: wave-based delivery means every 1.5-2 weeks produces a demoable slice. Can stop after Wave 3 and have a coherent demo if needed.

- **RISK-03:** S3 Vectors is a recent service. SDK stability, feature gaps, and best practices are still emerging.
  - Likelihood: medium | Impact: medium
  - Mitigation: verify against AWS Docs MCP at design time; have a fallback (Bedrock Knowledge Bases) ready.

- **RISK-04:** Minimal security is intentional but creates a hard "do not expose publicly" constraint.
  - Likelihood: high | Impact: medium (only if violated)
  - Mitigation: Vercel password protection at the platform level + app-level password gate. No public DNS for AWS resources. Acknowledged in deploy runbook.

- **RISK-05:** Cost overrun from heavy Opus use in Module 27.
  - Likelihood: medium | Impact: medium
  - Mitigation: daily Opus token cap; hard alert at $30/month; option to demo Module 27 with cached prior generations rather than live generation.

- **RISK-06:** Strands Agents framework maturity. Strands is recent; hierarchical 3-layer pattern may surface edge cases.
  - Likelihood: medium | Impact: medium
  - Mitigation: validate against Strands docs MCP at design time; have a manual orchestration fallback (direct tool invocation from Chat without intermediate agents).

- **RISK-07:** Embeddings cost. Re-embedding 30+ files on every change adds Titan Embed v2 cost.
  - Likelihood: low | Impact: low
  - Mitigation: embed only changed files (hash-based dedup); demo content is small.

---

## 18. References & Inspiration

- **North-star vision:** `docs/starters/AI CoE Platform Brief.md` (27-module roadmap, authoritative)
- **Karpathy LLM wiki pattern:** markdown vault + agent over vault (April 2026 pattern)
- **AWS Strands Agents:** hierarchical multi-agent framework
- **AWS Bedrock:** Claude Sonnet 4.6, Haiku 4.5, Opus 4.7, Titan Embed v2
- **Post-demo enhancement plan:** `ai_docs/post-demo-plan.md` (companion to this brief)

---

*End of brief. Next step: feed this file plus `docs/templates/02a_generate_system_design.md` into a Claude Code session to produce `ai_docs/design.md`, then `02_generate_implementation_plan.md` to produce `ai_docs/plan.md`.*
