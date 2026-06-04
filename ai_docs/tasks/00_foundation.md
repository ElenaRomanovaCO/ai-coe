# Task: Foundation (Phase 0 — Substrate for all subsequent work)

> **Phase:** 0
> **Feature group:** Foundation
> **Covers:** FR-001 (password gate), FR-004 (auto-embed), FR-005 (agents.md), plus all cross-cutting setup
> **Depends on:** none
> **Blocks:** every other task file in this suite
> **Estimated effort:** 4-6 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

> *Use this if your Claude Code session already has `ai_docs/brief.md` and `ai_docs/design.md` in context.*

**Goal:** Stand up every shared substrate piece (AWS account prep, CDK app, S3, IAM, Vercel + AWS OIDC, password gate, re-embed pipeline, observability, CI/CD, devex) so that subsequent wave tasks can focus on module-specific work only.

**Build steps:**

1. **AWS account prep** → Verify: `aws bedrock list-foundation-models --region us-east-1` returns Claude Sonnet 4.6, Haiku 4.5, Opus 4.7, Titan Embed v2 with `inferenceTypesSupported` including `ON_DEMAND`.
2. **CDK Python project bootstrap** (`infra/`) → Verify: `cdk synth` succeeds with empty stacks.
3. **Storage stack** (S3 vault bucket + S3 sessions bucket + S3 Vectors index) → Verify: `aws s3 ls` shows buckets; `aws s3vectors list-indexes` shows index.
4. **IAM stack** (5 roles: Fargate orchestrator, ModuleAgents Lambda, Workers Lambda, ReEmbed Lambda, Vercel-OIDC) → Verify: roles created; `aws iam get-role` returns expected trust policy for each.
5. **ReEmbed Lambda + EventBridge wiring** → Verify: drop a test .md into vault bucket, `aws s3vectors query-vectors` returns the file content within 60s.
6. **modules.json schema + initial file** → Verify: Pydantic loader validates the seeded `vault/modules.json` (empty `modules: []` is valid).
7. **agents.md initial file** → Verify: file exists at `vault/agents.md` with a minimal "you are the Chat orchestrator" outline.
8. **Bedrock Guardrails policy** (PII + prompt attack) → Verify: `aws bedrock get-guardrail --guardrail-identifier {id}` returns ACTIVE.
9. **Next.js 16 project bootstrap** (`web/`) + Tailwind + shadcn/ui → Verify: `pnpm dev` boots and lands on a placeholder authenticated dashboard route.
10. **Password gate middleware + localStorage display_name flow** → Verify: wrong password blocks all routes; correct password + display name persists across reloads.
11. **Vercel-AWS OIDC federation** → Verify: Vercel preview deploy can call `lambda:Invoke` on a no-op test Lambda using IAM role assumed via OIDC, no static AWS keys in Vercel env.
12. **CI/CD pipeline** (GitHub Actions: lint, test, CDK synth, CDK deploy with manual approval, Vercel auto-deploy) → Verify: PR triggers full lint+test+synth; merging to main triggers deploy.
13. **Observability conventions** (structured log schema, metric names, CloudWatch log groups per service, alarm: daily cost > $5) → Verify: a manual Lambda invoke emits a log line with the required JSON shape and a CloudWatch metric counter increments.
14. **Daily Opus cost cap mechanism** (S3-backed counter at `usage/{yyyy-mm-dd}/opus.json`) → Verify: cap library reads + increments correctly; second call after cap hit raises CapExceeded.
15. **Shared Python agents lib** (`agents/lib/`, base agent class, common tools, model client wrappers) → Verify: `pytest agents/lib/tests/` passes with stub coverage.

**Files to create/edit:**

