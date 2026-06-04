# Task: Wave 1 — Chat Orchestrator (AGENT-01)

> **Phase:** 1
> **Feature group:** Wave 1 (Foundation)
> **Covers:** FR-002 (chat dock), FR-003 (RAG + citations), FR-006 (describe module), FR-007 (list modules), FR-008 (invoke module), FR-009 (route correctness)
> **Builds:** AGENT-01 (Chat Orchestrator, Sonnet 4.6, Fargate)
> **Depends on:** 00_foundation, 01_wave1_vault_seed_content
> **Blocks:** every module task (each module needs Chat to invoke its agent)
> **Estimated effort:** 4-5 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** A user can open a persistent chat dock on any page, ask a question about vault content, and get a streamed response with citations. Chat can describe any module and route to a (not-yet-built) module agent.

**Build steps:**

1. **Build AGENT-01 in `agents/orchestrator/`** (Strands agent, Sonnet 4.6, 5 tools) → Verify: local unit test of each tool returns the expected schema.
2. **Containerize the orchestrator** (Dockerfile, ECR push) → Verify: image pushed to ECR.
3. **CDK: Fargate Spot service** behind internal ALB + ECR + log group → Verify: Fargate task `RUNNING`; ALB target healthy.
4. **CDK: orchestrator proxy Lambda** (response-streaming-enabled) → Verify: invoking the proxy returns a streamed response from Fargate.
5. **Apply Bedrock Guardrails** to AGENT-01 only → Verify: a prompt-attack input returns the guardrail refusal.
6. **Next.js chat dock UI** (persistent, Server-Sent Events stream consumer) → Verify: dock renders on every authenticated route; opens/closes; persists conversation across navigation within a session.
7. **Next.js server action `chat_send`** that invokes the proxy Lambda → Verify: typing a message streams a response token-by-token.
8. **Session persistence** to S3 at `sessions/{display_name}/{session_id}.json` → Verify: refresh restores history; new tab starts a new session.
9. **modules.json hot reload** every 60s in Fargate task → Verify: editing modules.json changes Chat's `list_modules` output by the next turn.
10. **agents.md hot reload** every 60s → Verify: editing agents.md changes routing behavior on the next turn (FR-005).

**Files to create/edit:**

- `agents/orchestrator/agent_01_chat.py` — AGENT-01 definition
- `agents/orchestrator/tools/search_knowledge_base.py` — RAG over S3 Vectors
- `agents/orchestrator/tools/describe_module.py` — registry meta-query
- `agents/orchestrator/tools/list_modules.py` — filtered registry browse
- `agents/orchestrator/tools/invoke_module.py` — lambda:Invoke wrapper
- `agents/orchestrator/tools/read_agents_md.py` — config refresh
- `agents/orchestrator/server.py` — Fargate HTTP server (FastAPI thin wrapper, SSE streaming)
- `agents/orchestrator/Dockerfile` — slim Python 3.12 + uv
- `agents/orchestrator/refresh.py` — modules.json + agents.md hot-reload loop
- `agents/proxy/handler.py` — orchestrator proxy Lambda (response-streaming)
- `infra/stacks/agents.py` — Fargate service + ALB + proxy Lambda
- `web/components/ChatDock.tsx` — persistent chat UI
- `web/app/(authenticated)/layout.tsx` — mount ChatDock
- `web/app/api/chat/route.ts` — Next.js streaming route handler
- `web/app/actions/chat.ts` — server action invoking proxy Lambda
- `web/lib/sse.ts` — SSE client helper

**Done when:**

- [ ] All listed FRs have passing smoke tests
- [ ] First-token p95 < 3s (NFR-001) on warm Fargate
- [ ] Chat dock visible on every authenticated page
- [ ] Citations clickable and link to Asset Library entries (or to the file path if Asset Library not yet built for that content type)
- [ ] modules.json + agents.md changes reflect in Chat behavior within 60s
- [ ] Guardrail-blocked input returns a clean refusal message, not a crash
- [ ] DoD checklist from `00_foundation.md` passed

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are implementing **AGENT-01 (Chat Orchestrator)**, the Layer 1 front-door agent for the AI CoE Platform. Task 00 (Foundation) and task 01 (Vault Seed Content) are done.

#### Project context

- Hierarchical multi-agent platform: 1 orchestrator (Sonnet 4.6) + 26 module agents (later tasks) + 16 task workers (later tasks).
- Per AD-01, the orchestrator runs on Fargate Spot (warm). Module agents and workers run on Lambda (cold-startable, called by orchestrator during streaming).
- Per AD-02, Next.js server actions invoke a thin proxy Lambda (response-streaming) via AWS SDK. Proxy forwards to Fargate internal ALB. No API Gateway, no FastAPI service exposed publicly.
- Per AD-03, the module registry is `vault/modules.json` (single file). Orchestrator hot-reloads it every 60s.
- Per AD-04, session state is JSON in S3 at `sessions/{display_name}/{session_id}.json`.
- Foundation (task 00) provides: 5 IAM roles, S3 vault + sessions buckets, S3 Vectors index `aicoe-content`, Bedrock Guardrails policy ARN, ReEmbed Lambda, Vercel-AWS OIDC, observability conventions (log shape + metrics + alarms), shared agents lib at `agents/lib/`.

