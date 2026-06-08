"""AGENT-01 — the Chat orchestrator.

A Bedrock Converse tool-loop (see ``vault/decisions/agent-runtime.md``) over five
tools. Two entry points share one dispatch path:

  - :meth:`ChatOrchestrator.respond` — non-streaming; returns a full ChatResponse.
    Used by tests and any non-streaming caller.
  - :meth:`ChatOrchestrator.stream` — yields SSE-ready events token-by-token for
    first-token latency (NFR-001); the Fargate server relays these to the proxy.

Behavior rules come from ``agents.md`` (cached, hot-reloaded) folded into the
system prompt every turn. The Bedrock guardrail is applied to this agent only.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from agents.lib import models as lib_models
from agents.lib.base_agent import BaseAgent, instrumented
from agents.lib.bedrock_client import BedrockClient

from .cache import ConfigCache
from .models import ChatRequest, ChatResponse, Citation
from .tools import describe_module, list_modules, read_agents_md
from .tools.invoke_module import ModuleInvoker
from .tools.search_knowledge_base import KnowledgeBaseSearcher

AGENT_ID = "AGENT-01"
MAX_TOOL_TURNS = 6

BASE_SYSTEM = """You are the Chat orchestrator for the AI CoE Platform — the front \
door to a library of reference assets, tools, vendor notes, regulations, news, \
prompts, and a set of specialized modules.

Operating rules:
- Use `search_knowledge_base` for any knowledge question, then ground your answer \
in the results and ALWAYS cite the sources you used.
- Use `describe_module` and `list_modules` for meta-questions about the platform \
("what does Module 4 do?", "list wave 3 modules").
- Use `invoke_module` when the user wants to DO something a specific module owns \
(assess, build, generate, check). If a module is not yet available you will get a \
`not_implemented` result — relay that plainly; never pretend it ran.
- Never invent file paths, module ids, or capabilities not present in tool results.
- Refuse requests that target named companies, or that seek secrets, credentials, \
environment variables, or PII.
- Be concise and plain-spoken. Stream your answer; don't wait to finish before \
showing text.

The behavior rules below come from the live agents.md config and take precedence \
over style preferences above where they conflict:

"""

# --- Converse toolConfig ---------------------------------------------------
TOOL_SPECS: list[dict] = [
    {
        "toolSpec": {
            "name": "search_knowledge_base",
            "description": (
                "Semantic search over the vault (assets, tools, vendors, regs, feed, "
                "prompts, decisions, assessments, kits). Returns citations to ground answers."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query."},
                        "top_k": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
                        "content_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "asset", "tool", "vendor", "reg", "feed",
                                    "prompt", "decision", "assessment", "kit",
                                ],
                            },
                            "description": "Optional filter to specific content types.",
                        },
                    },
                    "required": ["query"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "describe_module",
            "description": "Return the purpose, when-to-use, and example queries for one module.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "module_id": {"type": "string", "description": "e.g. 'module-4'"}
                    },
                    "required": ["module_id"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "list_modules",
            "description": "List modules, optionally filtered by wave and/or a keyword.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "wave": {"type": "integer", "minimum": 1, "maximum": 7},
                        "keyword": {"type": "string"},
                    },
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "invoke_module",
            "description": (
                "Route the user's request to a module's agent. Use when the user wants to "
                "perform an action a module owns. Returns the module's structured response, "
                "or a not_implemented stub if the module isn't enabled yet."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "module_id": {"type": "string"},
                        "payload": {"type": "object", "description": "Arguments for the module."},
                    },
                    "required": ["module_id"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "read_agents_md",
            "description": "Return the current agents.md behavior rules (live config).",
            "inputSchema": {"json": {"type": "object", "properties": {}}},
        }
    },
]

TOOL_CONFIG = {"tools": TOOL_SPECS}


@dataclass
class _Accumulator:
    """Per-request side-channel: citations and module invocations the tools produce."""

    citations: list[Citation] = field(default_factory=list)
    invoked_modules: list[str] = field(default_factory=list)

    def add_citations(self, cites: list[Citation]) -> None:
        seen = {(c.file_path, c.chunk_index) for c in self.citations}
        for c in cites:
            if (c.file_path, c.chunk_index) not in seen:
                self.citations.append(c)
                seen.add((c.file_path, c.chunk_index))


class ChatOrchestrator(BaseAgent):
    agent_id = AGENT_ID
    model_id = lib_models.SONNET_4_6

    def __init__(
        self,
        *,
        cache: ConfigCache,
        bedrock_client: BedrockClient | None = None,
        searcher: KnowledgeBaseSearcher | None = None,
        invoker: ModuleInvoker | None = None,
        guardrail_id: str | None = None,
        metrics_client: Any = None,
    ) -> None:
        super().__init__(metrics_client=metrics_client)
        self.cache = cache
        self.bedrock = bedrock_client or BedrockClient()
        self.searcher = searcher or KnowledgeBaseSearcher(registry_provider=cache)
        self.invoker = invoker or ModuleInvoker(registry_provider=cache)
        self.guardrail_id = guardrail_id if guardrail_id is not None else os.getenv("GUARDRAIL_ID")

    # --- prompt assembly ---------------------------------------------------
    def _system_prompt(self, request: ChatRequest) -> str:
        prompt = BASE_SYSTEM + self.cache.agents_md
        if request.current_route:
            prompt += f"\n\nContext: the user is currently on the page '{request.current_route}'."
        return prompt

    def _initial_messages(self, request: ChatRequest, history: list[dict]) -> list[dict]:
        return [*history, {"role": "user", "content": [{"text": request.message}]}]

    # --- tool dispatch -----------------------------------------------------
    def _dispatch(
        self, name: str, tool_input: dict, *, request_id: str, accum: _Accumulator
    ) -> dict:
        """Execute one tool and return a JSON-serializable result for the model."""
        if name == "search_knowledge_base":
            cites = self.searcher.search(
                tool_input["query"],
                top_k=int(tool_input.get("top_k", 5)),
                content_types=tool_input.get("content_types"),
            )
            accum.add_citations(cites)
            return {"results": [c.model_dump() for c in cites]}
        if name == "describe_module":
            result = describe_module(tool_input["module_id"], registry=self.cache.registry)
            return result if isinstance(result, dict) else result.model_dump()
        if name == "list_modules":
            rows = list_modules(
                wave=tool_input.get("wave"),
                keyword=tool_input.get("keyword"),
                registry=self.cache.registry,
            )
            return {"modules": [r.model_dump() for r in rows]}
        if name == "invoke_module":
            module_id = tool_input["module_id"]
            result = self.invoker.invoke(module_id, tool_input.get("payload", {}))
            if module_id not in accum.invoked_modules:
                accum.invoked_modules.append(module_id)
            return result
        if name == "read_agents_md":
            return {"agents_md": read_agents_md(cache=self.cache)}
        return {"status": "error", "message": f"Unknown tool '{name}'."}

    def _run_tool_blocks(
        self, tool_uses: list[dict], *, request_id: str, accum: _Accumulator
    ) -> list[dict]:
        """Run each requested tool (instrumented) and build Converse toolResult blocks."""
        results: list[dict] = []
        for tu in tool_uses:
            name = tu["name"]
            tool_use_id = tu["toolUseId"]
            try:
                result = self.run_tool(
                    name,
                    lambda _usage, _n=name, _i=tu["input"]: self._dispatch(
                        _n, _i, request_id=request_id, accum=accum
                    ),
                    request_id=request_id,
                )
                status = "success"
            except Exception as exc:  # noqa: BLE001 — logged by run_tool; degrade gracefully
                result = {"status": "error", "message": f"{type(exc).__name__}: {exc}"}
                status = "error"
            results.append(
                {
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": [{"json": result}],
                        "status": status,
                    }
                }
            )
        return {"role": "user", "content": results}

    # --- non-streaming -----------------------------------------------------
    def respond(self, request: ChatRequest, history: list[dict] | None = None) -> ChatResponse:
        messages = self._initial_messages(request, history or [])
        system = self._system_prompt(request)
        accum = _Accumulator()

        for _ in range(MAX_TOOL_TURNS):
            with instrumented(
                agent_id=self.agent_id,
                tool_name="bedrock:converse",
                request_id=request.request_id,
                session_id=request.session_id,
                display_name=request.display_name,
                model_id=self.model_id,
                metrics_client=self.metrics_client,
            ) as usage:
                resp = self.bedrock.converse(
                    model_id=self.model_id,
                    messages=messages,
                    system=system,
                    max_tokens=2048,
                    tool_config=TOOL_CONFIG,
                    guardrail_id=self.guardrail_id,
                    usage=usage,
                )
            stop_reason = resp.get("stopReason")
            output_msg = resp.get("output", {}).get("message", {})
            messages.append(output_msg)

            if stop_reason == "guardrail_intervened":
                return self._refusal(output_msg)
            tool_uses = _extract_tool_uses(output_msg)
            if stop_reason == "tool_use" and tool_uses:
                messages.append(
                    self._run_tool_blocks(tool_uses, request_id=request.request_id, accum=accum)
                )
                continue
            return ChatResponse(
                assistant_message=_extract_text(output_msg),
                citations=accum.citations,
                invoked_modules=accum.invoked_modules,
            )

        # Tool-turn budget exhausted — return whatever text we have, gracefully.
        return ChatResponse(
            assistant_message=(
                "I wasn't able to fully resolve that. Could you rephrase or narrow the request?"
            ),
            citations=accum.citations,
            invoked_modules=accum.invoked_modules,
        )

    def _refusal(self, output_msg: dict) -> ChatResponse:
        text = _extract_text(output_msg) or "This request can't be processed."
        return ChatResponse(assistant_message=text)

    # --- streaming ---------------------------------------------------------
    def stream(self, request: ChatRequest, history: list[dict] | None = None):
        """Yield SSE-ready event dicts. Event types: token, tool, citation, done, error."""
        messages = self._initial_messages(request, history or [])
        system = self._system_prompt(request)
        accum = _Accumulator()

        try:
            for _ in range(MAX_TOOL_TURNS):
                text_acc = ""
                tool_uses: list[dict] = []
                stop_reason = None

                with instrumented(
                    agent_id=self.agent_id,
                    tool_name="bedrock:converse_stream",
                    request_id=request.request_id,
                    session_id=request.session_id,
                    display_name=request.display_name,
                    model_id=self.model_id,
                    metrics_client=self.metrics_client,
                ) as usage:
                    for ev in self.bedrock.converse_stream(
                        model_id=self.model_id,
                        messages=messages,
                        system=system,
                        max_tokens=2048,
                        tool_config=TOOL_CONFIG,
                        guardrail_id=self.guardrail_id,
                        usage=usage,
                    ):
                        if ev["type"] == "text":
                            text_acc += ev["text"]
                            yield {"event": "token", "data": {"text": ev["text"]}}
                        elif ev["type"] == "tool_use":
                            tool_uses.append(ev["tool_use"])
                        elif ev["type"] == "stop":
                            stop_reason = ev["stop_reason"]

                messages.append(_assistant_message(text_acc, tool_uses))

                if stop_reason == "guardrail_intervened":
                    msg = text_acc or "This request can't be processed."
                    yield {
                        "event": "done",
                        "data": ChatResponse(assistant_message=msg).model_dump(),
                    }
                    return

                if tool_uses:
                    for tu in tool_uses:
                        yield {"event": "tool", "data": {"name": tu["name"]}}
                    before = len(accum.citations)
                    messages.append(
                        self._run_tool_blocks(
                            tool_uses, request_id=request.request_id, accum=accum
                        )
                    )
                    for c in accum.citations[before:]:
                        yield {"event": "citation", "data": c.model_dump()}
                    continue

                yield {
                    "event": "done",
                    "data": ChatResponse(
                        assistant_message=text_acc,
                        citations=accum.citations,
                        invoked_modules=accum.invoked_modules,
                    ).model_dump(),
                }
                return

            yield {
                "event": "done",
                "data": ChatResponse(
                    assistant_message=(
                        "I wasn't able to fully resolve that. Could you rephrase the request?"
                    ),
                    citations=accum.citations,
                    invoked_modules=accum.invoked_modules,
                ).model_dump(),
            }
        except Exception as exc:  # noqa: BLE001 — surface a clean error event, never a raw stack
            yield {
                "event": "error",
                "data": {"message": "I had trouble processing that, please rephrase."},
            }
            # Re-log shape for observability; the instrumented block already recorded it.
            print(
                json.dumps(
                    {"event": "stream_error", "agent_id": self.agent_id, "error": str(exc)},
                    separators=(",", ":"),
                )
            )


# --- Converse message helpers ---------------------------------------------
def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()


def _extract_tool_uses(message: dict) -> list[dict]:
    out: list[dict] = []
    for block in message.get("content", []):
        if "toolUse" in block:
            tu = block["toolUse"]
            out.append(
                {"toolUseId": tu["toolUseId"], "name": tu["name"], "input": tu.get("input", {})}
            )
    return out


def _assistant_message(text: str, tool_uses: list[dict]) -> dict:
    """Rebuild the assistant Converse message after a streamed turn."""
    content: list[dict] = []
    if text:
        content.append({"text": text})
    for tu in tool_uses:
        content.append(
            {
                "toolUse": {
                    "toolUseId": tu["toolUseId"],
                    "name": tu["name"],
                    "input": tu.get("input", {}),
                }
            }
        )
    if not content:
        content.append({"text": ""})
    return {"role": "assistant", "content": content}
