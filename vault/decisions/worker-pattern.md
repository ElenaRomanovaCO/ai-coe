---
id: decision-worker-pattern
title: Layer 3 worker pattern — static-dispatch workers Lambda, deterministic workers
kind: decision
owner: demo
updated_at: "2026-06-09"
---

# Layer 3 worker pattern — static-dispatch workers Lambda, deterministic workers

## Decision

Layer 3 task workers live in a single `aicoe-workers-lambda` and are routed the
same way module agents are: an explicit **static dispatch registry**
(`agents/lambdas/workers/router.py`, `{worker_id -> Worker factory}`), no Strands.
Module agents call workers with `invoke_worker` (lambda:Invoke,
`{worker_id, args}`). Workers are **deterministic and self-contained** — no LLM in
the worker tier; any conversational phrasing is the module agent's job.

## Context

Task 05 (Maturity Assessment) introduces the first workers (WORKER-01 question
picker, WORKER-02 scorer, WORKER-03 recommender). The spec referenced Strands and
"Haiku workers," but `vault/decisions/agent-runtime.md` already dropped Strands, and
the task's hard guardrail requires **deterministic scoring**. Every later worker
task inherits whatever we choose here, so it's settled once.

## Decisions & why

| Choice | Rationale |
|---|---|
| Workers in one Lambda, static-dispatch router | Mirrors `vault/decisions/module-agent-routing.md`; AD-01 (few Lambdas); trivial to extend. |
| Deterministic workers (no LLM) | Satisfies the "deterministic scoring / same inputs → same stage" guardrail; fully unit-testable without AWS or Bedrock; cheap. Question picker = fixed bank with adaptive (but deterministic) length; scorer = keyword rule; recommender = filter. |
| Conversational phrasing in the module agent, not the worker | Keeps workers pure; AGENT-02 owns tone (mechanical for now, LLM-phrasable later without contract change). |
| In-progress state in S3 (sessions bucket) | AD-04 (no DB). AGENT-02 persists `assessments/{slug}/{id}.json`; final result markdown to `vault/assessments/{slug}/{ts}.md` (re-embedded, searchable). |
| `invoke_worker` = lambda:Invoke `{worker_id, args}` | Same contract shape as `invoke_module`; `module-agents-lambda-role` already has lambda:Invoke on the workers function. |

## Consequences

- `WorkerInvoker` (`agents/lambdas/modules/worker_client.py`) is the reusable
  client; tests close the loop with a fake Lambda that calls `workers.router.route`.
- IAM: `aicoe-workers-lambda-role` gains `s3:ListBucket` on the vault (WORKER-03
  enumerates assets) — the spec's "no IAM change" was wrong, same class of gap the
  orchestrator/module roles hit.
- New module agents that decompose work follow this: add a `Worker` subclass + one
  REGISTRY line; call it via `invoke_worker`.

Builds on `vault/decisions/agent-runtime.md` and `vault/decisions/module-agent-routing.md`.
