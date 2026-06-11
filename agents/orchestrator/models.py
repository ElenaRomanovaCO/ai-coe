"""Wire-format models for AGENT-01.

These are the request/response contracts the proxy Lambda and the Next.js chat
dock exchange with the Fargate orchestrator, plus the tool-result shapes used
inside the agent loop. Kept in one place so the web client (which mirrors them
in TypeScript) and the server never drift.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Citation content types are the SINGULAR forms surfaced to the UI. The vault
# stores content under PLURAL directory prefixes (assets/, tools/, ...); the
# vector index records that prefix as ``content_type``. ``search_knowledge_base``
# maps one to the other via CONTENT_TYPE_FROM_DIR below.
ContentType = Literal[
    "asset", "tool", "vendor", "reg", "feed", "prompt", "decision", "assessment", "kit", "insight"
]

CONTENT_TYPE_FROM_DIR: dict[str, ContentType] = {
    "assets": "asset",
    "tools": "tool",
    "vendors": "vendor",
    "regs": "reg",
    "feed": "feed",
    "prompts": "prompt",
    "decisions": "decision",
    "assessments": "assessment",
    "kits": "kit",
    # Retro-extracted insights (AGENT-15) are reusable knowledge — searchable in chat.
    # (The retros themselves live under retros/ and are generated:true → scoped out.)
    "insights": "insight",
}
DIR_FROM_CONTENT_TYPE: dict[ContentType, str] = {v: k for k, v in CONTENT_TYPE_FROM_DIR.items()}


class ChatRequest(BaseModel):
    display_name: str
    session_id: str
    request_id: str
    message: str
    current_route: str | None = None


class Citation(BaseModel):
    file_path: str
    chunk_index: int
    content_type: ContentType
    # Populated only when an Asset Library browse exists for this content type
    # (i.e. module-2 enabled). Otherwise None and the UI links to file_path.
    asset_library_url: str | None = None
    score: float | None = None


class UIAction(BaseModel):
    type: Literal[
        "navigate", "open_panel", "start_assessment", "start_kit_builder", "show_module_card"
    ]
    payload: dict


class ChatResponse(BaseModel):
    assistant_message: str
    citations: list[Citation] = Field(default_factory=list)
    invoked_modules: list[str] = Field(default_factory=list)
    ui_actions: list[UIAction] = Field(default_factory=list)


class ModuleDescription(BaseModel):
    """Result of ``describe_module`` — the full meta view of one module."""

    id: str
    name: str
    wave: int
    purpose: str
    when_to_use: list[str] = Field(default_factory=list)
    example_queries: list[str] = Field(default_factory=list)
    agent_id: str
    enabled: bool


class ModuleSummary(BaseModel):
    """Result row of ``list_modules`` — the compact browse view."""

    id: str
    name: str
    wave: int
    purpose: str
    enabled: bool
