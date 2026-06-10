"""AGENT-11 — Prompt Engineering Studio (Module 11), Sonnet 4.6 tier.

Author prompts, fork/version them, run them live against a chosen Bedrock model, and
get improvement suggestions. The 5 seed prompts are read-only references in the vault
(``vault/prompts/``); user-created versions/forks are written to the **sessions** bucket
(``prompts/{id}.md``) so scratch drafts are never embedded into KB search and don't fire
the reembed pipeline (decision recorded in the task notes). ``list``/``get`` merge both
sources.

A prompt ``.md`` = frontmatter (``id, title, use_case, model_targets, variables, version,
parent_id, created_by, created_at``) + a ``## Prompt`` section holding the prompt text
with ``{{variable}}`` placeholders.

Operations (on ``op``):
  - ``list_prompts``        — merge seed+user, filter by use_case / model_target (default)
  - ``get_prompt``          — one prompt: frontmatter + extracted prompt_text + body
  - ``save_prompt``         — mode version|fork|new → write a new file to sessions
  - ``run_prompt``          — substitute variables, call Bedrock, return output + metrics
  - ``suggest_improvements``— anti-pattern flags (deterministic) + one Sonnet suggestion call
  - ``version_history``     — the lineage (root + descendants) of a prompt, by version

``run_prompt`` is non-streaming (one invoke returns the full result), consistent with the
other module agents. ``suggest_improvements`` follows the AGENT-05/24 precedent: deterministic
analysis + exactly one Sonnet call (with a deterministic fallback).
"""

from __future__ import annotations

import os
import re
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from agents.lib import models as lib_models
from agents.lib.base_agent import Usage, instrumented
from agents.lib.bedrock_client import BedrockClient

from .agent_03_asset_library import _split_frontmatter
from .base import ModuleAgent

