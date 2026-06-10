"""AGENT-25 — Universal Asset Q&A (Module 26), Sonnet 4.6 tier.

The first Layer 2 module agent that runs a **Bedrock Converse tool-loop** (the
orchestrator's AGENT-01 pattern, see ``vault/decisions/agent-runtime.md``), but
scoped to ONE asset: the asset's full markdown body and frontmatter are baked
into the system prompt, and the model answers questions grounded in that single
document. It refuses questions unrelated to the asset.

Three tools, used only when the user reaches beyond the one asset:
  - ``read_asset(asset_id)``                       — pull another asset to compare
  - ``search_vector_index_scoped(query, ...)``     — cross-asset semantic search,
    excluding the asset in context
  - ``summarize_for_role(role)``                   — role-specific framing guide
    (executive / engineer / compliance / product) the model applies to the
    in-context content; deterministic, no nested LLM call

Asset reads/search compose :class:`AssetLibraryAgent` (AGENT-03) so the S3 +
S3 Vectors plumbing and content-type filtering live in exactly one place. No
Bedrock guardrail is applied here (the module-agents role has no
``ApplyGuardrail`` grant); refusal of off-asset questions is steered by the
system prompt instead.

Invoked synchronously by the web ``asset_qa`` server action via Lambda invoke,
so this is **non-streaming** — ``handle`` returns the full response in one shot.
"""

from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, Field

from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .agent_03_asset_library import AssetLibraryAgent
from .base import ModuleAgent

AGENT_ID = "AGENT-25"
MAX_TOOL_TURNS = 5
ASSET_LIBRARY_ROUTE = "/modules/asset-library"

# Role framings for ``summarize_for_role``. The asset content is already in the
# system prompt; this tool returns *how* to frame a summary for a given audience,
# which the model then applies. Deterministic and fully testable.
ROLE_FRAMINGS: dict[str, dict[str, Any]] = {
    "executive": {
        "audience": "senior leadership / decision-makers",
        "emphasize": ["business value", "risk and cost", "the decision to be made", "timeline"],
        "format": "3-5 crisp bullets, plain language, no jargon; lead with the bottom line.",
    },
    "engineer": {
        "audience": "implementing engineers / architects",
        "emphasize": ["architecture and components", "data flow", "trade-offs", "build steps"],
        "format": "structured technical summary with concrete components and sequencing.",
    },
    "compliance": {
        "audience": "risk, compliance, and governance reviewers",
        "emphasize": [
            "regulatory considerations",
            "controls and safeguards",
            "residual risks",
            "audit/evidence needs",
        ],
        "format": "a checklist of considerations, each phrased as an actionable control.",
    },
    "product": {
        "audience": "product managers and delivery leads",
        "emphasize": ["user value", "scope and milestones", "dependencies", "success metrics"],
        "format": "short narrative plus a milestone list.",
    },
}
_ROLE_ALIASES = {
    "exec": "executive",
    "executive": "executive",
    "leadership": "executive",
    "engineer": "engineer",
    "engineering": "engineer",
    "technical": "engineer",
    "developer": "engineer",
    "architect": "engineer",
    "compliance": "compliance",
    "risk": "compliance",
    "governance": "compliance",
    "regulatory": "compliance",
    "legal": "compliance",
    "product": "product",
    "pm": "product",
    "delivery": "product",
}

DEFAULT_SUGGESTIONS = [
    "Summarize this for an executive",
    "What are the key risks or considerations?",
    "Turn this into an action checklist",
    "Compare this to similar assets",
]

BASE_SYSTEM = """You are the Universal Asset Q&A assistant. You answer questions \
about ONE specific asset whose full content is provided below. Ground every answer \
in that content.

Rules:
- Answer from the asset content in context. Cite the sections you draw on by their \
markdown heading.
- Use `summarize_for_role` when the user wants a summary framed for a particular \
audience (executive, engineer, compliance, product); apply the framing it returns \
to the in-context content.
- Use `read_asset` only when the user asks to compare this asset to another named \
asset, and `search_vector_index_scoped` when they ask how this relates to other \
assets in the library. Do not pull other content unless asked.
- If the user asks something unrelated to this asset (general chit-chat, other \
topics, requests for secrets/credentials/PII, or named companies), politely decline \
and steer them back to questions about this asset.
- Be concise and plain-spoken.

--- ASSET IN CONTEXT ---
"""

