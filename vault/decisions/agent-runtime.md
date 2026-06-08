---
id: decision-agent-runtime-bedrock-converse
title: Standardize agent runtime on Bedrock Converse, defer Strands
kind: decision
owner: demo
updated_at: "2026-06-06"
---

# Standardize agent runtime on Bedrock Converse, defer Strands

## Decision

All AI CoE agents — the Chat orchestrator (AGENT-01) and every future module agent
and task worker — are built on a **lightweight tool-calling loop over the Bedrock
Converse API**, using the shared `agents/lib/bedrock_client.py` wrapper. We do **not**
adopt the Strands Agents framework, even though task specs reference it.

## Context

The Phase 0 foundation deliberately built `BaseAgent` and `BedrockClient` directly on
the Bedrock Converse API (with retry, cost computation, the Opus cap, and the
instrumentation contract already wired in). Task 02's spec describes AGENT-01 as a
"Strands agent," but `strands-agents` was never installed and adopting it now would
fork the runtime: two streaming models, two tool-definition styles, and a heavier
container, for no capability we need at demo grade.

## Options considered

| Option | Why not / why |
|---|---|
| Strands Agents | Heavier container, second streaming/tool model to learn, diverges from the foundation's Converse-based `BaseAgent`. Not justified for a solo demo. |
| **Bedrock Converse tool-loop** | **Chosen** — reuses `BedrockClient` (retry, cost cap, metrics, guardrails), fully unit-testable with a fake client, one consistent pattern across all 43 agents/workers. |

## Consequences

- AGENT-01 and all later module-agent / worker tasks implement tools as plain Python
  functions plus a Converse `toolConfig` spec, executed in an instrumented loop — no
  Strands dependency.
- `BedrockClient` gains `tool_config`, `guardrail_id`, and `converse_stream` support
  (backward compatible).
- If a future requirement genuinely needs Strands (e.g. a feature we can't express in
  the Converse loop), revisit this entry rather than mixing both runtimes ad hoc.

Supersedes the "Strands agent" phrasing in `ai_docs/tasks/02_wave1_chat_orchestrator.md`
and the equivalent phrasing in later module/worker task specs.
