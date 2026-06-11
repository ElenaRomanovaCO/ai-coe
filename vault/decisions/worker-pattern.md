---
id: decision-worker-pattern
title: Layer 3 worker pattern — static-dispatch workers Lambda, deterministic by default (one LLM-worker exception)
kind: decision
owner: demo
updated_at: "2026-06-10"
---

# Layer 3 worker pattern — static-dispatch workers Lambda, deterministic workers

## Decision

Layer 3 task workers live in a single `aicoe-workers-lambda` and are routed the
same way module agents are: an explicit **static dispatch registry**
(`agents/lambdas/workers/router.py`, `{worker_id -> Worker factory}`), no Strands.
Module agents call workers with `invoke_worker` (lambda:Invoke,
`{worker_id, args}`). Workers are **deterministic and self-contained by default** —
no LLM in the worker tier; any conversational phrasing is the module agent's job.

**Exception (Task 15, 2026-06-10):** a worker MAY make its own Bedrock call when
generative prose *is* the worker's whole purpose and the module agent would otherwise
be a pass-through. The first and (so far) only such worker is **WORKER-11
`commentary_writer`** (Sonnet 4.6), which writes the Intelligence Feed's personalized
"what this means for you" note. Any LLM-backed worker MUST ship a **deterministic
fallback** so it still returns a useful result (and stays unit-testable offline) when
Bedrock errors — WORKER-11 falls back to the item's own "What this means" section, or
its lede. This is a deliberate, narrow carve-out, not a new default: keep workers
deterministic unless prose generation is the entire job.

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
| Deterministic workers (no LLM) by default | Satisfies the "deterministic scoring / same inputs → same stage" guardrail; fully unit-testable without AWS or Bedrock; cheap. Question picker = fixed bank with adaptive (but deterministic) length; scorer = keyword rule; recommender = filter. |
| LLM worker allowed only when prose is the whole job (WORKER-11) | The workers role already grants `bedrock:InvokeModel` over the chat models (`invoke_model_resource_arns`, region-wildcarded foundation-model + inference-profile ARNs), so the cross-region path that bit the orchestrator/module roles is already covered — **no IAM change**. Required deterministic fallback preserves offline testability and graceful degradation. WORKER-10 `item_classifier`, by contrast, stays deterministic (relevance scoring is a rule). |
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
