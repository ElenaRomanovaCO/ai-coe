# Post-Demo Enhancement Plan

> Generated: 2026-06-03
> Companion to: `ai_docs/brief.md`
> Purpose: Track every feature, capability, and operational concern that was intentionally downscoped or deferred for the demo build. When the demo lands a real prospect and the platform moves toward production, these are the upgrades that turn it from "show me" into "use me."

---

## How to read this document

- Each item names the trigger that moves it from "deferred" to "active work."
- Items are grouped by theme, not by priority.
- Effort estimates are solo-developer rough cuts.
- Anything new that surfaces during the build (not captured here) gets appended to Section 8.

---

## 1. Identity & Auth

### 1.1 Migrate from shared password to Cognito (per Q1 decision)

- **Current state (demo):** Single shared password in env var + display name in browser localStorage. No real identity.
- **Trigger:** A prospect says they want to use the platform with their team.
- **Upgrade plan:**
  - Add Amazon Cognito User Pool with email signup + verification
  - Replace password gate middleware with Cognito JWT verification in Next.js middleware
  - Migrate session storage from localStorage to Cognito-issued tokens
  - Add per-user content scoping: assessments, kits, decisions, retros tagged by `cognito_sub`
  - Add row-level isolation: users only see their own assessments, saved items, retros (Asset Library, Compliance Tracker, etc. stay shared)
  - Add password reset, email verification, MFA optional
- **Effort:** ~1 week solo
- **Risk:** Cognito JWT verification in Next.js middleware requires care around edge runtime constraints
- **Dependencies:** none

### 1.2 Per-user data isolation in S3

- **Current state (demo):** All vault content and session files visible to anyone with the shared password
- **Trigger:** moves with Cognito migration above
- **Upgrade plan:**
  - Re-key S3 session paths: `sessions/{cognito_sub}/{session_id}.json` (replace `display_name` with `cognito_sub`)
  - Add S3 bucket policy + IAM conditions enforcing per-user prefix access
  - Migrate existing files (one-time script)
- **Effort:** ~2 days
- **Dependencies:** Cognito migration

### 1.3 Roles & permissions model

- **Current state (demo):** No roles. Everyone is effectively an admin.
- **Trigger:** multi-tenant or multi-team usage
- **Upgrade plan:**
  - Define roles: Consultant, CoE Lead / Curator, Practice Lead, Client Stakeholder (read-only)
  - Implement RBAC with Cognito groups
  - Gate curator-only routes (Knowledge Contribution approval, Analytics Dashboard)
  - Gate leadership routes (Analytics Dashboard, Certification team capability map)
- **Effort:** ~3-4 days
- **Dependencies:** Cognito migration

---

## 2. Client-Facing Surfaces (per Q2 decision)

### 2.1 Module 14: shareable signed-URL report portal

- **Current state (demo):** PDF download only. Consultant downloads and shares externally.
- **Trigger:** prospect wants to share a maturity report with their client without forcing the client to sign up.
- **Upgrade plan:**
  - Add S3-hosted static report renderer (HTML output, not PDF)
  - Generate CloudFront signed URLs with configurable expiry (7 days default)
  - Add a Reports Dashboard view for consultants to manage active links (revoke, regenerate)
  - Add view-only watermark + analytics (link opens, time-on-page)
  - Optional: gated access via one-time email code for higher-trust sharing
- **Effort:** ~1 week
- **Dependencies:** none (S3 + CloudFront only)

### 2.2 Branded report templates

- **Current state (demo):** Generic styling, no brand customization.
- **Trigger:** real productization with multiple firm tenants
- **Upgrade plan:**
  - Tenant-level brand config (logo, colors, typography)
  - Report template variants by industry
  - White-label option for firm-specific deployments
- **Effort:** ~1 week
- **Dependencies:** multi-tenancy

---

## 3. External Data Ingestion (per Q3 decision)

### 3.1 Module 24: real Intelligence Feed ingestion