AGENT_ID = "AGENT-11"
PROMPTS_PREFIX = "prompts/"
PROMPT_STUDIO_ROUTE = "/modules/prompt-studio"
_VAR = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
_PROMPT_SECTION = re.compile(r"^##\s+Prompt\s*$(.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL)
_VAGUE = ("good", "nice", "appropriate", "better", "stuff", "things", "etc")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _extract_prompt_text(body: str) -> str:
    """The text of the ``## Prompt`` section, else the whole body (minus the H1)."""
    m = _PROMPT_SECTION.search(body)
    if m:
        return m.group(1).strip()
    return re.sub(r"^#\s+.+?$", "", body, count=1, flags=re.MULTILINE).strip()


class PromptStudioAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.SONNET_4_6

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        sessions_bucket: str | None = None,
        region: str = lib_models.REGION,
        s3: Any = None,
        bedrock: Any = None,
        bedrock_client: BedrockClient | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.region = region
        self._s3 = s3
        self.bedrock_client = bedrock_client or BedrockClient(client=bedrock)

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        if "prompt_id" not in args and args.get("id"):
            args = {**args, "prompt_id": args["id"]}
        op = args.get("op")
        if op == "get_prompt" or (op is None and args.get("prompt_id")):
            return self.run_tool("get_prompt", lambda _u: self._get(args))
        if op == "save_prompt":
            return self.run_tool("save_prompt", lambda _u: self._save(args))
        if op == "run_prompt":
            return self.run_tool("run_prompt", lambda _u: self._run(args))
        if op == "suggest_improvements":
            return self.run_tool("suggest_improvements", lambda _u: self._suggest(args))
        if op == "version_history":
            return self.run_tool("version_history", lambda _u: self._history(args))
        return self.run_tool("list_prompts", lambda _u: self._list(args))

    # --- storage helpers ---------------------------------------------------
    def _list_keys(self, bucket: str) -> list[str]:
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": bucket, "Prefix": PROMPTS_PREFIX}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            keys.extend(o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(".md"))
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
        return keys

    def _read(self, bucket: str, key: str) -> str:
        return self.s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")

    def _read_all(self) -> list[dict[str, Any]]:
        """Every prompt across vault (seed) + sessions (user), as parsed records."""
        out: list[dict[str, Any]] = []
        for bucket, source in ((self.vault_bucket, "seed"), (self.sessions_bucket, "user")):
            if not bucket:
                continue
            for key in self._list_keys(bucket):
                fm, body = _split_frontmatter(self._read(bucket, key))
                out.append(
                    {"fm": fm, "body": body, "key": key, "bucket": bucket, "source": source}
                )
        return out

    @staticmethod
    def _rec_id(rec: dict) -> str:
        return str(rec["fm"].get("id") or rec["key"].rsplit("/", 1)[-1].removesuffix(".md"))

    def _load(self, prompt_id: str) -> dict[str, Any] | None:
        target = str(prompt_id)
        basename = f"/{target}.md"
        fallback: dict[str, Any] | None = None
        for rec in self._read_all():
            if self._rec_id(rec) == target:
                return rec
            if rec["key"].endswith(basename):
                fallback = rec
        return fallback

    def _summary(self, rec: dict) -> dict[str, Any]:
        fm = rec["fm"]
        return {
            "id": self._rec_id(rec),
            "title": str(fm.get("title", "")),
            "use_case": str(fm.get("use_case", "")),
            "model_targets": [str(m) for m in (fm.get("model_targets") or [])],
            "variables": [str(v) for v in (fm.get("variables") or [])],
            "version": int(fm.get("version", 1) or 1),
            "parent_id": fm.get("parent_id") if fm.get("parent_id") else None,
            "source": rec["source"],
            "created_by": str(fm.get("created_by", "")),
            "created_at": str(fm.get("created_at", "")),
        }

    # --- operations --------------------------------------------------------
    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        use_case = (args.get("use_case") or "").strip().lower()
        model_target = (args.get("model_target") or "").strip().lower()
        query = (args.get("query") or "").strip().lower()
        out = []
        for rec in self._read_all():
            s = self._summary(rec)
            if use_case and use_case not in s["use_case"].lower():
                continue
            if model_target and model_target not in {m.lower() for m in s["model_targets"]}:
                continue
            if query and query not in f"{s['title']} {s['use_case']}".lower():
                continue
            out.append(s)
        out.sort(key=lambda s: (s["title"], s["version"]))
        return {"status": "ok", "prompts": out}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        prompt_id = args.get("prompt_id")
        if not prompt_id:
            return {"status": "error", "message": "prompt_id is required."}
        rec = self._load(prompt_id)
        if rec is None:
            return {"status": "not_found", "prompt_id": prompt_id, "message": "No such prompt."}
        s = self._summary(rec)
        return {
            "status": "ok",
            "prompt": {
                **s,
                "prompt_text": _extract_prompt_text(rec["body"]),
                "body_markdown": rec["body"].strip(),
            },
        }

    def _save(self, args: dict[str, Any]) -> dict[str, Any]:
        mode = (args.get("mode") or "new").strip().lower()
        if mode not in ("new", "version", "fork"):
            return {"status": "error", "message": "mode must be new, version, or fork."}
        prompt_text = (args.get("prompt_text") or "").strip()
        if not prompt_text:
            return {"status": "error", "message": "prompt_text is required."}

        parent_id: str | None = None
        version = 1
        if mode in ("version", "fork"):
            source_id = args.get("source_id") or args.get("prompt_id")
            src = self._load(source_id) if source_id else None
            if src is None:
                return {"status": "error", "message": "source_id is required for version/fork."}
            src_summary = self._summary(src)
            parent_id = src_summary["id"]
            version = src_summary["version"] + 1 if mode == "version" else 1

        new_id = f"prompt-user-{uuid.uuid4().hex[:10]}"
        title = str(args.get("title") or "Untitled prompt").strip()
        use_case = str(args.get("use_case") or "").strip()
        model_targets = [str(m) for m in (args.get("model_targets") or ["sonnet-4-6"])]
        variables = [str(v) for v in (args.get("variables") or _VAR.findall(prompt_text))]
        created_by = str(args.get("display_name") or "anon")
        created_at = _now_iso()

        body = _render_prompt_md(
            new_id, title, use_case, model_targets, variables, version, parent_id,
            created_by, created_at, prompt_text,
        )
        key = f"{PROMPTS_PREFIX}{new_id}.md"
        self.s3.put_object(
            Bucket=self.sessions_bucket, Key=key, Body=body.encode("utf-8"),
            ContentType="text/markdown",
        )
        return {
            "status": "ok",
            "prompt": {
                "id": new_id, "title": title, "use_case": use_case,
                "model_targets": model_targets, "variables": variables, "version": version,
                "parent_id": parent_id, "source": "user", "created_by": created_by,
                "created_at": created_at, "mode": mode,
            },
        }

    def _run(self, args: dict[str, Any]) -> dict[str, Any]:
        prompt_text = (args.get("prompt_text") or "").strip()
        if not prompt_text:
            return {"status": "error", "message": "prompt_text is required."}
        model_id = _resolve_model(args.get("model_id") or "sonnet-4-6")
        if model_id is None:
            return {"status": "error", "message": "Unknown model_id."}
        variables = args.get("variables") or {}
        rendered = _substitute(prompt_text, variables)
        max_tokens = int(args.get("max_tokens", 1000))
        temperature = float(args.get("temperature", 0.7))

        usage = Usage(model_id=model_id)
        start = time.perf_counter()
        with instrumented(
            agent_id=self.agent_id,
            tool_name="bedrock:converse",
            model_id=model_id,
            metrics_client=self.metrics_client,
        ) as u:
            resp = self.bedrock_client.converse(
                model_id=model_id,
                messages=[{"role": "user", "content": [{"text": rendered}]}],
                max_tokens=max_tokens,
                temperature=temperature,
                usage=u,
            )
            usage = u
        latency_ms = int((time.perf_counter() - start) * 1000)
        output = _extract_text(resp.get("output", {}).get("message", {}))
        return {
            "status": "ok",
            "output": output,
            "tokens_in": usage.tokens_in,
            "tokens_out": usage.tokens_out,
            "cost_usd": round(usage.cost_usd, 6),
            "latency_ms": latency_ms,
            "model_id": model_id,
        }

    def _suggest(self, args: dict[str, Any]) -> dict[str, Any]:
        prompt_text = (args.get("prompt_text") or "").strip()
        if not prompt_text:
            return {"status": "error", "message": "prompt_text is required."}
        declared = [str(v) for v in (args.get("variables") or [])]
        anti_patterns = _anti_patterns(prompt_text, declared)
        suggestions = self._suggestions(prompt_text, anti_patterns)
        return {"status": "ok", "suggestions": suggestions, "anti_patterns": anti_patterns}

    def _suggestions(self, prompt_text: str, anti_patterns: list[dict]) -> list[str]:
        flags = "\n".join(f"- {a['flag']}: {a['detail']}" for a in anti_patterns) or "- (none)"
        user_text = (
            f"Prompt under review:\n\n{prompt_text}\n\n"
            f"Deterministic anti-pattern flags already found:\n{flags}\n\n"
            "Give 3-5 concrete, specific suggestions to improve this prompt's clarity, "
            "structure, and output reliability. Output ONLY a markdown bullet list, one "
            "sentence per bullet. Do not repeat the flags verbatim."
        )
        try:
            with instrumented(
                agent_id=self.agent_id,
                tool_name="bedrock:converse",
                model_id=self.model_id,
                metrics_client=self.metrics_client,
            ) as usage:
                resp = self.bedrock_client.converse(
                    model_id=self.model_id,
                    messages=[{"role": "user", "content": [{"text": user_text}]}],
                    system=SUGGEST_SYSTEM,
                    max_tokens=500,
                    usage=usage,
                )
            parsed = _bullets(_extract_text(resp.get("output", {}).get("message", {})))
            if parsed:
                return parsed[:5]
        except Exception:  # noqa: BLE001 — deterministic fallback
            pass
        return _fallback_suggestions(anti_patterns)

    def _history(self, args: dict[str, Any]) -> dict[str, Any]:
        prompt_id = args.get("prompt_id")
        if not prompt_id:
            return {"status": "error", "message": "prompt_id is required."}
        all_recs = self._read_all()
        by_id = {self._rec_id(r): self._summary(r) for r in all_recs}
        if prompt_id not in by_id:
            return {"status": "not_found", "prompt_id": prompt_id}

        # Walk up to the lineage root, then collect every prompt reachable through parent links.
        root = prompt_id
        guard = 0
        while guard < 50:
            parent = by_id.get(root, {}).get("parent_id")
            if not parent or parent not in by_id:
                break
            root = parent
            guard += 1
        lineage = [s for s in by_id.values() if _in_lineage(s, root, by_id)]
        lineage.sort(key=lambda s: (s["version"], s["created_at"]))
        return {"status": "ok", "root_id": root, "versions": lineage}


# --- module-level helpers --------------------------------------------------
def _in_lineage(summary: dict, root: str, by_id: dict[str, dict]) -> bool:
    node = summary["id"]
    guard = 0
    while node and guard < 50:
        if node == root:
            return True
        node = by_id.get(node, {}).get("parent_id")
        guard += 1
    return False


def _substitute(text: str, variables: dict[str, Any]) -> str:
    def repl(m: re.Match) -> str:
        name = m.group(1)
        return str(variables.get(name, m.group(0)))

    return _VAR.sub(repl, text)


def _resolve_model(model_id: str) -> str | None:
    m = str(model_id).strip()
    if m in lib_models.TIER_TO_MODEL_ID:
        return lib_models.TIER_TO_MODEL_ID[m]
    if m in lib_models.TIER_TO_MODEL_ID.values():
        return m
    return None


def _anti_patterns(prompt_text: str, declared: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    referenced = set(_VAR.findall(prompt_text))
    declared_set = set(declared)
    undeclared = referenced - declared_set
    if declared and undeclared:
        out.append({
            "flag": "undeclared-variables",
            "detail": f"Used but not declared: {', '.join(sorted(undeclared))}.",
        })
    unused = declared_set - referenced
    if unused:
        out.append({
            "flag": "unused-variables",
            "detail": f"Declared but never used: {', '.join(sorted(unused))}.",
        })
    low = prompt_text.lower()
    if not re.search(r"format|json|bullet|list|table|markdown|sentence|paragraph|step", low):
        out.append({
            "flag": "no-output-format",
            "detail": "No explicit output format/structure is specified.",
        })
    if not re.search(r"you are|act as|your role|as an? ", low):
        out.append({
            "flag": "no-role",
            "detail": "No role or persona is set for the model.",
        })
    vague = sorted({w for w in _VAGUE if re.search(rf"\b{w}\b", low)})
    if vague:
        out.append({
            "flag": "vague-language",
            "detail": f"Vague terms that weaken instructions: {', '.join(vague)}.",
        })
    if len(prompt_text) > 600 and "#" not in prompt_text and "\n-" not in prompt_text:
        out.append({
            "flag": "long-unstructured",
            "detail": "Long prompt with no headings or lists to structure it.",
        })
    return out


def _fallback_suggestions(anti_patterns: list[dict]) -> list[str]:
    tips = {
        "undeclared-variables": "Declare every {{variable}} you reference so callers can fill it.",
        "unused-variables": "Remove or use the declared variables that never appear in the prompt.",
        "no-output-format": "State the exact output format you expect (a table, JSON, etc.).",
        "no-role": "Open with a clear role for the model (e.g. 'You are a risk reviewer…').",
        "vague-language": "Replace vague words with concrete, measurable criteria.",
        "long-unstructured": "Break the prompt into headed sections or a numbered list of steps.",
    }
    out = [tips[a["flag"]] for a in anti_patterns if a["flag"] in tips]
    if not out:
        out.append("This prompt looks solid; add a short worked example to anchor the output.")
    return out[:5]


def _render_prompt_md(
    pid: str, title: str, use_case: str, model_targets: list[str], variables: list[str],
    version: int, parent_id: str | None, created_by: str, created_at: str, prompt_text: str,
) -> str:
    mt = ", ".join(f'"{m}"' for m in model_targets)
    vs = ", ".join(f'"{v}"' for v in variables)
    pid_line = f"parent_id: {parent_id}" if parent_id else "parent_id: null"
    return (
        f"---\n"
        f"id: {pid}\n"
        f"title: {title}\n"
        f"use_case: \"{use_case}\"\n"
        f"model_targets: [{mt}]\n"
        f"variables: [{vs}]\n"
        f"version: {version}\n"
        f"{pid_line}\n"
        f"created_by: {created_by}\n"
        f"created_at: {created_at}\n"
        f"---\n\n"
        f"# {title}\n\n"
        f"## Prompt\n\n{prompt_text}\n"
    )


SUGGEST_SYSTEM = """You are a prompt-engineering reviewer. You improve prompts for clarity, \
structure, and reliable output. You are given a prompt and a list of deterministic \
anti-pattern flags already found. Return ONLY a markdown bullet list of 3-5 concrete, \
specific suggestions (one sentence each). Do not restate the flags verbatim; build on them."""


def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()


def _bullets(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m and m.group(1).strip():
            out.append(m.group(1).strip())
    return out
