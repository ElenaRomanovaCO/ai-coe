---
id: decision-asset-panel-no-guardrail
title: Asset-panel module agents run without a Bedrock guardrail (prompt-only refusal)
kind: decision
owner: demo
updated_at: "2026-06-10"
---

# Asset-panel module agents run without a Bedrock guardrail (prompt-only refusal)

## Decision

AGENT-25 (and any module agent that runs a Converse loop behind an asset-detail
chat panel) runs with **no Bedrock guardrail applied**. Off-asset, unsafe, or
out-of-scope requests are refused by **system-prompt steering only**. This is a
conscious tradeoff, not an oversight: the global chat dock (AGENT-01) still enforces
the guardrail, but the asset panels do not.

## Context

The module-agents Lambda role (`aicoe-module-agents-lambda-role`) is **not** granted
`bedrock:ApplyGuardrail` — only the orchestrator/fargate roles hold that grant
(`infra/stacks/iam.py`). So a module agent physically cannot call the guardrail at
runtime without an IAM change. AGENT-25 is the first Layer-2 module agent to run a
real Converse generation loop (earlier module agents 03/04/16 were mechanical, 02
delegated to deterministic workers), so it is the first to actually surface this gap.
The asset panel is also low-risk: the model is grounded in one asset whose content is
baked into the system prompt, and the prompt instructs it to decline anything
unrelated, secrets/credentials/PII requests, and named companies.

## Options considered

| Option | Verdict |
|---|---|
| Prompt-only refusal, no guardrail | **Chosen** — no IAM delta; acceptable risk for a grounded single-asset panel in a demo; ships now |
| Grant the module-agents role `bedrock:ApplyGuardrail` and apply the guardrail in AGENT-25 | Why not (for now) — widens a shared role used by all 26 module agents; deferred until a higher-risk module needs it |
| Route panel turns through the orchestrator so the dock's guardrail covers them | Why not — couples the scoped panel to the global session and adds a hop, contradicting `decision-asset-panel-transport` |

## Consequences

- **Every later asset-detail panel inherits this prompt-only-refusal posture**
  (Compliance Tracker, Vendor Eval, Intelligence Feed). Refusal quality depends on
  the system prompt, so each panel's prompt must keep the decline rules.
- If a future module behind a panel handles higher-risk input (e.g. free-form user
  uploads, regulatory advice presented as authoritative), revisit by granting
  `bedrock:ApplyGuardrail` to the module-agents role and applying the guardrail in
  that agent — a localized IAM + agent change, no architecture shift.
- Deviation from the implicit "all agents enforce the guardrail" expectation is
  scoped to module-agent panels and recorded here so later tasks don't assume the
  guardrail is active on this path.

## Links

- Task: `ai_docs/tasks/07_wave2_universal_asset_qa.md`
- Related: `vault/decisions/agent-runtime.md`, `vault/decisions/module-agent-routing.md`, `vault/decisions/asset-panel-transport.md`
