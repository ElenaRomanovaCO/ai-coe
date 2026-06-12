"""AGENT-22 — Consultant Onboarding Journey (Module 23), Haiku 4.5 tier.

Read-mostly Layer 2 agent that turns a new consultant's profile (role, experience,
industry focus, AI background, goals) into a personalized first-30-days onboarding
path. It is **mechanical / deterministic — no chat-LLM loop** (the AGENT-03 / AGENT-08
directory shape): it *composes* three existing module agents in-process rather than
duplicating their reads —

  - AGENT-03 (:class:`AssetLibraryAgent`) — top assets for the user's industries
  - AGENT-07 (:class:`CommunityAgent`)    — role-tailored learning paths + experts
  - AGENT-08 (:class:`ToolsRepoAgent`)     — key tools for the user's AI-stage band

The onboarding profile and the 30-day checklist progress are persisted to the shared
user profile ``users/{slug}.json`` in the sessions bucket (the AGENT-03 / AGENT-07
profile-sidecar pattern), read-modify-written so the user's saved assets / office-hour
signups are never clobbered.

Operations dispatched from :meth:`handle` on ``op``:

  - ``generate_path`` (default)   — the full :class:`OnboardingPath` (FR-067)
  - ``save_profile``              — persist the profile; marks onboarding completed
  - ``get_profile`` / ``read_profile`` — the saved profile + checklist state
  - ``list_first_actions``        — the 30-day checklist with done-state merged (FR-068)
  - ``recommend_connections``     — suggested expert connections by industry
  - ``update_checklist``          — toggle one checklist item's done state (FR-068)

No Titan / S3 Vectors call is needed (asset/tool relevance is mechanical filtering),
so no new IAM: the module-agents role already has vault Get/List + sessions Get/Put.
"""

from __future__ import annotations

import os
from typing import Any

from botocore.exceptions import ClientError
from pydantic import BaseModel, Field, ValidationError, field_validator

from agents.lib import models as lib_models

from .agent_03_asset_library import AssetLibraryAgent, AssetSummary, _slug
from .agent_07_community import CommunityAgent
from .agent_08_tools import ToolsRepoAgent, ToolSummary
from .base import ModuleAgent

AGENT_ID = "AGENT-22"
ONBOARDING_ROUTE = "/modules/onboarding"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}

_VALID_ROLES = ("consultant", "architect", "data-engineer", "pm", "executive")
_VALID_BACKGROUNDS = ("novice", "intermediate", "advanced")

# Onboarding role -> the learning-path / expertise vocabulary used in vault/community/.
_ROLE_TO_LEARNING_ROLE = {
    "consultant": "delivery-lead",
    "architect": "solution-architect",
    "data-engineer": "data-scientist",
    "pm": "delivery-lead",
    "executive": "executive",
}
# AI background -> the AI-maturity stage band a consultant should focus tooling on.
_BACKGROUND_TO_STAGES = {
    "novice": {0, 1, 2},
    "intermediate": {2, 3, 4},
    "advanced": {3, 4, 5},
}


# --- wire models -----------------------------------------------------------
class OnboardingProfile(BaseModel):
    role: str = "consultant"
    experience_years: int = 0
    industry_focus: list[str] = Field(default_factory=list)
    ai_background: str = "novice"
    goals: list[str] = Field(default_factory=list)

    @field_validator("role")
    @classmethod
    def _role(cls, v: str) -> str:
        v = (v or "").strip().lower()
        return v if v in _VALID_ROLES else "consultant"

    @field_validator("ai_background")
    @classmethod
    def _background(cls, v: str) -> str:
        v = (v or "").strip().lower()
        return v if v in _VALID_BACKGROUNDS else "novice"

    @field_validator("experience_years", mode="before")
    @classmethod
    def _years(cls, v: Any) -> int:
        try:
            return max(0, int(v))
        except (TypeError, ValueError):
            return 0

    @field_validator("industry_focus", "goals", mode="before")
    @classmethod
    def _str_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            v = [v]
        return [str(x).strip() for x in v if str(x).strip()]


class ActionItem(BaseModel):
    id: str
    title: str
    description: str = ""
    week: int = 1
    module_route: str | None = None
    done: bool = False


class OnboardingAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.HAIKU_4_5

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        sessions_bucket: str | None = None,
        vector_bucket: str = "aicoe-content-vectors",
        index_name: str = "aicoe-content",
        region: str = lib_models.REGION,
        s3: Any = None,
        s3vectors: Any = None,
        bedrock: Any = None,
        asset_agent: AssetLibraryAgent | None = None,
        community_agent: CommunityAgent | None = None,
        tools_agent: ToolsRepoAgent | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.region = region
        self._s3 = s3
        # Compose the existing module agents (one source of truth), sharing clients.
        self.assets = asset_agent or AssetLibraryAgent(
            vault_bucket=self.vault_bucket,
            sessions_bucket=self.sessions_bucket,
            vector_bucket=vector_bucket,
            index_name=index_name,
            region=region,
            s3=s3,
            s3vectors=s3vectors,
            bedrock=bedrock,
        )
        self.community = community_agent or CommunityAgent(
            vault_bucket=self.vault_bucket,
            sessions_bucket=self.sessions_bucket,
            region=region,
            s3=s3,
        )
        self.tools = tools_agent or ToolsRepoAgent(
            vault_bucket=self.vault_bucket,
            vector_bucket=vector_bucket,
            index_name=index_name,
            region=region,
            s3=s3,
            s3vectors=s3vectors,
            bedrock=bedrock,
        )

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        op = args.get("op")
        if op == "save_profile":
            return self.run_tool("save_profile", lambda _u: self._save_profile(args))
        if op in ("get_profile", "read_profile"):
            return self.run_tool("get_profile", lambda _u: self._get_profile(args))
        if op == "list_first_actions":
            return self.run_tool("list_first_actions", lambda _u: self._first_actions_op(args))
        if op == "recommend_connections":
            return self.run_tool("recommend_connections", lambda _u: self._connections_op(args))
        if op == "update_checklist":
            return self.run_tool("update_checklist", lambda _u: self._update_checklist(args))
        return self.run_tool("generate_path", lambda _u: self._generate_path(args))

    # --- user profile (read-modify-write the shared sidecar) ---------------
    def _user_key(self, display_name: str) -> str:
        return f"users/{_slug(display_name)}.json"

    def _read_profile(self, display_name: str) -> dict:
        import json

        default = {"display_name": display_name}
        try:
            raw = self.s3.get_object(
                Bucket=self.sessions_bucket, Key=self._user_key(display_name)
            )["Body"].read()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _NOT_FOUND:
                return default
            raise
        except (KeyError, FileNotFoundError):
            return default
        try:
            profile = json.loads(raw)
        except (ValueError, TypeError):
            return default
        return profile if isinstance(profile, dict) else default

    def _write_profile(self, display_name: str, profile: dict) -> None:
        import json

        self.s3.put_object(
            Bucket=self.sessions_bucket,
            Key=self._user_key(display_name),
            Body=json.dumps(profile, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    def _resolve_profile(self, args: dict[str, Any]) -> OnboardingProfile:
        """Inline profile fields in ``args`` win; otherwise the saved one."""
        inline = {
            k: args[k]
            for k in ("role", "experience_years", "industry_focus", "ai_background", "goals")
            if k in args and args[k] not in (None, "")
        }
        if inline:
            return OnboardingProfile(**inline)
        display_name = args.get("display_name")
        saved = (self._read_profile(display_name) or {}).get("onboarding") if display_name else None
        return OnboardingProfile(**(saved or {}))

    # --- operations: profile read/write ------------------------------------
    def _save_profile(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = (args.get("display_name") or "").strip()
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        try:
            prof = OnboardingProfile(
                role=args.get("role", "consultant"),
                experience_years=args.get("experience_years", 0),
                industry_focus=args.get("industry_focus", []),
                ai_background=args.get("ai_background", "novice"),
                goals=args.get("goals", []),
            )
        except ValidationError as exc:
            return {"status": "error", "message": f"Invalid profile: {exc.errors()[:1]}"}

        profile = self._read_profile(display_name)
        profile["display_name"] = display_name
        profile["onboarding"] = prof.model_dump()
        profile["onboarding_completed"] = True
        self._write_profile(display_name, profile)
        return {
            "status": "ok",
            "onboarding": prof.model_dump(),
            "onboarding_completed": True,
        }

    def _get_profile(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = (args.get("display_name") or "").strip()
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        profile = self._read_profile(display_name)
        onboarding = profile.get("onboarding")
        return {
            "status": "ok",
            "onboarding": onboarding,
            "onboarding_completed": bool(profile.get("onboarding_completed")),
            "checklist": profile.get("onboarding_checklist") or {},
        }

    def _checklist_state(self, display_name: str | None) -> dict[str, bool]:
        if not display_name:
            return {}
        raw = self._read_profile(display_name).get("onboarding_checklist") or {}
        return {str(k): bool(v) for k, v in raw.items()}

    def _update_checklist(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = (args.get("display_name") or "").strip()
        action_id = (args.get("action_id") or args.get("id") or "").strip()
        if not display_name or not action_id:
            return {"status": "error", "message": "display_name and action_id are required."}
        done = bool(args.get("done", True))
        profile = self._read_profile(display_name)
        raw = profile.get("onboarding_checklist") or {}
        checklist = {str(k): bool(v) for k, v in raw.items()}
        checklist[action_id] = done
        profile["onboarding_checklist"] = checklist
        profile.setdefault("display_name", display_name)
        self._write_profile(display_name, profile)
        return {"status": "ok", "action_id": action_id, "done": done, "checklist": checklist}

    # --- composition: assets / learning / experts / tools ------------------
    def _top_assets(self, profile: OnboardingProfile, limit: int = 7) -> list[AssetSummary]:
        result = self.assets.handle({"op": "list_assets", "limit": 1000})
        summaries = [AssetSummary(**a) for a in result.get("assets", [])]
        focus = {i.lower() for i in profile.industry_focus}
        goal_tokens = {t.lower() for g in profile.goals for t in g.replace("-", " ").split()}

        def score(a: AssetSummary) -> tuple:
            in_focus = 1 if focus and a.industry.lower() in focus else 0
            tag_hits = sum(1 for t in a.tags if t.lower() in goal_tokens)
            return (in_focus, tag_hits, a.updated_at)

        ranked = sorted(summaries, key=score, reverse=True)
        # Prefer in-focus assets but backfill so the path is never empty.
        in_focus = [a for a in ranked if not focus or a.industry.lower() in focus]
        chosen = in_focus[:limit]
        if len(chosen) < min(5, len(ranked)):
            seen = {a.id for a in chosen}
            chosen += [a for a in ranked if a.id not in seen][: limit - len(chosen)]
        return chosen

    def _learning_paths(self, profile: OnboardingProfile, limit: int = 4) -> list[dict]:
        result = self.community.handle({"op": "list_learning_paths"})
        paths = result.get("learning_paths", [])
        target = _ROLE_TO_LEARNING_ROLE.get(profile.role, "")

        def matches(p: dict) -> bool:
            role = str(p.get("role") or "").lower()
            return bool(target) and (target in role or role in target)

        preferred = [p for p in paths if matches(p)]
        rest = [p for p in paths if not matches(p)]
        return (preferred + rest)[:limit]

    def _connections(self, profile: OnboardingProfile, limit: int = 5) -> list[dict]:
        focus = profile.industry_focus or [""]
        seen: set[str] = set()
        out: list[dict] = []
        for industry in focus:
            res = self.community.handle(
                {"op": "get_expert_directory", **({"industry": industry} if industry else {})}
            )
            for e in res.get("experts", []):
                if e["id"] in seen:
                    continue
                seen.add(e["id"])
                out.append(e)
        # Only backfill when the focus filters matched nobody, so the path is never
        # empty — a non-empty industry match is returned as-is (not padded).
        if not out:
            out = self.community.handle({"op": "get_expert_directory"}).get("experts", [])
        return out[:limit]

    def _key_tools(self, profile: OnboardingProfile, limit: int = 5) -> list[ToolSummary]:
        result = self.tools.handle({"op": "list_tools", "limit": 1000})
        summaries = [ToolSummary(**t) for t in result.get("tools", [])]
        stages = _BACKGROUND_TO_STAGES.get(profile.ai_background, set())

        def score(t: ToolSummary) -> tuple:
            fits = 1 if stages and set(t.ai_stage_fit) & stages else 0
            return (fits, -len(t.ai_stage_fit), t.name)

        ranked = sorted(summaries, key=lambda t: (-score(t)[0], score(t)[1], score(t)[2]))
        return ranked[:limit]

    # --- 30-day checklist (deterministic, role-aware) ----------------------
    def _first_actions(self, profile: OnboardingProfile, done: dict[str, bool]) -> list[ActionItem]:
        industry = profile.industry_focus[0] if profile.industry_focus else "your industry"
        items: list[tuple[str, str, str, int, str | None]] = [
            (
                "complete-profile",
                "Complete your onboarding profile",
                "Tell us your role, industry focus, and goals so the platform can tailor itself.",
                1,
                "/modules/onboarding/profile",
            ),
            (
                "run-maturity-assessment",
                "Run a maturity assessment",
                "Walk through the AI maturity assessment to learn the 0–5 curve we use.",
                1,
                "/modules/maturity-assessment",
            ),
            (
                "browse-asset-library",
                f"Explore {industry} assets in the Asset Library",
                "Browse reference architectures and solution patterns relevant to your focus.",
                1,
                "/modules/asset-library",
            ),
            (
                "review-key-tools",
                "Review the key tools for your role",
                "Skim the Tools Repository for the frameworks and platforms you'll lean on.",
                2,
                "/modules/tools-repo",
            ),
            (
                "join-office-hour",
                "Join a community office hour",
                "Sign up for an upcoming office hour and meet the guild.",
                2,
                "/modules/community/office-hours",
            ),
            (
                "start-learning-path",
                "Start your recommended learning path",
                "Pick the role-tailored learning path from your plan and begin week one.",
                2,
                "/modules/community/learning",
            ),
            (
                "try-prompt-studio",
                "Try the Prompt Studio",
                "Run a prompt against a model and explore the platform's hands-on tooling.",
                3,
                "/modules/prompt-studio",
            ),
            (
                "ask-the-assistant",
                "Ask the AI assistant a delivery question",
                "Use the chat dock or Q&A to get a cited answer from the knowledge vault.",
                3,
                "/modules/qa",
            ),
            (
                "connect-with-expert",
                "Connect with a suggested expert",
                "Reach out to one of the experts recommended for your industry focus.",
                3,
                "/modules/community/experts",
            ),
            (
                "build-engagement-kit",
                "Build your first engagement kit",
                "Assemble a tailored kit for a real or sample engagement.",
                4,
                "/modules/kit-builder",
            ),
            (
                "contribute-knowledge",
                "Contribute a lesson learned",
                "Share an asset or insight back to the vault with AI-assisted anonymization.",
                4,
                "/modules/contribute",
            ),
        ]
        return [
            ActionItem(
                id=i, title=t, description=d, week=w, module_route=r, done=bool(done.get(i, False))
            )
            for (i, t, d, w, r) in items
        ]

    # --- the headline path -------------------------------------------------
    def _generate_path(self, args: dict[str, Any]) -> dict[str, Any]:
        profile = self._resolve_profile(args)
        display_name = args.get("display_name")
        done = self._checklist_state(display_name)
        path = {
            "user": display_name or "",
            "profile": profile.model_dump(),
            "top_assets": [a.model_dump() for a in self._top_assets(profile)],
            "learning_paths": self._learning_paths(profile),
            "suggested_connections": self._connections(profile),
            "key_tools": [t.model_dump() for t in self._key_tools(profile)],
            "first_actions": [a.model_dump() for a in self._first_actions(profile, done)],
        }
        return {"status": "ok", **path}

    def _first_actions_op(self, args: dict[str, Any]) -> dict[str, Any]:
        profile = self._resolve_profile(args)
        done = self._checklist_state(args.get("display_name"))
        actions = self._first_actions(profile, done)
        return {"status": "ok", "first_actions": [a.model_dump() for a in actions]}

    def _connections_op(self, args: dict[str, Any]) -> dict[str, Any]:
        # Explicit ``industry`` arg overrides the profile's focus list.
        if args.get("industry"):
            profile = OnboardingProfile(industry_focus=[args["industry"]])
        else:
            profile = self._resolve_profile(args)
        return {"status": "ok", "suggested_connections": self._connections(profile)}