- `infra/app.py` — CDK app entry
- `infra/stacks/storage.py` — vault bucket, sessions bucket, S3 Vectors index
- `infra/stacks/iam.py` — 5 IAM roles + policies
- `infra/stacks/events.py` — EventBridge rule + ReEmbed Lambda
- `infra/stacks/observability.py` — log groups, metric filters, alarms
- `infra/stacks/guardrails.py` — Bedrock guardrail policy
- `infra/cdk.json` — CDK config
- `infra/requirements.txt` — CDK dependencies
- `agents/lib/base_agent.py` — Strands base agent
- `agents/lib/bedrock_client.py` — Bedrock wrapper with cost tracking
- `agents/lib/cost_cap.py` — daily Opus cap (S3-backed)
- `agents/lib/logging.py` — structured log helper
- `agents/lib/models.py` — model ID constants (sonnet_4_6, haiku_4_5, opus_4_7, titan_embed_v2)
- `agents/lib/tests/test_base_agent.py` — base tests
- `agents/lambdas/reembed/handler.py` — ReEmbed Lambda code
- `agents/lambdas/reembed/chunker.py` — heading-aware chunking
- `web/middleware.ts` — password gate
- `web/app/layout.tsx` — root layout with auth context
- `web/app/login/page.tsx` — password entry + display name
- `web/app/(authenticated)/dashboard/page.tsx` — placeholder dashboard
- `web/lib/auth.ts` — localStorage helpers
- `web/lib/aws.ts` — IAM-signed Lambda invoke helper
- `vault/agents.md` — initial orchestrator config
- `vault/modules.json` — initial empty module registry
- `vault/_schema/modules.schema.json` — JSON schema for modules.json
- `.github/workflows/ci.yml` — lint + test + synth
- `.github/workflows/deploy-dev.yml` — manual-trigger CDK deploy
- `.github/workflows/deploy-vercel.yml` — Vercel deploy on main
- `pyproject.toml` — Python dependencies (uv)
- `web/package.json` — Next.js + Tailwind + shadcn deps
- `README.md` — local dev + deploy runbook

**Done when:**

- [ ] FR-001 verified end-to-end (password gate works; display name persists)
- [ ] FR-004 verified end-to-end (file change → embedded within 60s)
- [ ] FR-005 verified (editing agents.md affects next chat turn — verified later in task 02; here we only verify the file is read at startup and reload happens on a configurable interval)
- [ ] All 5 IAM roles created with least-privilege policies
- [ ] CDK can `synth` + `deploy` to a dev AWS account
- [ ] Vercel preview deploy reaches a working dashboard placeholder after password entry
- [ ] CI pipeline green on a no-op PR
- [ ] Cost alarm fires on test (manually simulate by adjusting threshold to $0.01)
- [ ] All file paths from "Files to create/edit" exist
- [ ] No secrets in code; all from Secrets Manager or env vars

---

## B. Standalone Prompt (paste into fresh Claude Code session)

> *Copy from `### START STANDALONE PROMPT` to `### END STANDALONE PROMPT` and paste as the first message in a new session.*

### START STANDALONE PROMPT

You are implementing the **Foundation** (Phase 0) of the **AI CoE Platform**, an internal platform for consultants at AI-focused IT consulting firms. This task is the substrate every subsequent module depends on. Build only what is described here. Do not start any module implementation.

#### Project context (essential, do not skip)

- **What the project does:** A hierarchical multi-agent platform (Chat orchestrator + 26 module agents + 16 task workers) over a markdown knowledge base on S3. Covers 27 functional modules including AI maturity assessment, engagement kit building, governance/risk checking, compliance tracking, intelligence feed, code generation, and 21 more. Solo developer build, demo-grade. Generic naming throughout, no company names anywhere.
- **Project type:** agentic-ai-multi-agent (3-layer hierarchical)
- **Tech stack:**
  - Backend / Agents: Python 3.12, AWS Strands Agents, Pydantic v2
  - Agent runtime: 1 Fargate Spot task (orchestrator) + 2 Lambdas (module agents, task workers) + 1 Lambda (re-embed)
  - Frontend: Next.js 16 (App Router), Tailwind CSS, shadcn/ui, deployed to Vercel
  - LLM: AWS Bedrock (Sonnet 4.6 default, Haiku 4.5 cheap, Opus 4.7 for code only). Embeddings: Titan Embed v2.
  - Content/state: S3 (vault bucket + sessions bucket) + S3 Vectors. No DynamoDB. No Postgres.
  - IaC: AWS CDK (Python). CI/CD: GitHub Actions.
  - Region: us-east-1.

#### What you are building

**Goal (user-facing outcome at end of this task):** A logged-in user can hit a placeholder dashboard. A markdown file dropped into the vault bucket is embedded and searchable within 60 seconds. All cross-cutting infrastructure (IAM, observability, CI/CD, cost guardrails) is in place for subsequent module work.