- **Current state (demo):** Seeded with curated content covering fintech, healthcare, PII themes. No live ingestion.
- **Trigger:** moving from demo to "actually useful daily" usage
- **Upgrade plan:**
  - EventBridge Scheduler (cron: every 6 hours) triggers an ingestion Lambda
  - Ingestion Lambda fans out to per-source workers:
    - RSS parser (OpenAI blog, Anthropic news, Google AI blog, AWS ML blog, vendor changelogs)
    - arXiv parser (cs.AI, cs.CL categories, last 24h)
    - News API client (configurable AI-related queries)
  - Each item passes through:
    - Dedup (URL hash + content hash)
    - Classifier (WORKER-10, already built) for topic + relevance
    - Commentary writer (WORKER-11, already built) for "what this means" notes
  - Items land in `vault/intelligence-feed/{yyyy-mm-dd}/{item_id}.md`
  - Re-embedding pipeline picks them up automatically
- **Effort:** ~1.5 weeks (mostly per-source parser work + dedup logic)
- **Dependencies:** none. The agents (WORKER-10, WORKER-11) are already built in demo.
- **Cost impact:** ongoing. Estimate $50-100/month at moderate ingestion volume (depends on commentary frequency).

### 3.2 Module 25: real regulation tracking

- **Current state (demo):** Seeded with curated regulations (EU AI Act, HIPAA AI guidance, NIST AI RMF, state-level US bills) focused on fintech, healthcare, PII.
- **Trigger:** real consulting work where regulatory currency matters
- **Upgrade plan:**
  - Identify authoritative sources per regulation family:
    - EU AI Act: EUR-Lex official journal
    - US federal: NIST publications, federal register
    - US state: state legislative trackers (varies)
    - Healthcare: FDA AI/ML guidance updates
    - Financial: SEC, FFIEC publication feeds
  - Build per-source crawlers (or use legal-tech APIs where available, e.g. Lex Machina, Bloomberg Law)
  - Use existing WORKER-12 (reg_summarizer) and WORKER-13 (applicability_checker) to process new entries
  - Add change detection: alert when an existing regulation's status changes
  - Add subscriber alerts: users with active engagements in matching geography/industry get notified
- **Effort:** ~2-3 weeks (legal sources vary in accessibility)
- **Dependencies:** none. WORKER-12, WORKER-13 already built.
- **Risk:** legal source TOS may restrict automated crawling. Consider partnering with a legal-tech provider.

### 3.3 Module 20: LinkedIn certification export

- **Current state (demo):** Badges visible only inside the platform.
- **Trigger:** demand for shareable external credentials
- **Upgrade plan:**
  - LinkedIn OAuth integration
  - Map platform certifications to LinkedIn Skills + Licenses & Certifications
  - One-click export with auto-formatted credential page
- **Effort:** ~3 days

---

## 4. Production Readiness (SLA, Resilience, DR)

### 4.1 Multi-AZ + automated failover

- **Current state (demo):** single AZ, no failover
- **Trigger:** production SLA commitment
- **Upgrade plan:**
  - All Lambdas to multi-AZ by default (already the case for Lambda; verify VPC configs)
  - S3 cross-region replication for the Knowledge Base bucket
  - S3 Vectors: replicate the vector index (manual re-embed in DR region as backup)
  - Add a us-west-2 DR stack via CDK (parameterized region)
  - Vercel: configure custom domain with failover DNS
- **Effort:** ~1 week
- **Dependencies:** none

### 4.2 Real DR drills

- **Trigger:** SOC 2 audit prep or production commitment
- **Upgrade plan:**
  - Quarterly DR drill: simulate region failure, verify RTO (target: 1 hour) and RPO (target: 1 hour)
  - Runbook for every top-5 failure mode
  - Tabletop exercise documentation
- **Effort:** ~2 days per drill, ongoing

### 4.3 Real monitoring + paging

