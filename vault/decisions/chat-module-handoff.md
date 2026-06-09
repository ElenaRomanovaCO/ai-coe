---
id: decision-chat-module-handoff
title: Chat→module handoff for guided UIs = navigate UIAction, not inline multi-turn
kind: decision
owner: demo
updated_at: "2026-06-09"
---

# Chat→module handoff for guided UIs = navigate UIAction, not inline multi-turn

## Decision

When a user asks the chat dock to run a **guided, multi-step module** (e.g. the
maturity assessment), the orchestrator does **not** run the module's multi-turn flow
inline in the dock. Instead it emits a `navigate` **UIAction** and the dock renders a
button that takes the user to the module's dedicated page. This is driven by an
optional `ui_route` field on the module registry entry.

## Context

Task 05's spec (step 7) said "Chat invokes AGENT-02 and streams the question flow
inline in the chat dock." But the dock is **stateless** request/response, and the
orchestrator only persists `{user, assistant}` text per turn — tool results
(including an `assessment_id`) are not carried across turns. True inline multi-turn
would require re-architecting the dock + orchestrator to thread per-module
conversation state. That's a large, fragile change for little benefit, since the
assessment already has a rich dedicated guided UI (the design's centerpiece).

## Mechanism

- `ModuleEntry.ui_route: str | None` (registry). Module 1 sets
  `/modules/maturity-assessment`.
- Orchestrator `invoke_module` dispatch: if the target module is enabled **and** has
  a `ui_route`, it skips the Lambda call, appends `UIAction(type="navigate",
  payload={route,label})`, and returns an `open_module` result instructing the LLM
  to say (in one sentence) that it's opening the module.
- `ChatResponse.ui_actions` flows through the SSE `done` event; `ChatDock` renders
  `navigate` actions as an "Open <module>" button (Next `Link`).

## Consequences

- General + data-driven: any future guided-UI module gets chat→page routing by
  setting `ui_route` — no per-module orchestrator code.
- The dock stays stateless; no per-module conversation state to manage.
- FR-016 "start from Chat" is satisfied via one-click navigation, not inline Q&A.
- If genuine inline multi-turn is ever required, revisit (it needs orchestrator
  session-scoped module state).

Builds on `vault/decisions/agent-runtime.md` (UIAction model is from task 02).
