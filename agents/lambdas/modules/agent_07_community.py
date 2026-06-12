"""AGENT-07 — Community & Enablement Hub (Module 6), Haiku 4.5 tier.

Read-mostly Layer 2 directory agent over ``vault/community/`` (the same mechanical
S3-read shape as AGENT-03/AGENT-08, no chat-LLM loop), plus one light write: signing up
for office hours, persisted to the user profile (``users/{slug}.json`` in the sessions
bucket — the AGENT-03 profile-sidecar pattern). Community threads are NOT duplicated
here: ``list_threads`` **composes AGENT-09 (Module 8 Q&A) in-process** (the AGENT-14→
AGENT-21 composition precedent) so there's one source of truth for threads.

Operations (on ``op``):
  - ``list_learning_paths``   — learning paths, filterable by role + stage (FR-061)
  - ``list_office_hours``     — upcoming office hours; marks the caller's signups (FR-062)
  - ``signup_office_hours``   — add/remove a signup on the user profile (idempotent)
  - ``list_threads``          — delegate to AGENT-09 (FR-062)
  - ``get_expert_directory``  — expert personas, filterable by expertise + industry (FR-063)
  - default                   — hub overview (counts per surface)
"""

from __future__ import annotations

import os
from typing import Any

from botocore.exceptions import ClientError

from agents.lib import models as lib_models

from .agent_03_asset_library import _slug, _split_frontmatter
from .agent_09_qa import QaAgent
from .base import ModuleAgent

AGENT_ID = "AGENT-07"
COMMUNITY_ROUTE = "/modules/community"
COMMUNITY_PREFIX = "community/"
LEARNING_PREFIX = "community/learning-paths/"
OFFICE_HOURS_PREFIX = "community/office-hours/"
EXPERTS_PREFIX = "community/experts/"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _str_list(value: Any) -> list[str]:
    return [str(v) for v in (value or [])]


class CommunityAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.HAIKU_4_5

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        sessions_bucket: str | None = None,
        region: str = lib_models.REGION,
        s3: Any = None,
        qa_agent: QaAgent | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.region = region
        self._s3 = s3
        self._qa_agent = qa_agent

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    @property
    def qa(self) -> QaAgent:
        # Compose AGENT-09 in-process (one source of truth for threads), sharing clients.
        if self._qa_agent is None:
            self._qa_agent = QaAgent(
                vault_bucket=self.vault_bucket,
                sessions_bucket=self.sessions_bucket,
                region=self.region,
                s3=self._s3,
                metrics_client=self.metrics_client,
            )
        return self._qa_agent

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        op = args.get("op")
        if op == "list_learning_paths":
            return self.run_tool("list_learning_paths", lambda _u: self._learning_paths(args))
        if op == "list_office_hours":
            return self.run_tool("list_office_hours", lambda _u: self._office_hours(args))
        if op in ("signup_office_hours", "cancel_office_hours"):
            return self.run_tool("signup_office_hours", lambda _u: self._signup(args))
        if op == "list_threads":
            return self.run_tool("list_threads", lambda _u: self._threads(args))
        if op in ("get_expert_directory", "list_experts"):
            return self.run_tool("get_expert_directory", lambda _u: self._experts(args))
        return self.run_tool("community_overview", lambda _u: self._overview())

    # --- S3 helpers --------------------------------------------------------
    def _list_keys(self, prefix: str) -> list[str]:
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": prefix}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            keys.extend(o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(".md"))
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
        return keys

    def _read_fm(self, key: str) -> dict:
        text = self.s3.get_object(Bucket=self.vault_bucket, Key=key)["Body"].read().decode("utf-8")
        fm, _ = _split_frontmatter(text)
        return fm

    def _entries(self, prefix: str) -> list[dict]:
        out: list[dict] = []
        for key in self._list_keys(prefix):
            fm = self._read_fm(key)
            fm["file_path"] = key
            fm["id"] = str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md"))
            out.append(fm)
        return out

    # --- user profile (signups) -------------------------------------------
    def _user_key(self, display_name: str) -> str:
        return f"users/{_slug(display_name)}.json"

    def _read_profile(self, display_name: str) -> dict:
        import json

        default = {"display_name": display_name, "office_hours": []}
        try:
            raw = self.s3.get_object(Bucket=self.sessions_bucket, Key=self._user_key(display_name))[
                "Body"
            ].read()
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
        profile.setdefault("office_hours", [])
        return profile

    def _write_profile(self, display_name: str, profile: dict) -> None:
        import json

        self.s3.put_object(
            Bucket=self.sessions_bucket,
            Key=self._user_key(display_name),
            Body=json.dumps(profile, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    def _signups(self, display_name: str | None) -> set[str]:
        if not display_name:
            return set()
        return {str(x) for x in (self._read_profile(display_name).get("office_hours") or [])}

    # --- operations --------------------------------------------------------
    def _learning_paths(self, args: dict[str, Any]) -> dict[str, Any]:
        role = _norm(args.get("role")).lower()
        stage = args.get("stage")
        stage_int = int(stage) if stage is not None and str(stage).strip() != "" else None
        out = []
        for fm in self._entries(LEARNING_PREFIX):
            if role and _norm(fm.get("role")).lower() != role:
                continue
            fm_stage = fm.get("stage")
            if stage_int is not None and fm_stage is not None and int(fm_stage) != stage_int:
                continue
            out.append(
                {
                    "id": fm["id"],
                    "title": _norm(fm.get("title")),
                    "role": _norm(fm.get("role")),
                    "stage": fm.get("stage"),
                    "duration": _norm(fm.get("duration")),
                    "modules": _str_list(fm.get("modules")),
                    "tags": _str_list(fm.get("tags")),
                }
            )
        out.sort(key=lambda p: (p["role"], p["title"]))
        return {"status": "ok", "learning_paths": out}

    def _office_hours(self, args: dict[str, Any]) -> dict[str, Any]:
        signed = self._signups(args.get("display_name"))
        out = []
        for fm in self._entries(OFFICE_HOURS_PREFIX):
            out.append(
                {
                    "id": fm["id"],
                    "title": _norm(fm.get("title")),
                    "host": _norm(fm.get("host")),
                    "date": _norm(fm.get("date")),
                    "topic": _norm(fm.get("topic")),
                    "capacity": fm.get("capacity"),
                    "tags": _str_list(fm.get("tags")),
                    "signed_up": fm["id"] in signed,
                }
            )
        out.sort(key=lambda o: o["date"])
        return {"status": "ok", "office_hours": out}

    def _signup(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        office_hour_id = _norm(args.get("office_hour_id") or args.get("id"))
        if not display_name or not office_hour_id:
            return {"status": "error", "message": "display_name and office_hour_id are required."}
        cancel = args.get("op") == "cancel_office_hours"
        profile = self._read_profile(display_name)
        signups = [str(x) for x in (profile.get("office_hours") or [])]
        if cancel:
            signups = [s for s in signups if s != office_hour_id]
        elif office_hour_id not in signups:
            signups.append(office_hour_id)
        profile["office_hours"] = signups
        self._write_profile(display_name, profile)
        return {
            "status": "ok",
            "office_hour_id": office_hour_id,
            "signed_up": not cancel,
            "signups": signups,
        }

    def _threads(self, args: dict[str, Any]) -> dict[str, Any]:
        # Delegate to AGENT-09's list_threads (one source of truth for community threads).
        passthrough = {k: v for k, v in args.items() if k != "op"}
        return self.qa.handle({"op": "list_threads", **passthrough})

    def _experts(self, args: dict[str, Any]) -> dict[str, Any]:
        want_expertise = _norm(args.get("expertise")).lower()
        want_industry = _norm(args.get("industry")).lower()
        out = []
        for fm in self._entries(EXPERTS_PREFIX):
            expertise = _str_list(fm.get("expertise"))
            industries = _str_list(fm.get("industries"))
            if want_expertise and not any(want_expertise in e.lower() for e in expertise):
                continue
            if want_industry and not any(want_industry in i.lower() for i in industries):
                continue
            out.append(
                {
                    "id": fm["id"],
                    "name": _norm(fm.get("name") or fm.get("title")),
                    "title": _norm(fm.get("title")),
                    "expertise": expertise,
                    "industries": industries,
                    "tags": _str_list(fm.get("tags")),
                }
            )
        out.sort(key=lambda e: e["name"])
        return {"status": "ok", "experts": out}

    def _overview(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "learning_paths_count": len(self._list_keys(LEARNING_PREFIX)),
            "office_hours_count": len(self._list_keys(OFFICE_HOURS_PREFIX)),
            "experts_count": len(self._list_keys(EXPERTS_PREFIX)),
        }
