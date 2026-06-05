# AI CoE Platform

Internal multi-agent platform over a markdown knowledge base on S3. Chat
orchestrator + module agents + task workers, served through a Next.js frontend.

> **Status:** Phase 0 (Foundation) in progress. See `ai_docs/tasks/00_foundation.md`.

## Repository layout

```
infra/      AWS CDK (Python) — storage, IAM, events, observability, guardrails, frontend (Amplify)
agents/     Python agents
  lib/        shared library (models, logging, metrics, cost cap, registry, base agent)
  lambdas/    Lambda handlers (reembed, …)
web/        Next.js 16 frontend (AWS Amplify Hosting Gen 2)
vault/      seed knowledge-base files (agents.md, modules.json, schema)
ai_docs/    brief, design, task specs
docs/       north-star vision
```

## Tech stack

| Layer        | Choice                                                            |
|--------------|-------------------------------------------------------------------|
| Agents       | Python 3.12, AWS Strands Agents, Pydantic v2                       |
| Runtime      | Fargate Spot (orchestrator) + Lambdas (module agents, workers, re-embed) |
| Frontend     | Next.js 16 (App Router), Tailwind, shadcn/ui → AWS Amplify Hosting Gen 2 |
| LLM          | AWS Bedrock — Sonnet 4.6 / Haiku 4.5 / Opus 4.7; Titan Embed v2   |
| Storage      | S3 (vault + sessions) + S3 Vectors. No DynamoDB, no Postgres.     |
| IaC / CI     | AWS CDK (Python) + GitHub Actions                                 |
| Region       | us-east-1                                                          |

### Confirmed Bedrock model IDs (us-east-1)

| Tier            | Model ID                                       |
|-----------------|------------------------------------------------|
| Sonnet 4.6      | `anthropic.claude-sonnet-4-6`                  |
| Haiku 4.5       | `anthropic.claude-haiku-4-5-20251001-v1:0`     |
| Opus 4.7        | `anthropic.claude-opus-4-7`                    |
| Titan Embed v2  | `amazon.titan-embed-text-v2:0` (1024 dims)     |

> On-demand Anthropic invocation in us-east-1 may require the regional inference
> profile prefix (`us.anthropic.…`). See `agents/lib/models.py`.

## Local development

### Python (agents lib)

```bash
uv sync --group dev
uv run pytest agents/lib
uv run ruff check agents
```

> Lambda runtime is pinned to Python 3.12 in CDK; the test suite runs on any
> `>=3.12` interpreter locally.

### Frontend

```bash
cd web
pnpm install
pnpm dev          # http://localhost:3000
```

Copy `web/.env.example` → `web/.env.local` and set `APP_PASSWORD`.

### Infra (CDK)

```bash
cd infra
uv sync
uv run cdk synth          # no AWS calls
uv run cdk deploy --all   # requires AWS credentials (see Deploy)
```

## Deploy

> ⚠️ Deploy steps create billable AWS resources (including the Amplify app) and are
> **not run by the build** — run them yourself with credentials in hand.

- **AWS account / region:** dev account `957650740941`, `us-east-1` (detected via
  the `default` CLI profile; the task spec names a profile `aicoe-dev`).
- **Bedrock model access:** already enabled for Sonnet 4.6, Haiku 4.5, Opus 4.7,
  Titan Embed v2 (confirmed via `list-foundation-models`).

### Runbook (in order)

1. **S3 Vectors index** (no CloudFormation support — must run first):
   ```bash
   uv run --project infra python infra/scripts/create_vector_index.py
   ```
   Verify: `aws s3vectors list-indexes` shows `aicoe-content`.
2. **CDK bootstrap + deploy:**
   ```bash
   cd infra && uv sync
   npx aws-cdk bootstrap aws://957650740941/us-east-1
   npx aws-cdk deploy --all --require-approval never \
     --context alarm_email=rev1982usa@gmail.com
   ```
3. **Seed vault files** into the deployed vault bucket (bucket name is a stack output):
   ```bash
   aws s3 cp vault/agents.md             s3://$VAULT_BUCKET/agents.md
   aws s3 cp vault/modules.json          s3://$VAULT_BUCKET/modules.json
   aws s3 cp vault/_schema/modules.schema.json s3://$VAULT_BUCKET/_schema/modules.schema.json
   ```
   Then verify FR-004: drop a test `.md` into `s3://$VAULT_BUCKET/vault/` and within
   60s query S3 Vectors for its content.
4. **AWS Amplify Hosting (Gen 2):** the `AiCoE-Frontend` stack provisions the
   Amplify app + `main` branch and attaches the `aicoe-amplify-ssr-role` compute
   role. Before deploy, store a GitHub PAT in Secrets Manager (default secret name
   `aicoe/github-token`, key `token`) and pass the repo URL to CDK:
   ```bash
   npx aws-cdk deploy AiCoE-Frontend \
     --context github_repository=https://github.com/<org>/<repo> \
     --context github_token_secret=aicoe/github-token
   ```
   Then in the Amplify console set the `APP_PASSWORD` branch env var (kept out of
   code). Amplify auto-deploys the Next.js app on every push to `main` via its
   native git integration — no GitHub Actions job for the frontend. The SSR Lambda
   invokes the orchestrator using its attached role; no AWS keys in the app config.

### Verified locally (no deploy needed)

- `uv run pytest agents -q` → **35 passing**
- `uv run ruff check agents infra` → clean
- `cd infra && npx aws-cdk synth` → all 6 stacks synthesize
- `cd web && pnpm build && pnpm lint` → clean; password gate (FR-001) smoke-tested

## No secrets in code

All secrets come from environment variables or AWS Secrets Manager. The shared
password lives in `APP_PASSWORD` (frontend env), never committed.