**Functional requirements covered:**

- **FR-001:** User can enter the app via a single shared password gate and provide a display name stored in browser localStorage.
  - Acceptance: wrong password blocks all routes; correct password + name persists across page reloads.
- **FR-004:** System auto-embeds every markdown file in the S3 Knowledge Base bucket on file change.
  - Acceptance: uploading a new .md file to the vault produces a vector record retrievable within 60 seconds.
- **FR-005:** The agents.md file at the Knowledge Base root controls Chat orchestrator behavior without code redeploy.
  - Acceptance (this task): file exists, schema validated, will be read by the orchestrator (orchestrator itself is built in task 02).

**Architectural decisions in force (from `ai_docs/design.md`):**

- **AD-01:** Hybrid agent runtime. Fargate Spot for orchestrator (warm). One Lambda for all 26 module agents (Strands internal routing). One Lambda for all 16 task workers.
- **AD-02:** Next.js server actions invoke Lambda directly via AWS SDK. No API Gateway. No FastAPI service.
- **AD-03:** Module registry is a single `vault/modules.json` file (structured), validated against a Pydantic schema at load.
- **AD-04:** Session state in S3 JSON files. No DynamoDB. No Postgres.

#### Architecture context (where this task sits)

```
   Browser ─→ Next.js (Vercel) ─→ [password gate middleware]
                                       │
                                       ├─→ (built later: lambda:Invoke to Fargate ALB)
                                       │
   S3 vault bucket  ──[ObjectCreated/Removed]──> EventBridge ──> ReEmbed Lambda ──> Bedrock Titan Embed v2 ──> S3 Vectors index
                                                                       │
                                                                       └──> CloudWatch logs/metrics

   IAM roles (5):  Fargate, ModuleAgents Lambda, Workers Lambda, ReEmbed Lambda, Vercel-OIDC
   Bedrock Guardrail policy (PII + prompt attack)  ─→ attached to orchestrator (built in task 02)
```

#### Data model for this task

S3 layout:

```
s3://{vault_bucket}/
  agents.md                         # orchestrator behavior config
  modules.json                      # 27-module registry (empty array initially)
  _schema/
    modules.schema.json             # JSON schema for modules.json
  vault/                            # all content (added by later tasks)
  usage/
    {yyyy-mm-dd}/
      opus.json                     # daily Opus token + dollar counters

s3://{sessions_bucket}/
  sessions/                         # chat session JSON (added later)
  users/                            # user profile JSON (added later)
```

S3 Vectors:

```
Index name: aicoe-content
Embedding model: amazon.titan-embed-text-v2:0
Dimensions: 1024
Metadata fields: file_path, content_type, frontmatter_id, chunk_index, updated_at
```

modules.json schema (Pydantic + JSON schema):

```python
class ModuleEntry(BaseModel):
    id: str                          # e.g. "module-2"
    name: str                        # e.g. "Asset Library"
    wave: int                        # 1-7
    purpose: str                     # one-line summary
    when_to_use: list[str]           # bullet examples
    example_queries: list[str]       # example user phrases that should route here
    agent_id: str                    # e.g. "AGENT-03"
    model_tier: Literal["haiku-4-5", "sonnet-4-6", "opus-4-7"]
    worker_ids: list[str] = []       # may be empty
    enabled: bool = False            # flip to true when the module is implemented

class ModuleRegistry(BaseModel):
    version: int = 1
    modules: list[ModuleEntry] = []
```

agents.md initial content:

```markdown
# Chat Orchestrator Config

You are the Chat orchestrator for the AI CoE Platform.

## Role
Front-door conversational agent. Route user intent across 27 modules.
Compose responses, cite sources, narrate.

## Routing rules
- If user is asking a knowledge question, retrieve from the Knowledge Base
  first via `search_knowledge_base`.
- If user wants to do something (assess, build, generate, check),
  use `list_modules` then `invoke_module` against the matching module.
- If user asks what something does ("what does Module 4 do?"), use
  `describe_module`.

## Style
Plain English. Cite sources by file path. No company names.
Avoid jargon. Stream when possible.

## Hard rules
- Never invent file paths or module IDs not in the registry.
- Refuse to share secrets, credentials, or environment variable values.
- Refuse to help write code that targets a specific named consulting firm.
```