- **Current state (demo):** CloudWatch logs + email alerts on cost
- **Trigger:** production commitment
- **Upgrade plan:**
  - PagerDuty (or Opsgenie) integration for critical alerts
  - SLO dashboards (CloudWatch + Grafana or Datadog)
  - Error budget tracking per module
  - On-call rotation if/when team exists
- **Effort:** ~1 week initial setup

---

## 5. Security Hardening

### 5.1 Bedrock Guardrails on all agents

- **Current state (demo):** Guardrails on AGENT-01 only
- **Trigger:** any handling of real client data
- **Upgrade plan:**
  - Apply default guardrail policy to all 26 module agents + 16 task workers
  - Per-agent customization: tighter content filters on client-facing outputs (Module 14, 22)
  - Sensitive info filters specifically enabled on Knowledge Contribution flow (Module 5)
- **Effort:** ~2 days
- **Cost impact:** ~5-10% increase in Bedrock costs

### 5.2 PII redaction pre-LLM

- **Current state (demo):** Hook present, not implemented
- **Trigger:** any real client data flowing through
- **Upgrade plan:**
  - Add Amazon Comprehend PII detection on every user message before LLM call
  - Redact detected PII inline with `[REDACTED:TYPE]` markers
  - Log redaction events without the underlying PII
  - Optional: allow per-user opt-out for testing
- **Effort:** ~3 days

### 5.3 Secrets rotation

- **Current state (demo):** no rotation
- **Trigger:** SOC 2 prep
- **Upgrade plan:**
  - Secrets Manager rotation policies (90-day default)
  - Re-issue app-level tokens on rotation
- **Effort:** ~1 day

### 5.4 VPC isolation

- **Current state (demo):** Lambdas in default no-VPC (lowest cost)
- **Trigger:** regulated workload or enterprise customer requirement
- **Upgrade plan:**
  - Move Lambdas into a private VPC subnet
  - VPC endpoints for S3, Bedrock, S3 Vectors, Secrets Manager
  - NAT Gateway for outbound (or use VPC endpoints exclusively)
- **Effort:** ~3 days
- **Cost impact:** ~$50-100/month for NAT Gateway, less if VPC endpoints suffice

### 5.5 Audit logging

- **Trigger:** SOC 2 / HIPAA / enterprise
- **Upgrade plan:**
  - CloudTrail enabled across all accounts
  - Per-user action audit log in DynamoDB
  - Immutable log storage (S3 Object Lock)
  - User-accessible "my activity" view
- **Effort:** ~1 week

---

## 6. Scale & Performance

### 6.1 Caching layer

- **Current state (demo):** no cache
- **Trigger:** sustained >100 users or p95 latency degradation
- **Upgrade plan:**
  - ElastiCache (Redis) for hot reads: module registry, asset list views, frequent searches
  - In-Lambda LRU cache for agent system prompts and frequently-invoked tools
  - CloudFront caching on static Asset Library pages
- **Effort:** ~3-4 days

### 6.2 Database for analytics & search

- **Current state (demo):** JSON files in S3 for everything
- **Trigger:** complex analytics queries (Module 10) start to feel slow with file-based aggregation
- **Upgrade plan:**
  - Add Aurora Serverless v2 (Postgres) for:
    - Analytics aggregation (Module 10)
    - User accounts (with Cognito sync)
    - Cross-tenant queries
    - Audit log
  - Keep markdown vault on S3 (source of truth for content)
  - Add a projection engine (Lambda) that syncs vault frontmatter → Aurora for fast filtering
- **Effort:** ~1.5 weeks

### 6.3 Strands Agents on Fargate

- **Current state (demo):** Lambda. If cold-start hurts latency, this is the migration.
- **Trigger:** p95 first-token consistently > 3s due to cold start
- **Upgrade plan:**
  - Move Chat orchestrator (AGENT-01) to Fargate with warm instance pool
  - Keep module agents on Lambda (cold start acceptable for non-Chat surfaces)
  - Use Provisioned Concurrency on Lambda as a cheaper alternative if Fargate cost is too high
