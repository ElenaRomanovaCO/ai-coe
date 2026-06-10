---
id: decision-agent-05-orchestration
title: Worker-orchestrating agents run a mechanical pipeline + one LLM call, not a tool-loop
kind: decision
owner: demo
updated_at: "2026-06-10"
---

# Worker-orchestrating agents run a mechanical pipeline + one LLM call, not a tool-loop

## Decision

AGENT-05 (Governance & Risk Checker) sequences its two workers in a **fixed,
mechanical pipeline** — WORKER-04 (regulation_finder) → WORKER-05 (checklist_generator)
— and uses the Sonnet 4.6 model for exactly **one thing**: writing the 3-4 sentence
executive summary from the already-built checklist. The LLM never decides which
worker to call, never builds the checklist, and never scores risk. A deterministic
fallback summary is used if the model call fails. This is the pattern Wave-3+
worker-orchestrating module agents follow, in preference to a full Bedrock Converse
tool-loop where the model drives the workers.

## Context

The task spec frames AGENT-05 as "Sonnet 4.6 with 3 tools (invoke_worker ×2,
write_governance_review)," which reads like an LLM tool-loop (the AGENT-25 pattern).
But the governance flow is a **fixed pipeline** with no branching the model needs to
decide, and the workers are already deterministic and fully testable
(`vault/decisions/worker-pattern.md`). Letting the LLM orchestrate would add cost and
non-determinism for no control-flow benefit, and would put the model on the path that
produces the risk output — exactly what the determinism guardrail discourages.

## Options considered

| Option | Verdict |
|---|---|
| Mechanical pipeline + one LLM call for the summary only | **Chosen** — risk logic stays deterministic/testable; LLM adds prose where it helps; ~1 cheap call per run; matches AGENT-02's worker sequencing |
| Fully deterministic (templated summary, no LLM) | Why not — zero cost and fully testable, but the executive summary prose is noticeably weaker for the demo |
| Full Converse tool-loop (literal spec reading) | Why not — highest cost and least deterministic for a fixed pipeline; puts the LLM on the risk-output path |

## Consequences

- The risk output (matched regulations + checklist) is produced entirely by
  deterministic workers, so it is reproducible and unit-tested without a model.
- AGENT-05 makes exactly one Sonnet call per `check`; the summary degrades to a
  deterministic template on any model error, so a Bedrock outage never fails the run.
- **Wave-3+ precedent:** later worker-orchestrating module agents (e.g. Ethics
  Checker AGENT-20) default to this shape — mechanical worker sequencing, LLM reserved
  for narrow prose/judgment steps — unless a task genuinely needs model-driven control
  flow, in which case the AGENT-25 Converse-loop pattern applies.
- No Bedrock guardrail is applied to the summary call (module-agents role lacks
  `ApplyGuardrail`, see `vault/decisions/asset-panel-no-guardrail.md`); the prompt is
  grounded in the deterministic checklist, so the risk is low.

## Links

- Task: `ai_docs/tasks/08_wave3_governance_checker.md`
- Related: `vault/decisions/worker-pattern.md`, `vault/decisions/agent-runtime.md`, `vault/decisions/asset-panel-no-guardrail.md`