#### IAM role conventions (one section because every later task adds to this)

5 roles. Each has a clear name, trust policy, and scope. Subsequent tasks attach minimum incremental permissions.

```
ROLE: aicoe-fargate-orchestrator-role
  Trusted by: ecs-tasks.amazonaws.com
  Permissions:
    - lambda:InvokeFunction on aicoe-module-agents-lambda only
    - bedrock:InvokeModel, bedrock:InvokeModelWithResponseStream
    - bedrock:ApplyGuardrail
    - s3:GetObject, s3:PutObject on {vault_bucket}/*, {sessions_bucket}/*
    - s3vectors:QueryVectors, s3vectors:PutVectors on aicoe-content index
    - cloudwatch:PutMetricData

ROLE: aicoe-module-agents-lambda-role
  Trusted by: lambda.amazonaws.com
  Permissions:
    - lambda:InvokeFunction on aicoe-workers-lambda only
    - bedrock:InvokeModel
    - s3:GetObject, s3:PutObject on {vault_bucket}/*, {sessions_bucket}/*
    - s3vectors:QueryVectors, s3vectors:PutVectors
    - cloudwatch:PutMetricData
    - logs:CreateLogStream, logs:PutLogEvents on the function's log group

ROLE: aicoe-workers-lambda-role
  Trusted by: lambda.amazonaws.com
  Permissions:
    - bedrock:InvokeModel
    - s3:GetObject, s3:PutObject on {vault_bucket}/* (NO sessions bucket)
    - cloudwatch:PutMetricData
    - logs:* on the function's log group
    - NO lambda:Invoke (workers cannot invoke other Lambdas)

ROLE: aicoe-reembed-lambda-role
  Trusted by: lambda.amazonaws.com
  Permissions:
    - s3:GetObject on {vault_bucket}/*
    - bedrock:InvokeModel (Titan Embed only, scope by model ARN)
    - s3vectors:PutVectors, s3vectors:DeleteVectors on aicoe-content index
    - cloudwatch:PutMetricData
    - logs:* on the function's log group

ROLE: aicoe-vercel-oidc-role
  Trusted by: token.actions.githubusercontent.com via OIDC (sub claim matches Vercel project)
  Permissions:
    - lambda:InvokeFunction on aicoe-fargate-orchestrator-endpoint-lambda (or ALB invoke)
    - NO direct S3, NO direct Bedrock
```

#### Observability conventions (every subsequent task references these)

Every agent invocation emits one structured log line with this JSON shape:

```json
{
  "ts": "2026-06-03T14:23:45.123Z",
  "request_id": "req_abc123",
  "session_id": "sess_xyz789",
  "display_name_hash": "sha256:abc...",
  "agent_id": "AGENT-NN",
  "tool_name": "search_knowledge_base",
  "model_id": "anthropic.claude-sonnet-4-6",
  "tokens_in": 1234,
  "tokens_out": 567,
  "cost_usd": 0.0123,
  "latency_ms": 1450,
  "outcome": "success|schema_failure|llm_error|timeout|refused",
  "trace": {"parent_agent": "AGENT-01", "depth": 2}
}
```

CloudWatch metrics emitted per invocation (in `AICoE/Agents` namespace):

- `AgentInvocations` (count, dimensions: agent_id, outcome)
- `AgentLatency` (ms, dimensions: agent_id)
- `AgentTokensIn`, `AgentTokensOut` (count, dimensions: agent_id, model_id)
- `AgentCostUSD` (custom, dimensions: agent_id, model_id)

CloudWatch alarms (created in this task, fed by later tasks):

- `aicoe-daily-cost-warning`: daily sum of `AgentCostUSD` across all dimensions > $5 → email to developer
- `aicoe-error-rate-warning`: 1-hour rate of `AgentInvocations` with `outcome != success` > 5% → email
- `aicoe-opus-cost-critical`: daily Opus cost > configured cap (default $5) → page (just email for demo)

#### Daily Opus cost cap pattern

Cap state lives at `s3://{vault_bucket}/usage/{yyyy-mm-dd}/opus.json`:

```json
{
  "date": "2026-06-03",
  "tokens_consumed": 12345,
  "cost_usd": 1.23,
  "cap_usd": 5.00,
  "cap_hit_at": null
}
```

Before any Opus invocation:

1. Read today's `opus.json`. If absent, treat as zero.
2. Estimate this call's max cost (input tokens × Opus rate + max_output_tokens × Opus rate).
3. If `cost_usd + estimate > cap_usd`: raise `OpusCapExceeded`, return user-visible message.
4. Otherwise: proceed.
5. After call: update `opus.json` with conditional write (S3 versioning prevents lost updates).

#### Definition-of-Done checklist template (every subsequent task includes this)

```markdown
- [ ] All listed FRs have passing smoke tests
- [ ] Agent returns valid Pydantic-validated output schema
- [ ] Structured log line emitted on every invocation (matches conventions)
- [ ] CloudWatch metric counters increment on success and failure
- [ ] IAM permissions added incrementally to existing roles (no new roles created in module tasks)
- [ ] S3 reads/writes scoped to documented paths only
- [ ] No secrets in code, all from env or Secrets Manager
- [ ] CDK changes applied to dev environment cleanly
- [ ] Manual smoke test passes (see per-task smoke steps)
- [ ] No company names, no PII, no real client data in any output
```

#### Implementation steps (each with verification)

1. **AWS account prep**
   - Files: none (account-level config)
   - Steps: request Bedrock model access for Sonnet 4.6, Haiku 4.5, Opus 4.7, Titan Embed v2 in us-east-1. Create AWS CLI profile `aicoe-dev` pointing to your account.
   - Verify: `aws bedrock list-foundation-models --region us-east-1 --profile aicoe-dev | jq '.modelSummaries[].modelId'` includes all four model IDs.

2. **CDK Python project bootstrap**
   - Files: `infra/app.py`, `infra/cdk.json`, `infra/requirements.txt`, `infra/stacks/__init__.py`
   - Steps: `uv init infra/`, `uv add aws-cdk-lib constructs`, `cdk init app --language python` (or equivalent). Create one stack per concern: `storage`, `iam`, `events`, `observability`, `guardrails`, `agents` (placeholder), `frontend` (placeholder — Vercel is outside CDK).
   - Verify: `cd infra && uv run cdk synth` succeeds.

3. **Storage stack**
   - Files: `infra/stacks/storage.py`
   - Steps: create vault bucket and sessions bucket (S3 Standard, versioning on, lifecycle: non-current versions expire after 90 days). Create S3 Vectors index `aicoe-content`, dimensions 1024.
   - Verify: `aws s3 ls --profile aicoe-dev` shows both buckets. `aws s3vectors list-indexes --profile aicoe-dev` shows the index.

4. **IAM stack (5 roles)**
   - Files: `infra/stacks/iam.py`
   - Steps: create the 5 roles per the conventions table above. Use `aws-cdk-lib.aws_iam.Role` with explicit policies; do not use managed policies.
   - Verify: `aws iam get-role --role-name aicoe-fargate-orchestrator-role` returns expected trust policy. Repeat for the other 4 roles.

5. **Guardrails stack**
   - Files: `infra/stacks/guardrails.py`
   - Steps: create a Bedrock Guardrail with PII detection (ANONYMIZE for SSN, EMAIL, PHONE) and prompt attack detection (HIGH severity). Output the guardrail ARN as a CDK export.
   - Verify: `aws bedrock get-guardrail --guardrail-identifier {id}` returns status `READY`.

6. **ReEmbed Lambda + EventBridge**
   - Files: `agents/lambdas/reembed/handler.py`, `agents/lambdas/reembed/chunker.py`, `infra/stacks/events.py`
   - Steps: write the Lambda code (read S3 object, chunk by heading with 1000-token max and 100-token overlap, embed each chunk via Titan Embed v2, upsert to S3 Vectors with metadata). Wire an EventBridge rule for `s3:ObjectCreated:*` and `s3:ObjectRemoved:*` on the vault bucket. Hash-based dedup: compute SHA-256 of content, store in vector metadata; skip if hash unchanged.
   - Verify: drop `test.md` with content "AI maturity stage 2 means piloting" into vault bucket. Wait 60s. Run `aws s3vectors query-vectors --index aicoe-content --query-vector $(some-prebuilt-embed-of-stage-2) --top-k 1`. Confirm the returned chunk references `test.md`.