- **Effort:** ~3-4 days

### 6.4 Embedding optimization

- **Current state (demo):** re-embed full file on any change
- **Trigger:** vault grows past ~1000 files
- **Upgrade plan:**
  - Chunked embedding with stable chunk IDs
  - Diff-based re-embed (only embed changed chunks)
  - Per-section embeddings for long documents
- **Effort:** ~3-4 days

---

## 7. Multi-Tenancy & Productization

### 7.1 True multi-tenancy

- **Current state (demo):** single tenant, shared instance
- **Trigger:** first paying customer wants their own data scope
- **Upgrade plan:**
  - Tenant-per-prefix in S3 (cheap, scales to ~100 tenants)
  - Cognito user pool per tenant OR app client per tenant within shared pool
  - Tenant-aware IAM policies
  - Tenant config: brand, default content, feature flags
- **Effort:** ~2 weeks

### 7.2 Per-tenant cost controls

- **Trigger:** multi-tenancy
- **Upgrade plan:**
  - Per-tenant token budget enforcement (already designed as a hook in demo)
  - Per-tenant invocation caps per module
  - Billing-grade usage tracking
- **Effort:** ~1 week

### 7.3 Admin / curator console

- **Trigger:** non-developer curators need to manage the vault
- **Upgrade plan:**
  - Web UI for vault file editing with frontmatter validation
  - Bulk import (CSV → markdown)
  - Tag taxonomy management
  - Contribution review queue UI (Module 5 currently uses raw S3 flow)
- **Effort:** ~1.5 weeks

---

## 8. Observability & Evals

### 8.1 LLM eval CI gate

- **Current state (demo):** manual review only
- **Trigger:** any production deploy commitment
- **Upgrade plan:**
  - Build eval harness (e.g. ragas, custom)
  - Eval set grows from 30 demo pairs to 200+ real pairs (one per FR)
  - Pre-deploy gate in CI: deploy blocked if eval scores drop below baseline
- **Effort:** ~1 week initial

### 8.2 OpenTelemetry tracing

- **Trigger:** multi-service architecture or production debugging needs
- **Upgrade plan:**
  - OTel instrumentation across Next.js, Lambda, Strands agents
  - Trace export to AWS X-Ray or Honeycomb
- **Effort:** ~3-4 days

### 8.3 Per-module dashboards

- **Trigger:** want to know which modules actually get used
- **Upgrade plan:**
  - Per-module usage dashboard (already partially built as Module 10)
  - Per-agent token cost tracking
  - Cohort retention analysis
- **Effort:** ~3 days

---

## 9. Pain Validation (the most important post-demo item)

### 9.1 Prospect interviews

- **Trigger:** demo build is functional and recordable
- **Action plan:**
  - Identify 5-10 contacts at AI-focused IT consulting firms
  - 30-minute interviews structured as:
    - 5 min: their current AI engagement workflow
    - 10 min: walk through demo (recorded)
    - 10 min: which modules resonated, which didn't, what's missing
    - 5 min: would they actually use this, what would block adoption
  - Synthesize findings into a "what to keep, what to cut, what to add" doc
- **Effort:** ongoing, 2-4 weeks elapsed
- **Outcome:** scope decision for v2 (productization or pivot)

### 9.2 Pivot decision

- **Trigger:** prospect interviews complete
- **Decision points:**
  - If 3+ prospects say "I'd use this": move toward productization (this whole plan kicks in)
  - If 1-2 prospects: narrow scope to the resonant modules, rebuild with those
  - If 0 prospects: archive the project as a learning artifact, no further investment

---

## 10. Newly Discovered Items (append during build)

Track items that surface during implementation that were not in the original brief.

- (none yet)

---

## 11. References

- **Source brief:** `ai_docs/brief.md`
- **North-star vision:** `docs/starters/AI CoE Platform Brief.md`