#### What you are building

**Goal:** Chat first-token p95 < 3s with streaming, RAG citations, module routing, registry meta-queries, configurable behavior via agents.md.

**Functional requirements covered:**

- **FR-002:** User can chat from any authenticated page via persistent dock.
- **FR-003:** Chat retrieves from vault via S3 Vectors, returns citations linking to Asset Library entries (or file paths when Asset Library is not yet built).
- **FR-006:** Chat can describe any module ("what does Module 4 do?") using `describe_module` against modules.json.
- **FR-007:** Chat can list modules filtered by wave / purpose / keyword via `list_modules`.
- **FR-008:** Chat invokes a module agent via `invoke_module` (returns a stub response in Wave 1 since module agents are not yet built; real responses arrive as later waves add them).
- **FR-009:** Chat routes correctly: a query matching Module 1 keywords invokes AGENT-02 (not yet built; returns NotImplemented gracefully).

#### Agent specification (AGENT-01)

```python
class ChatRequest(BaseModel):
    display_name: str
    session_id: str
    request_id: str
    message: str
    current_route: str | None = None

class Citation(BaseModel):
    file_path: str
    chunk_index: int
    content_type: Literal["asset", "tool", "vendor", "reg", "feed", "prompt", "decision", "assessment", "kit"]
    asset_library_url: str | None  # populated if Asset Library exists for this type

class UIAction(BaseModel):
    type: Literal["navigate", "open_panel", "start_assessment", "start_kit_builder", "show_module_card"]
    payload: dict

class ChatResponse(BaseModel):
    assistant_message: str
    citations: list[Citation]
    invoked_modules: list[str]
    ui_actions: list[UIAction]
```

Tools (5):

```python
def search_knowledge_base(query: str, top_k: int = 5, content_types: list[str] | None = None) -> list[Citation]:
    """RAG over S3 Vectors. Embed query via Titan Embed v2, query index, return citations."""

def describe_module(module_id: str) -> ModuleDescription:
    """Look up module in modules.json registry. Return purpose, when_to_use, example_queries."""

def list_modules(wave: int | None = None, keyword: str | None = None) -> list[ModuleSummary]:
    """Filter and list modules from the registry."""

def invoke_module(module_id: str, payload: dict) -> dict:
    """lambda:Invoke aicoe-module-agents-lambda with routing key. Returns module agent's structured response. If the module is not yet enabled in the registry, return {'status': 'not_implemented', 'message': '...'}."""

def read_agents_md() -> str:
    """Return current contents of vault/agents.md from in-memory cache (refreshed every 60s)."""
```

System prompt outline:

- You are the Chat orchestrator for the AI CoE Platform.
- Load behavior rules from agents.md at the start of every turn (already cached, read via `read_agents_md`).
- Use `search_knowledge_base` for knowledge questions.
- Use `describe_module` / `list_modules` for meta-queries about the platform.
- Use `invoke_module` when the user wants to do something a specific module owns.
- Always cite sources. If you cite an asset, include its asset_library_url (or note "view in vault" if not browseable yet).
- Stream responses. Never wait for full completion before showing tokens.
- Refuse: requests that target named companies, secrets, credentials, or PII.

Failure handling:

- Tool failure: emit a log line with `outcome: schema_failure | llm_error | timeout`, retry once with simplified prompt, then fall back to a "I had trouble processing that, please rephrase" message.
- Guardrail trip: return guardrail's refusal text, log `outcome: refused`, do not retry.

#### Fargate + proxy Lambda topology

```
Browser
  ↓ (SSE GET /api/chat)
Next.js server action `chat_send`
  ↓ (lambda:InvokeWithResponseStream, sigv4)
Proxy Lambda (aicoe-orchestrator-proxy)
  ↓ (HTTP to internal ALB)
Internal ALB
  ↓
Fargate task running agents/orchestrator/server.py
  ↓ (Strands + Bedrock + tools)
Bedrock (Sonnet 4.6 + Guardrails)
```

Streaming: Bedrock streams to Strands → server.py yields SSE events → ALB → proxy Lambda streams response → Next.js server action streams to browser via Response object.

#### IAM permission deltas (add to existing roles from task 00)

```
aicoe-fargate-orchestrator-role:
  - Already has: lambda:Invoke on module-agents-lambda, bedrock:InvokeModel*, s3 vault+sessions read/write, s3vectors:QueryVectors+PutVectors, cloudwatch:PutMetricData
  - Add: bedrock:ApplyGuardrail on the guardrail ARN

aicoe-proxy-lambda-role (NEW, but follows same pattern):
  - lambda.amazonaws.com trust
  - Invoke internal ALB target (network access only, no IAM action)
  - logs:* on its log group
  - cloudwatch:PutMetricData

aicoe-vercel-oidc-role:
  - Add: lambda:InvokeFunctionUrl OR lambda:InvokeWithResponseStream on aicoe-orchestrator-proxy ARN
```

