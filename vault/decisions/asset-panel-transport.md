---
id: decision-asset-panel-transport
title: Asset Q&A panel transport = non-streaming server action, not SSE
kind: decision
owner: demo
updated_at: "2026-06-10"
---

# Asset Q&A panel transport = non-streaming server action, not SSE

## Decision

The scoped asset chat panel (AGENT-25, Module 26) sends each turn through a
**Next.js server action** (`web/app/actions/asset_qa.ts` → `invokeModule` →
module-agents Lambda) and renders the full answer in one shot. It does **not** use
the SSE route handler + orchestrator Function URL transport the global chat dock
uses (`vault/decisions/web-chat-transport.md`). The panel components
(`AssetChatPanel` / `AssetChatPanelHook`) and this action live in module-neutral
locations so every later asset-detail page reuses them unchanged.

## Context

AGENT-25 runs a Bedrock Converse tool-loop but returns the assembled answer from a
single synchronous Lambda invoke — it is **non-streaming** by design (the panel is a
focused Q&A, not a long generation). Two facts make a server action the right fit:

1. **No incremental stream to forward.** The dock needs a `ReadableStream` body to
   stream tokens, which forced a route handler there. The panel has one response
   payload, so a server action (which returns a single serialized result) is
   simpler and sufficient — no SSE parser, no passthrough route.
2. **It already has a Lambda path.** The Asset Library actions invoke the
   module-agents Lambda via the SSR role's `lambda:InvokeFunction`; the panel reuses
   exactly that transport (`invokeModule(AGENT-25, …)`), no new wiring.

## Options considered

| Option | Verdict |
|---|---|
| Server action → `invokeModule` (one-shot) | **Chosen** — matches AGENT-25's non-streaming contract; reuses the Asset Library Lambda transport; reusable across panels |
| SSE route handler + orchestrator Function URL (the dock's path) | Why not — only justified for incremental token streaming; AGENT-25 doesn't stream, so it adds an SSE parser + passthrough route for no benefit |
| Route through the orchestrator (invoke_module) | Why not — adds a hop and couples the panel to the global dock session; the panel is scoped to one asset and calls its agent directly |

## Consequences

- Client keeps the panel transcript in component state and replays it as `history`
  on each turn (AGENT-25 is otherwise stateless per request); one `session_id` per
  open panel.
- Citations link back to compared assets; quick-prompt suggestions come from the
  agent response.
- **Every later asset-detail panel (Compliance Tracker, Vendor Eval, Intelligence
  Feed) inherits this transport** — embed `<AssetChatPanelHook .../>` and add a
  thin server action if the agent differs; no streaming plumbing required.
- If a future panel needs token streaming, it must adopt the dock's SSE path rather
  than extend this action.

## Links

- Task: `ai_docs/tasks/07_wave2_universal_asset_qa.md`
- Related: `vault/decisions/web-chat-transport.md`, `vault/decisions/module-agent-routing.md`
