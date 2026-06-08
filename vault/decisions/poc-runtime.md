---
id: decision-poc-runtime-streaming-lambda
title: POC orchestrator runtime = streaming Lambda; defer Fargate-warm to real traffic
kind: decision
owner: demo
updated_at: "2026-06-06"
---

# POC orchestrator runtime = streaming Lambda; defer Fargate-warm to real traffic

## Decision

For the POC, AGENT-01 (Chat orchestrator) runs as a **container Lambda with HTTP
response streaming** — Lambda Web Adapter + a Function URL with
`InvokeMode=RESPONSE_STREAM` and IAM auth — instead of the originally specced
**Fargate Spot service behind an internal ALB + a separate proxy Lambda**. This
drops idle cost to ~$0. The Fargate-warm topology is kept as a documented,
**un-deployed** scale-up path and promoted only when real traffic makes cold
starts unacceptable.

## Context

The task 02 spec (AD-01/AD-02) put the orchestrator on warm Fargate behind an ALB,
fronted by a response-streaming proxy Lambda. For a solo, pre-traffic POC that's
mostly idle, an always-on Fargate task + ALB + NAT bills 24/7 for nothing. A
streaming Lambda bills only per request and still streams first tokens.

## Options considered

| Option | Why not / why |
|---|---|
| Fargate Spot + internal ALB + proxy Lambda (original spec) | Always-on cost (task + ALB + NAT) with no traffic; more moving parts (ALB, proxy). Right once warm latency matters. |
| **Streaming Lambda (LWA + Function URL, RESPONSE_STREAM)** | **Chosen** — ~$0 idle, streams via SSE, reuses the exact same container image, no ALB, no proxy. |
| Node.js streaming shim in front of a Python Lambda | Keeps the literal `InvokeWithResponseStream` API but reintroduces a proxy and a second language; rejected. |

## Consequences

- The orchestrator **is** `aicoe-fargate-orchestrator-endpoint-lambda` (name kept
  from the foundation so the SSR role + `web/lib/aws.ts` need no rewiring). It runs
  the FastAPI `agents/orchestrator/server.py` under the Lambda Web Adapter.
- **Transport changed from `InvokeWithResponseStream` to a Function URL**: Python
  can't stream from the managed runtime, and LWA streaming is documented only via a
  Function URL. The SSR role's grant becomes `lambda:InvokeFunctionUrl` (IAM-authed
  URLs only); `web/lib/aws.ts` uses a SigV4 streaming fetch; the URL is injected
  into Amplify as `AICOE_ORCHESTRATOR_URL`.
- **Config hot-reload split**: per-invocation `refresh_if_stale` on Lambda (the env
  is frozen between invocations, so the 60s daemon can't tick); the daemon
  (`start_refresh_loop`) is kept in `server.py` for local dev and the Fargate path.
- **No ALB, no separate proxy Lambda** (`agents/proxy/` is not created).
- The Fargate variant lives in `infra/stacks/agents_fargate.py`, **not** wired into
  `app.py`; the container image is identical, so promotion is config-only.

Refines (does not contradict) AD-01/AD-02 for the POC phase. See
`vault/decisions/agent-runtime.md` for the related runtime decision.
