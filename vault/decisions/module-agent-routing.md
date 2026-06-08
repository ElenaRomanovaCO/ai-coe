---
id: decision-module-agent-routing
title: Module-agents Lambda routing = static dispatch registry (no Strands)
kind: decision
owner: demo
updated_at: "2026-06-07"
---

# Module-agents Lambda routing = static dispatch registry (no Strands)

## Decision

The single `aicoe-module-agents-lambda` (AD-01: 26 Layer-2 agents, one function)
routes invocations with an **explicit static dispatch registry**, not Strands. The
orchestrator's `invoke_module` sends `{"agent_id": "...", "args": {...}}`;
`agents/lambdas/modules/router.py` holds `REGISTRY: {agent_id -> ModuleAgent
factory}`, looks up the agent, and calls `agent.handle(args)`. Each agent then
dispatches on an `op` key to its own operations. Adding a module = one REGISTRY
line + one `ModuleAgent` subclass.

## Context

The task 03 spec says "internal Strands routing per AD-01," but
`vault/decisions/agent-runtime.md` already standardized all agents on the Bedrock
Converse tool-loop and dropped Strands. We needed the routing mechanism decided
once because every later module task (AGENT-04 … AGENT-27) inherits it.

## Options considered

| Option | Why not / why |
|---|---|
| Strands internal routing | Reintroduces the framework we removed in agent-runtime.md; two runtimes, no benefit at demo scale. |
| **Static dispatch registry** | **Chosen** — a dict `{agent_id -> factory}` + per-agent `op` dispatch. Mirrors the orchestrator's explicit tool dispatch, fully unit-testable, trivial to extend. |
| Flat `(agent_id, op)` table | Flatter, but agents stop being cohesive objects; per-agent setup (clients, model tier) gets duplicated. |
| One Lambda per module agent | Reverses AD-01; 26 functions, 26 cold-start surfaces, more infra/IAM. |

## Consequences

- `router.handler` returns the **same `not_implemented` shape** for an unknown
  `agent_id` that the orchestrator already returns for a disabled module, so the
  chat path degrades identically whether a module is disabled in `modules.json` or
  simply absent from the registry.
- `ModuleAgent(BaseAgent)` is the common base; agents reuse the shared
  instrumentation (`run_tool`), metrics, and cost logic.
- Each agent's `handle(args)` accepts an optional `op` selector and is tolerant
  (e.g. AGENT-03 infers `get_asset` from an `asset_id`, `search` from a `query`),
  so both the orchestrator (LLM-built payloads) and the web (explicit ops) work.
- Module agents are invoked by **direct `lambda:Invoke`** — from the orchestrator
  and, for read-only flows, directly from the web's server actions (no orchestrator
  in the loop).

Builds on `vault/decisions/agent-runtime.md`.