7. **modules.json schema and initial file**
   - Files: `vault/_schema/modules.schema.json`, `vault/modules.json`, `agents/lib/registry.py`
   - Steps: write the Pydantic `ModuleRegistry` model. Generate the JSON Schema and save it. Create an initial `modules.json` with `version: 1, modules: []`. Add a unit test for the Pydantic loader.
   - Verify: `pytest agents/lib/tests/test_registry.py::test_empty_registry_loads` passes.

8. **agents.md initial file**
   - Files: `vault/agents.md`
   - Steps: create the file with the content shown in the Data model section above.
   - Verify: file exists in vault bucket. Open it via the AWS console and confirm content matches.

9. **Next.js 16 project bootstrap**
   - Files: `web/package.json`, `web/next.config.ts`, `web/tailwind.config.ts`, `web/app/layout.tsx`, `web/app/(authenticated)/dashboard/page.tsx`
   - Steps: `pnpm create next-app@latest web --typescript --tailwind --app --turbopack`. Install shadcn/ui: `pnpm dlx shadcn@latest init`. Add base components (Button, Card, Input).
   - Verify: `pnpm dev` boots the app on `http://localhost:3000` and a placeholder `/dashboard` route renders.

10. **Password gate middleware + localStorage flow**
    - Files: `web/middleware.ts`, `web/app/login/page.tsx`, `web/lib/auth.ts`
    - Steps: middleware checks for an `auth_ok` cookie (HttpOnly) set after correct password entry. Login page accepts password (env var `APP_PASSWORD`) and display name; on success sets the cookie and writes display name to localStorage; redirects to `/dashboard`. Logout clears both.
    - Verify: visit `/dashboard` without auth → redirected to `/login`. Enter wrong password → stay on login with error. Enter correct password + name → land on dashboard. Refresh → still on dashboard. Display name visible in header.

11. **Vercel-AWS OIDC federation**
    - Files: `infra/stacks/iam.py` (add Vercel role), `web/lib/aws.ts`, `.github/workflows/deploy-vercel.yml`
    - Steps: follow Vercel's AWS OIDC integration setup. Create the `aicoe-vercel-oidc-role` with a trust policy keyed to the Vercel project's OIDC issuer + sub claim. In `web/lib/aws.ts`, build a helper that calls `AssumeRoleWithWebIdentity` then invokes a target Lambda. Add a no-op `aicoe-test-lambda` for verification.
    - Verify: deploy to Vercel preview. From a server action, call the test Lambda. Confirm CloudWatch logs show the invoke. No AWS access keys in Vercel env vars (only the role ARN and region).

12. **CI/CD pipeline**
    - Files: `.github/workflows/ci.yml`, `.github/workflows/deploy-dev.yml`, `.github/workflows/deploy-vercel.yml`
    - Steps: `ci.yml` runs on PRs: pnpm lint, pnpm test, uv run ruff check, uv run pytest, uv run cdk synth. `deploy-dev.yml` is manual-trigger: assumes dev AWS role, runs `cdk deploy --all --require-approval never` (acceptable for solo demo only). `deploy-vercel.yml` deploys frontend on merges to main (Vercel CLI or git integration).
    - Verify: open a no-op PR; all CI checks green. Manually trigger deploy-dev; CDK deploys cleanly. Merge to main; Vercel auto-deploys.

13. **Observability conventions**
    - Files: `agents/lib/logging.py`, `agents/lib/metrics.py`, `infra/stacks/observability.py`
    - Steps: `logging.py` provides `log_invocation(**fields)` matching the JSON shape above. `metrics.py` wraps `cloudwatch.put_metric_data` with sensible defaults. CDK creates 3 alarms (cost warning, error rate warning, Opus cost critical) and 1 SNS topic for email delivery.
    - Verify: invoke a test handler that calls `log_invocation` + a metric emit. Tail the log group; confirm the JSON shape. Verify the metric appears in CloudWatch.