# --- Converse toolConfig ---------------------------------------------------
TOOL_SPECS: list[dict] = [
    {
        "toolSpec": {
            "name": "read_asset",
            "description": (
                "Fetch the full body and frontmatter of ANOTHER asset by its id, so you "
                "can compare it to the asset in context. Do not use this for the asset "
                "already in context."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "asset_id": {"type": "string", "description": "The other asset's id."}
                    },
                    "required": ["asset_id"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "search_vector_index_scoped",
            "description": (
                "Semantic search over the asset library for assets related to a query, "
                "excluding the asset in context. Use when the user asks how this asset "
                "relates to, or compares with, similar assets."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
                        "exclude_asset_id": {
                            "type": "string",
                            "description": "Asset id to exclude (the asset in context).",
                        },
                    },
                    "required": ["query"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "summarize_for_role",
            "description": (
                "Return audience-specific framing guidance (what to emphasize and how to "
                "format) for summarizing the asset in context for a given role. Apply the "
                "returned framing to produce the summary."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "role": {
                            "type": "string",
                            "description": "e.g. executive, engineer, compliance, product.",
                        }
                    },
                    "required": ["role"],
                }
            },
        }
    },
]
TOOL_CONFIG = {"tools": TOOL_SPECS}


# --- wire models -----------------------------------------------------------
class AssetCitation(BaseModel):
    """A source the answer drew on. Superset-compatible with the chat dock's
    citation shape (file_path/content_type/asset_library_url) plus display fields."""

    asset_id: str
    title: str = ""
    file_path: str = ""
    content_type: str = "asset"
    asset_library_url: str | None = None


class AssetChatRequest(BaseModel):
    asset_id: str
    asset_content: str = ""
    asset_frontmatter: dict = Field(default_factory=dict)
    session_id: str = ""
    message: str
    # Client-side conversation history (the panel keeps it, like the chat dock).
    # Each item: {"role": "user"|"assistant", "text": "..."}.
    history: list[dict] = Field(default_factory=list)
    display_name: str = ""


class AssetChatResponse(BaseModel):
    assistant_message: str
    citations: list[AssetCitation] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class _Accumulator:
    """Per-request side-channel: citations the tools surface, de-duped by asset_id."""

    def __init__(self) -> None:
        self.citations: list[AssetCitation] = []
        self._seen: set[str] = set()
        self.searched = False

    def add(self, cite: AssetCitation) -> None:
        if cite.asset_id and cite.asset_id not in self._seen:
            self._seen.add(cite.asset_id)
            self.citations.append(cite)


class AssetQAAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.SONNET_4_6

    def __init__(
        self,
        *,
        bedrock_client: BedrockClient | None = None,
        asset_agent: AssetLibraryAgent | None = None,
        s3: Any = None,
        s3vectors: Any = None,
        bedrock: Any = None,
        vault_bucket: str | None = None,
        sessions_bucket: str | None = None,
        metrics_client: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(metrics_client=metrics_client, **kwargs)
        # Converse client for the chat loop (Sonnet 4.6).
        self.bedrock_client = bedrock_client or BedrockClient(client=bedrock)
        # AGENT-03 owns the S3 + S3 Vectors plumbing; compose it for read/search.
        self.asset_agent = asset_agent or AssetLibraryAgent(
            vault_bucket=vault_bucket,
            sessions_bucket=sessions_bucket,
            s3=s3,
            s3vectors=s3vectors,
            bedrock=bedrock,
            metrics_client=metrics_client,
        )

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        # Op is "chat" (or inferred from a message). Be liberal: ``id`` aliases
        # ``asset_id`` to match how the orchestrator/web may shape the payload.
        if "asset_id" not in args and args.get("id"):
            args = {**args, "asset_id": args["id"]}
        if not args.get("message"):
            return {"status": "error", "message": "message is required."}
        if not args.get("asset_id"):
            return {"status": "error", "message": "asset_id is required."}
        return self.run_tool("asset_qa_chat", lambda _u: self._chat(args))

    # --- prompt assembly ---------------------------------------------------
    def _system_prompt(self, req: AssetChatRequest) -> str:
        fm = req.asset_frontmatter or {}
        title = str(fm.get("title") or req.asset_id)
        try:
            fm_yaml = yaml.safe_dump(fm, sort_keys=False).strip() if fm else "(none)"
        except yaml.YAMLError:
            fm_yaml = "(unavailable)"
        return (
            f"{BASE_SYSTEM}"
            f"asset_id: {req.asset_id}\n"
            f"title: {title}\n\n"
            f"Frontmatter:\n{fm_yaml}\n\n"
            f"Content:\n{req.asset_content or '(no body provided)'}\n"
            "--- END ASSET ---\n"
        )

    def _initial_messages(self, req: AssetChatRequest) -> list[dict]:
        messages: list[dict] = []
        for turn in req.history:
            role = turn.get("role")
            text = turn.get("text") or turn.get("content") or ""
            if role in ("user", "assistant") and text:
                messages.append({"role": role, "content": [{"text": str(text)}]})
        messages.append({"role": "user", "content": [{"text": req.message}]})
        return messages

    # --- tool dispatch -----------------------------------------------------
    def _citation_for(self, asset_summary: dict) -> AssetCitation:
        aid = str(asset_summary.get("id", ""))
        return AssetCitation(
            asset_id=aid,
            title=str(asset_summary.get("title", "")),
            file_path=str(asset_summary.get("file_path", "")),
            content_type="asset",
            asset_library_url=f"{ASSET_LIBRARY_ROUTE}/{aid}" if aid else None,
        )

    def _dispatch(self, name: str, tool_input: dict, *, accum: _Accumulator, req: AssetChatRequest):
        if name == "read_asset":
            other_id = tool_input.get("asset_id")
            if not other_id:
                return {"status": "error", "message": "asset_id is required."}
            result = self.asset_agent.handle({"op": "get_asset", "asset_id": other_id})
            if result.get("status") == "ok":
                summary = result.get("asset", {}).get("summary", {})
                accum.add(self._citation_for(summary))
            return result
        if name == "search_vector_index_scoped":
            query = tool_input.get("query", "")
            exclude = tool_input.get("exclude_asset_id") or req.asset_id
            top_k = int(tool_input.get("top_k", 5))
            # Over-fetch by one so excluding the in-context asset still yields top_k.
            result = self.asset_agent.handle({"op": "search", "query": query, "top_k": top_k + 1})
            assets = [a for a in result.get("assets", []) if str(a.get("id")) != str(exclude)][
                :top_k
            ]
            accum.searched = True
            for a in assets:
                accum.add(self._citation_for(a))
            return {"status": "ok", "assets": assets}
        if name == "summarize_for_role":
            role_raw = str(tool_input.get("role", "")).strip().lower()
            canonical = _ROLE_ALIASES.get(role_raw)
            if canonical is None:
                return {
                    "status": "ok",
                    "role": role_raw or "general",
                    "framing": {
                        "audience": "a general reader",
                        "emphasize": ["the main purpose", "key points", "practical takeaways"],
                        "format": "a clear, concise summary.",
                    },
                }
            return {"status": "ok", "role": canonical, "framing": ROLE_FRAMINGS[canonical]}
        return {"status": "error", "message": f"Unknown tool '{name}'."}

    def _run_tool_blocks(self, tool_uses: list[dict], *, accum, req) -> dict:
        results: list[dict] = []
        for tu in tool_uses:
            try:
                result = self._dispatch(tu["name"], tu.get("input", {}), accum=accum, req=req)
                status = "success"
            except Exception as exc:  # noqa: BLE001 — degrade gracefully, never raise to the model
                result = {"status": "error", "message": f"{type(exc).__name__}: {exc}"}
                status = "error"
            results.append(
                {
                    "toolResult": {
                        "toolUseId": tu["toolUseId"],
                        "content": [{"json": result}],
                        "status": status,
                    }
                }
            )
        return {"role": "user", "content": results}

    # --- the loop ----------------------------------------------------------
    def _chat(self, args: dict[str, Any]) -> dict[str, Any]:
        req = AssetChatRequest.model_validate(args)
        system = self._system_prompt(req)
        messages = self._initial_messages(req)
        accum = _Accumulator()
        # The asset in context is always the primary grounding source.
        accum.add(
            AssetCitation(
                asset_id=req.asset_id,
                title=str((req.asset_frontmatter or {}).get("title") or req.asset_id),
                file_path=str((req.asset_frontmatter or {}).get("file_path", "")),
                content_type="asset",
                asset_library_url=f"{ASSET_LIBRARY_ROUTE}/{req.asset_id}",
            )
        )

        text = ""
        for _ in range(MAX_TOOL_TURNS):
            with instrumented(
                agent_id=self.agent_id,
                tool_name="bedrock:converse",
                session_id=req.session_id,
                display_name=req.display_name or None,
                model_id=self.model_id,
                metrics_client=self.metrics_client,
            ) as usage:
                resp = self.bedrock_client.converse(
                    model_id=self.model_id,
                    messages=messages,
                    system=system,
                    max_tokens=2048,
                    tool_config=TOOL_CONFIG,
                    usage=usage,
                )
            output_msg = resp.get("output", {}).get("message", {})
            messages.append(output_msg)
            stop_reason = resp.get("stopReason")
            tool_uses = _extract_tool_uses(output_msg)
            if stop_reason == "tool_use" and tool_uses:
                messages.append(self._run_tool_blocks(tool_uses, accum=accum, req=req))
                continue
            text = _extract_text(output_msg)
            break
        else:
            text = "I couldn't fully work through that. Could you rephrase the question?"

        return AssetChatResponse(
            assistant_message=text,
            citations=accum.citations,
            suggestions=self._suggestions(accum),
        ).model_dump() | {"status": "ok"}

    def _suggestions(self, accum: _Accumulator) -> list[str]:
        # If the answer reached other assets, nudge a comparison follow-up; else
        # offer the standard quick-prompts.
        if accum.searched or len(accum.citations) > 1:
            other = next((c for c in accum.citations[1:]), None)
            compare = (
                f"Compare this to {other.title}"
                if other and other.title
                else "Compare to similar assets"
            )
            return [
                "Summarize this for an executive",
                "What are the key differences?",
                compare,
                "Turn this into an action checklist",
            ]
        return list(DEFAULT_SUGGESTIONS)


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
