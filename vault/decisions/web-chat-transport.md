---
id: decision-web-chat-transport
title: Web chat transport = streaming route handler + client-side SSE and history
kind: decision
owner: demo
updated_at: "2026-06-06"
---

# Web chat transport = streaming route handler + client-side SSE and history

## Decision

The chat dock streams via a **Next.js route handler** (`web/app/api/chat/route.ts`)
that is a pure passthrough of the orchestrator's SSE stream, and the **client**
(`ChatDock.tsx`) reads that stream with a small SSE parser (`web/lib/sse.ts`).
Conversation history is kept **client-side in `sessionStorage`** (per tab). This
replaces the task spec's `app/actions/chat.ts` server action and any server-side
history load.

## Context

The task 02 file list named a server action `chat_send` and S3 session restore on
the web side. Two constraints made the route-handler path correct instead:

1. **Server Actions can't stream incrementally to the browser.** They return a
   single serialized result; token-by-token streaming needs an HTTP response whose
   body is a `ReadableStream` — i.e. a route handler. The explicit smoke-test
   target is "tokens stream incrementally in the browser through Amplify SSR," so
   the transport must stream end to end.
2. **The SSR role is least-privilege** (`vault/decisions/poc-runtime.md`): it may
   only `lambda:InvokeFunctionUrl` the orchestrator — no S3. So the web layer
   cannot read the S3 session document to restore history. The orchestrator still
   persists turns to S3 for durability/audit; the browser keeps its own transcript.

## Consequences

- `web/app/api/chat/route.ts` signs (SigV4, aws4fetch) and forwards to the
  orchestrator Function URL, then returns `new Response(upstream.body)` with
  `text/event-stream` + `no-transform` + `X-Accel-Buffering: no` — no buffering.
  It gates on the `auth_ok` cookie because `/api` is excluded from the middleware.
- `ChatDock.tsx` persists the transcript + session id in `sessionStorage`:
  survives refresh (restores history), not shared across tabs (a new tab = a new
  session) — matching the spec's session semantics without an S3 read.
- The dock is mounted in the `(authenticated)` layout, so it persists across
  navigation within a session.
- If durable cross-device history is ever needed, add a read path **through the
  orchestrator** (not by widening the SSR role's S3 access).