#### Implementation steps

1. **Build AGENT-01** (`agents/orchestrator/agent_01_chat.py`): subclass of `BaseAgent` from `agents/lib/`. Register 5 tools. System prompt loads from agents.md (cached). Cost tracking via `bedrock_client.py`.

2. **Implement each tool** in `agents/orchestrator/tools/`:
   - `search_knowledge_base.py`: embed query → s3vectors query → return Citation list (compute asset_library_url from content_type)
   - `describe_module.py`: read cached modules.json → return ModuleDescription
   - `list_modules.py`: read cached modules.json → filter → return ModuleSummary list
   - `invoke_module.py`: lambda:Invoke aicoe-module-agents-lambda with payload `{agent_id, args}`. On NotEnabled response from registry, return stub.
   - `read_agents_md.py`: return cached agents.md (refreshed by background loop in `refresh.py`)

3. **Write `server.py`** (FastAPI in Fargate): one POST endpoint `/chat` that accepts ChatRequest, invokes AGENT-01, streams SSE events back. Background task: `refresh.py` reloads modules.json + agents.md every 60s.

4. **Dockerfile + ECR push**: slim Python 3.12 base, uv for dependency install, runs `uvicorn agents.orchestrator.server:app`.

5. **CDK Fargate service** (`infra/stacks/agents.py`):
   - ECS cluster (Fargate Spot capacity provider)
   - Task definition: 0.25 vCPU, 0.5 GB RAM, ARM64
   - Service: desired count 1, health check via ALB
   - Internal ALB: HTTP listener on port 80, target group health check `/healthz`
   - CloudWatch log group with 30-day retention

6. **Proxy Lambda** (`agents/proxy/handler.py`):
   - Response streaming enabled (`responseStreaming: true`)
   - Receives event payload, forwards as HTTP POST to internal ALB
   - Streams ALB response chunks back as Lambda response stream

7. **Apply Guardrail to AGENT-01**: in `bedrock_client.py`, when called from AGENT-01 only, attach `guardrailIdentifier`. Read guardrail ARN from environment variable set by CDK.

8. **Chat dock UI** (`web/components/ChatDock.tsx`): fixed-bottom-right dock, expand/collapse, message list, input field, "Stop" button, citations rendered as clickable badges. Use shadcn `Sheet` or custom positioned div.

9. **Server action `chat_send`** (`web/app/actions/chat.ts`): builds ChatRequest, calls `lambda:InvokeWithResponseStream` via AWS SDK (using OIDC role), returns a streaming Response to the client.

10. **SSE consumer** (`web/lib/sse.ts`): parses SSE events, dispatches token-by-token to chat state.

11. **Session persistence**: each turn appends to `sessions/{display_name}/{session_id}.json` in S3. On dock open, load history. Session ID generated on first message of a new browser session.

12. **Smoke tests**:
    - Login, open dock, ask "What does Module 4 do?" → describe_module returns purpose, when_to_use, example_queries
    - Ask "List wave 3 modules" → list_modules returns 3 entries
    - Ask "Healthcare reference architecture for clinical notes" → search_knowledge_base cites the seed asset; UI renders citation badge clickable
    - Ask "Assess my client" → invoke_module is called for AGENT-02; returns NotImplemented stub gracefully
    - Edit agents.md to add a rule "Always end with 'Anything else?'" → next turn ends with that phrase
    - Send a known prompt-injection input → Guardrail refusal text displayed; outcome=refused logged

#### Definition of done

- [ ] All FRs listed have smoke tests passing
- [ ] First-token p95 < 3s on warm Fargate, measured with 10 representative queries
- [ ] Chat dock visible on every authenticated page
- [ ] Citations clickable
- [ ] modules.json + agents.md hot-reload within 60s
- [ ] Guardrail refusal works
- [ ] Streaming SSE works end-to-end (no buffering at ALB or proxy)
- [ ] Session persists across page navigation
- [ ] DoD checklist from `00_foundation.md` passed

#### Behavioral guardrails

Same as task 00. Plus: do not introduce a database; session storage is S3 JSON only (AD-04). Do not add API Gateway (AD-02). Do not split the orchestrator into multiple Lambdas (AD-01).

#### Out of scope

- Module agent implementations (later tasks, one per module)
- Task worker implementations (later tasks)
- Cognito or real auth (post-demo-plan.md Section 1)
- Multi-session UI (one active session at a time per browser is enough)
- WebSocket upgrade (SSE is sufficient per design Q-04 default)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
- 2026-06-03: created. Streaming via SSE per design Q-04 default. Proxy Lambda pattern resolves design Q-07.

## D. References
- Brief: `ai_docs/brief.md` Sections 5.1-5.2 (FRs), 6.2 (AGENT-01 spec), 12.2 (models), 15.1 (Wave 1)
- Design: `ai_docs/design.md` Section 5.2 (AGENT-01), Section 6 Flow 1, Section 9 (Q-01, Q-04, Q-07)
- Foundation: `ai_docs/tasks/00_foundation.md`
