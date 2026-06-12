"""AGENT-31 — Trainings (Module 32), Haiku 4.5 tier.

A curated learning catalog over ``vault/trainings/``: CoE-hosted sessions (``kind: hosted``)
and recommended external tutorials (``kind: tutorial``), grouped by theme. **Mechanical**,
exactly like AGENT-03/AGENT-08 — deterministic S3 reads for list/detail, and a read-modify-
write of the user profile for save/unsave. **No LLM loop** (curated content, not generative).

Training content is general reference material, so it is seeded into the **vault** and indexed
(Chat/Q&A can recommend it) — the KB-pollution rule covers only runtime/client-specific writes
(``vault/decisions/curated-content-in-vault.md``). Saves persist to ``users/{slug}.json`` in the
sessions bucket under a dedicated ``saved_trainings`` list (the AGENT-03 profile-sidecar pattern),
so they don't collide with saved assets.

Operations (on ``op``):
  - ``list``        — enumerate + filter the catalog (theme/source/level/kind/query)
  - ``get``         — one training's rendered body + frontmatter
  - ``save``/``unsave`` — toggle a training on the user profile
  - ``list_saved``  — the caller's saved trainings (for the dashboard card)
"""

from __future__ import annotations

import json
import os
from typing import Any

from botocore.exceptions import ClientError

from agents.lib import models as lib_models

from .agent_03_asset_library import _slug, _split_frontmatter
from .base import ModuleAgent

AGENT_ID = "AGENT-31"
TRAININGS_ROUTE = "/modules/trainings"
TRAININGS_PREFIX = "trainings/"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _str_list(value: Any) -> list[str]:
    return [str(v) for v in (value or [])]


def _summary(fm: dict, key: str) -> dict:
    return {
        "id": str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md")),
        "title": _norm(fm.get("title")),
        "summary": _norm(fm.get("summary")),
        "kind": _norm(fm.get("kind")),
        "theme": _norm(fm.get("theme")),
        "source": _norm(fm.get("source")),
        "level": _norm(fm.get("level")),
        "url": _norm(fm.get("url")),
        "duration_min": int(fm.get("duration_min") or 0),
        "author": _norm(fm.get("author")),
        "presenter": _norm(fm.get("presenter")),
        "tags": _str_list(fm.get("tags")),
        "last_verified": _norm(fm.get("last_verified")),
    }


class TrainingsAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.HAIKU_4_5

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        sessions_bucket: str | None = None,
        region: str = lib_models.REGION,
        s3: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.region = region
        self._s3 = s3

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        if "training_id" not in args and args.get("id"):
            args = {**args, "training_id": args["id"]}
        op = args.get("op")
        if op == "get" or (op is None and args.get("training_id")):
            return self.run_tool("get_training", lambda _u: self._get(args))
        if op in ("save", "unsave"):
            return self.run_tool("save_training", lambda _u: self._save(args))
        if op == "list_saved":
            return self.run_tool("list_saved_trainings", lambda _u: self._list_saved(args))
        return self.run_tool("list_trainings", lambda _u: self._list(args))

    # --- S3 helpers --------------------------------------------------------
    def _list_keys(self) -> list[str]:
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": TRAININGS_PREFIX}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            keys.extend(o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(".md"))
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
        return keys

    def _read(self, key: str) -> str:
        return self.s3.get_object(Bucket=self.vault_bucket, Key=key)["Body"].read().decode("utf-8")

    def _all(self) -> list[tuple[dict, str]]:
        out: list[tuple[dict, str]] = []
        for key in self._list_keys():
            fm, body = _split_frontmatter(self._read(key))
            out.append((fm, body))
        return out

    # --- user profile (saves) ---------------------------------------------
    def _user_key(self, display_name: str) -> str:
        return f"users/{_slug(display_name)}.json"

    def _read_profile(self, display_name: str) -> dict:
        default = {"display_name": display_name, "saved_trainings": []}
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
        profile.setdefault("saved_trainings", [])
        return profile

    def _write_profile(self, display_name: str, profile: dict) -> None:
        self.s3.put_object(
            Bucket=self.sessions_bucket,
            Key=self._user_key(display_name),
            Body=json.dumps(profile, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    def _saved_ids(self, display_name: Any) -> set[str]:
        if not display_name:
            return set()
        return {str(x) for x in self._read_profile(display_name).get("saved_trainings", [])}

    # --- operations --------------------------------------------------------
    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        theme = _norm(args.get("theme")).lower()
        source = _norm(args.get("source")).lower()
        level = _norm(args.get("level")).lower()
        kind = _norm(args.get("kind")).lower()
        query = _norm(args.get("query")).lower()
        limit = int(args.get("limit", 100))
        saved = self._saved_ids(args.get("display_name"))

        out: list[dict] = []
        for fm, _ in self._all():
            s = _summary(fm, "")
            if theme and s["theme"].lower() != theme:
                continue
            if source and s["source"].lower() != source:
                continue
            if level and s["level"].lower() != level:
                continue
            if kind and s["kind"].lower() != kind:
                continue
            if query:
                haystack = f"{s['title']} {s['summary']} {s['theme']} {' '.join(s['tags'])}".lower()
                if query not in haystack:
                    continue
            s["saved"] = s["id"] in saved
            out.append(s)

        out.sort(key=lambda t: (t["theme"], t["title"]))
        return {"status": "ok", "trainings": out[:limit]}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        training_id = _norm(args.get("training_id"))
        if not training_id:
            return {"status": "error", "message": "training_id is required."}
        saved = self._saved_ids(args.get("display_name"))
        for fm, body in self._all():
            s = _summary(fm, "")
            if s["id"] == training_id:
                s["saved"] = s["id"] in saved
                return {
                    "status": "ok",
                    "training": {
                        **s,
                        "session_date": _norm(fm.get("session_date")),
                        "materials": list(fm.get("materials") or []),
                        "updated_at": _norm(fm.get("updated_at")),
                        "body_markdown": body.strip(),
                    },
                }
        return {"status": "not_found", "training_id": training_id, "message": "No such training."}

    def _save(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        training_id = _norm(args.get("training_id"))
        if not display_name or not training_id:
            return {"status": "error", "message": "display_name and training_id are required."}
        unsave = args.get("op") == "unsave"
        profile = self._read_profile(display_name)
        saved = [str(x) for x in profile.get("saved_trainings", [])]
        if unsave:
            saved = [s for s in saved if s != training_id]
        elif training_id not in saved:
            saved.append(training_id)
        profile["saved_trainings"] = saved
        self._write_profile(display_name, profile)
        return {
            "status": "ok",
            "training_id": training_id,
            "saved": not unsave,
            "saved_trainings": saved,
        }

    def _list_saved(self, args: dict[str, Any]) -> dict[str, Any]:
        display_name = _norm(args.get("display_name"))
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        saved_ids = {str(x) for x in self._read_profile(display_name).get("saved_trainings", [])}
        out = [
            {**_summary(fm, ""), "saved": True}
            for fm, _ in self._all()
            if str(fm.get("id")) in saved_ids
        ]
        out.sort(key=lambda t: (t["theme"], t["title"]))
        return {"status": "ok", "trainings": out}