14. **Daily Opus cost cap mechanism**
    - Files: `agents/lib/cost_cap.py`, `agents/lib/tests/test_cost_cap.py`
    - Steps: implement read-modify-write against `s3://{vault_bucket}/usage/{yyyy-mm-dd}/opus.json` with optimistic locking via S3 versioning. Default cap $5/day, env-var overridable.
    - Verify: `pytest agents/lib/tests/test_cost_cap.py` covers: empty file → first call works, accumulated > cap → next call raises `OpusCapExceeded`.

15. **Shared Python agents lib**
    - Files: `agents/lib/base_agent.py`, `agents/lib/bedrock_client.py`, `agents/lib/models.py`, `agents/lib/registry.py`, `agents/lib/tests/`
    - Steps: `base_agent.py` defines a Strands-compatible base class with auto-instrumentation (logs + metrics around every tool call). `bedrock_client.py` wraps Bedrock calls with retry, cost computation, and Opus cap check. `models.py` exports model ID constants.
    - Verify: `pytest agents/lib/` passes. A toy agent class derived from `BaseAgent` invokes a stub model and produces a valid log line + metric.

#### Definition of done

- [ ] FR-001 verified end-to-end (password gate; display name persists)
- [ ] FR-004 verified end-to-end (file change → embedded within 60s)
- [ ] FR-005 partial: agents.md file exists and is readable from vault bucket (full verification in task 02)
- [ ] All 5 IAM roles created with least-privilege policies
- [ ] CDK `synth` and `deploy --all` succeed against dev account
- [ ] Vercel preview deploy reaches dashboard placeholder after password
- [ ] CI green on no-op PR
- [ ] Manual smoke test passes:
  - Visit Vercel preview URL → land on login
  - Enter correct password + name → land on dashboard
  - Drop a test markdown file into vault bucket → wait 60s → query S3 Vectors and confirm retrieval
  - Visit CloudWatch console → confirm log group + metric exist + alarm visible
- [ ] No secrets in code; all from env vars or Secrets Manager
- [ ] All file paths from "Files to create/edit" exist
- [ ] No company names, no PII, no real client data anywhere in code, vault, or logs

#### Behavioral guardrails for this task

Before writing code:
- State your assumptions explicitly. If any acceptance check is ambiguous, ask before coding.
- If a simpler approach exists than what's described, say so before implementing.
- Confirm AWS CDK version and Strands Agents version in use; record in `README.md`.

While writing code:
- Touch only files listed in this task. Do not refactor adjacent code.
- Match existing style (quote style, formatting, naming) once a file exists.
- No speculative features. No abstractions for single-use code. No error handling for impossible cases.
- Every line you change should trace to a step above.

Before declaring done:
- Run the full test suite, not just new tests.
- Walk the Definition of Done checklist and confirm each item.
- Record the actual deployed dev AWS account ID and region in `README.md`.

#### What is explicitly OUT of scope for this task

- AGENT-01 Chat orchestrator implementation (task 02_wave1_chat_orchestrator.md)
- Any module agent code (later tasks per module)
- modules.json populated with actual modules (added incrementally by later tasks)
- vault content (seeded in task 01_wave1_vault_seed_content.md)
- Cognito or any real auth (post-demo-plan.md Section 1)
- DynamoDB, Postgres, or any database (post-demo-plan.md Section 6)
- VPC, NAT Gateway, VPC endpoints (post-demo-plan.md Section 5)
- Multi-region, DR, failover (post-demo-plan.md Section 4)
- API Gateway (per AD-02)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log

Track decisions and questions during implementation:

- 2026-06-03: created from brief + design with hybrid Fargate + Lambda topology per AD-01.

---

## D. References

- Brief: `ai_docs/brief.md` Sections 1, 2, 6, 12, 13, 17
- Design: `ai_docs/design.md` Sections 2 (ADs), 3 (diagram), 4 (component inventory), 7 (avoided complexity), 8 (risk assessment)
- Post-demo plan: `ai_docs/post-demo-plan.md` (everything deferred)
- North star: `docs/starters/AI CoE Platform Brief.md` (full 27-module vision)
- AWS Strands Agents: https://strandsagents.com
- AWS Bedrock model IDs: confirm at implementation time
- AWS S3 Vectors: confirm SDK signatures at implementation time
- Vercel-AWS OIDC federation: Vercel official guide
