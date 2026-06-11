"""AGENT-09 — Q&A (Module 8), Sonnet 4.6 tier.

Two modes over the same agent:

* **Community** — browse/post question threads, answer them, and upvote answers.
  Threads are markdown at ``vault/qa/{yyyy-mm}/{id}.md`` (re-embedded, so they become
  searchable + citable); upvotes live in a sidecar ``vault/qa/_metadata/{id}.json`` and
  per-user votes in ``sessions/qa-votes/{slug}.json`` (idempotent, one per user per
  answer) — the AGENT-03 metadata-sidecar pattern.
* **AI** — ``answer_with_citations`` runs RAG over the whole Knowledge Base (Titan embed
  → S3 Vectors) and makes **one Sonnet call** to synthesize a grounded answer with
  citations, a confidence, and related threads. Mechanical retrieval + a single model
  call, per the AGENT-05/24 precedent; deterministic fallback if the model fails.
  Non-streaming (one invoke returns the full answer), like the other module agents.

Operations (on ``op``):
  - ``list_threads``           — filter/sort the thread list (default)
  - ``get_thread``             — one thread with answers + upvotes
  - ``post_thread``            — write a new thread (optionally with an initial answer)
  - ``answer_thread``          — append an answer to a thread
  - ``upvote``                 — upvote an answer (idempotent per user)
  - ``answer_with_citations``  — AI-mode synthesized answer over the KB
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import UTC, datetime
from typing import Any

import yaml
from botocore.exceptions import ClientError

from agents.lib import models as lib_models
from agents.lib.base_agent import instrumented
from agents.lib.bedrock_client import BedrockClient

from .agent_03_asset_library import _split_frontmatter
from .base import ModuleAgent

AGENT_ID = "AGENT-09"
QA_PREFIX = "qa/"
META_PREFIX = "qa/_metadata/"
VOTES_PREFIX = "qa-votes/"
QA_ROUTE = "/modules/qa"
_SLUG_UNSAFE = re.compile(r"[^a-zA-Z0-9._-]+")
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}

# Map a content type (reembed's leading-path-segment tag) to its detail route, so AI
# citations deep-link into the right module.
_ROUTE_BY_TYPE = {
    "assets": "/modules/asset-library",
    "regs": "/modules/compliance-tracker",
    "tools": "/modules/tools-repo",
    "vendors": "/modules/vendor-eval",
    "prompts": "/modules/prompt-studio",
    "qa": "/modules/qa",
}


def _slug(name: str) -> str:
    s = _SLUG_UNSAFE.sub("-", (name or "").strip()).strip("-").lower()
    return s or "anon"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _title_of(fm: dict, key: str) -> str:
    for field in ("title", "name", "question"):
        if fm.get(field):
            return str(fm[field])
    return str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md"))


class QaAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.SONNET_4_6

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        sessions_bucket: str | None = None,
        vector_bucket: str = "aicoe-content-vectors",
        index_name: str = "aicoe-content",
        embed_model: str = lib_models.TITAN_EMBED_V2,
        region: str = lib_models.REGION,
        s3: Any = None,
        s3vectors: Any = None,
        bedrock: Any = None,
        bedrock_client: BedrockClient | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.vector_bucket = vector_bucket
        self.index_name = index_name
        self.embed_model = embed_model
        self.region = region
        self._s3 = s3
        self._s3vectors = s3vectors
        self._bedrock = bedrock
        self.bedrock_client = bedrock_client or BedrockClient(client=bedrock)

    # --- lazy clients ------------------------------------------------------
    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    @property
    def s3vectors(self) -> Any:
        if self._s3vectors is None:
            import boto3

            self._s3vectors = boto3.client("s3vectors", region_name=self.region)
        return self._s3vectors

    @property
    def bedrock(self) -> Any:
        if self._bedrock is None:
            import boto3

            self._bedrock = boto3.client("bedrock-runtime", region_name=self.region)
        return self._bedrock

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        if "thread_id" not in args and args.get("id"):
            args = {**args, "thread_id": args["id"]}
        op = args.get("op")
        if op == "get_thread" or (op is None and args.get("thread_id")):
            return self.run_tool("get_thread", lambda _u: self._get(args))
        if op == "post_thread":
            return self.run_tool("post_thread", lambda _u: self._post(args))
        if op == "answer_thread":
            return self.run_tool("answer_thread", lambda _u: self._answer(args))
        if op == "upvote":
            return self.run_tool("upvote", lambda _u: self._upvote(args))
        if op == "answer_with_citations":
            return self.run_tool("answer_with_citations", lambda _u: self._answer_ai(args))
        return self.run_tool("list_threads", lambda _u: self._list(args))

    # --- thread corpus I/O -------------------------------------------------
    def _thread_keys(self) -> list[str]:
        keys: list[str] = []
        token: str | None = None
        while True:
            kw: dict[str, Any] = {"Bucket": self.vault_bucket, "Prefix": QA_PREFIX}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            for o in resp.get("Contents", []):
                k = o["Key"]
                if k.endswith(".md") and "/_metadata/" not in k:
                    keys.append(k)
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
        return keys

    def _read(self, key: str) -> str:
        return self.s3.get_object(Bucket=self.vault_bucket, Key=key)["Body"].read().decode("utf-8")

    def _all_threads(self) -> list[tuple[dict, str]]:
        """(frontmatter, key) for every thread file."""
        out: list[tuple[dict, str]] = []
        for key in self._thread_keys():
            fm, _ = _split_frontmatter(self._read(key))
            out.append((fm, key))
        return out

    def _load_thread(self, thread_id: str) -> tuple[dict, str] | None:
        target = str(thread_id)
        basename = f"/{target}.md"
        fallback: tuple[dict, str] | None = None
        for fm, key in self._all_threads():
            if str(fm.get("id")) == target:
                return fm, key
            if key.endswith(basename):
                fallback = (fm, key)
        return fallback

    # --- JSON sidecars (upvotes + per-user votes) --------------------------
    def _read_json(self, bucket: str, key: str, default: dict) -> dict:
        try:
            raw = self.s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _NOT_FOUND:
                return dict(default)
            raise
        except (KeyError, FileNotFoundError):
            return dict(default)
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return dict(default)

    def _write_json(self, bucket: str, key: str, obj: dict) -> None:
        self.s3.put_object(
            Bucket=bucket, Key=key,
            Body=json.dumps(obj, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    def _meta_key(self, thread_id: str) -> str:
        return f"{META_PREFIX}{thread_id}.json"

    def _votes_key(self, display_name: str) -> str:
        return f"{VOTES_PREFIX}{_slug(display_name)}.json"

    def _upvotes(self, thread_id: str) -> dict[str, int]:
        meta = self._read_json(self.vault_bucket, self._meta_key(thread_id), {"answer_upvotes": {}})
        return {str(k): int(v) for k, v in (meta.get("answer_upvotes") or {}).items()}

    # --- summaries ---------------------------------------------------------
    def _summary(self, fm: dict, key: str) -> dict[str, Any]:
        tid = str(fm.get("id") or key.rsplit("/", 1)[-1].removesuffix(".md"))
        answers = fm.get("answers") or []
        upvotes = self._upvotes(tid)
        return {
            "id": tid,
            "question": str(fm.get("question", "")),
            "tags": [str(t) for t in (fm.get("tags") or [])],
            "posted_by": str(fm.get("posted_by", "")),
            "posted_at": str(fm.get("posted_at", "")),
            "answer_count": len(answers),
            "score": sum(upvotes.values()),
        }

    # --- operations: read --------------------------------------------------
    def _list(self, args: dict[str, Any]) -> dict[str, Any]:
        tag = (args.get("tag") or "").strip().lower()
        query = (args.get("query") or "").strip().lower()
        sort = (args.get("sort") or "recent").strip().lower()

        out = []
        for fm, key in self._all_threads():
            s = self._summary(fm, key)
            if tag and tag not in {t.lower() for t in s["tags"]}:
                continue
            if query and query not in s["question"].lower():
                continue
            out.append(s)

        if sort == "upvotes":
            out.sort(key=lambda t: (t["score"], t["posted_at"]), reverse=True)
        elif sort == "unanswered":
            out.sort(key=lambda t: (t["answer_count"], _neg(t["posted_at"])))
        else:  # recent
            out.sort(key=lambda t: t["posted_at"], reverse=True)
        return {"status": "ok", "threads": out}

    def _get(self, args: dict[str, Any]) -> dict[str, Any]:
        thread_id = args.get("thread_id")
        if not thread_id:
            return {"status": "error", "message": "thread_id is required."}
        loaded = self._load_thread(thread_id)
        if loaded is None:
            return {"status": "not_found", "thread_id": thread_id, "message": "No such thread."}
        fm, key = loaded
        tid = str(fm.get("id") or thread_id)
        upvotes = self._upvotes(tid)
        voted: set[str] = set()
        if args.get("display_name"):
            vf = self._read_json(
                self.sessions_bucket, self._votes_key(args["display_name"]), {"voted": []}
            )
            voted = {v.split(":", 1)[1] for v in vf.get("voted", []) if v.startswith(f"{tid}:")}
        answers = [
            {
                "id": str(a.get("id")),
                "text": str(a.get("text", "")),
                "posted_by": str(a.get("posted_by", "")),
                "posted_at": str(a.get("posted_at", "")),
                "upvotes": upvotes.get(str(a.get("id")), 0),
                "voted": str(a.get("id")) in voted,
            }
            for a in (fm.get("answers") or [])
        ]
        answers.sort(key=lambda a: a["upvotes"], reverse=True)
        return {
            "status": "ok",
            "thread": {
                "id": tid,
                "question": str(fm.get("question", "")),
                "tags": [str(t) for t in (fm.get("tags") or [])],
                "posted_by": str(fm.get("posted_by", "")),
                "posted_at": str(fm.get("posted_at", "")),
                "answers": answers,
                "score": sum(upvotes.values()),
            },
        }

    # --- operations: write -------------------------------------------------
    def _write_thread(self, key: str, fm: dict) -> None:
        front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True)
        body = _render_body(fm)
        content = f"---\n{front}---\n\n{body}"
        self.s3.put_object(
            Bucket=self.vault_bucket, Key=key,
            Body=content.encode("utf-8"), ContentType="text/markdown",
        )

    def _post(self, args: dict[str, Any]) -> dict[str, Any]:
        question = (args.get("question") or "").strip()
        if not question:
            return {"status": "error", "message": "question is required."}
        posted_by = str(args.get("display_name") or "anon")
        posted_at = _now_iso()
        tid = "qa-" + (_slug(question)[:40].strip("-") or uuid.uuid4().hex[:10])
        # Disambiguate if the slug already exists.
        if self._load_thread(tid) is not None:
            tid = f"{tid}-{uuid.uuid4().hex[:6]}"
        answers = []
        initial = (args.get("initial_answer") or "").strip()
        if initial:
            answers.append(
                {"id": "ans-1", "text": initial, "posted_by": posted_by, "posted_at": posted_at}
            )
        fm = {
            "id": tid,
            "question": question,
            "tags": [str(t) for t in (args.get("tags") or [])],
            "posted_by": posted_by,
            "posted_at": posted_at,
            "answers": answers,
        }
        ym = posted_at[:7]  # yyyy-mm
        key = f"{QA_PREFIX}{ym}/{tid}.md"
        self._write_thread(key, fm)
        return {"status": "ok", "thread": self._summary(fm, key)}

    def _answer(self, args: dict[str, Any]) -> dict[str, Any]:
        thread_id = args.get("thread_id")
        text = (args.get("answer_text") or "").strip()
        if not thread_id or not text:
            return {"status": "error", "message": "thread_id and answer_text are required."}
        loaded = self._load_thread(thread_id)
        if loaded is None:
            return {"status": "not_found", "thread_id": thread_id, "message": "No such thread."}
        fm, key = loaded
        answers = list(fm.get("answers") or [])
        answers.append({
            "id": f"ans-{len(answers) + 1}",
            "text": text,
            "posted_by": str(args.get("display_name") or "anon"),
            "posted_at": _now_iso(),
        })
        fm["answers"] = answers
        self._write_thread(key, fm)
        return {"status": "ok", "thread": self._summary(fm, key)}

    def _upvote(self, args: dict[str, Any]) -> dict[str, Any]:
        thread_id = args.get("thread_id")
        answer_id = args.get("answer_id")
        display_name = args.get("display_name")
        if not thread_id or not answer_id or not display_name:
            return {
                "status": "error",
                "message": "thread_id, answer_id, and display_name are required.",
            }
        loaded = self._load_thread(thread_id)
        if loaded is None:
            return {"status": "not_found", "thread_id": thread_id}
        fm, _ = loaded
        tid = str(fm.get("id") or thread_id)
        if not any(str(a.get("id")) == str(answer_id) for a in (fm.get("answers") or [])):
            return {"status": "error", "message": "No such answer."}

        vkey = self._votes_key(display_name)
        votes = self._read_json(self.sessions_bucket, vkey, {"voted": []})
        token = f"{tid}:{answer_id}"
        meta_key = self._meta_key(tid)
        meta = self._read_json(self.vault_bucket, meta_key, {"answer_upvotes": {}})
        counts = {str(k): int(v) for k, v in (meta.get("answer_upvotes") or {}).items()}

        already = token in votes.get("voted", [])
        if not already:  # one upvote per user per answer
            counts[str(answer_id)] = counts.get(str(answer_id), 0) + 1
            votes.setdefault("voted", []).append(token)
            meta["answer_upvotes"] = counts
            self._write_json(self.vault_bucket, meta_key, meta)
            self._write_json(self.sessions_bucket, vkey, votes)
        return {
            "status": "ok",
            "thread_id": tid,
            "answer_id": str(answer_id),
            "upvotes": counts.get(str(answer_id), 0),
            "voted": True,
        }

    # --- operations: AI mode (RAG + one Sonnet call) -----------------------
    def _embed(self, text: str) -> list[float]:
        resp = self.bedrock.invoke_model(
            modelId=self.embed_model,
            body=json.dumps(
                {"inputText": text, "dimensions": lib_models.EMBED_DIMENSIONS, "normalize": True}
            ),
        )
        return json.loads(resp["body"].read())["embedding"]

    def _retrieve(self, question: str, top_k: int) -> list[dict]:
        resp = self.s3vectors.query_vectors(
            vectorBucketName=self.vector_bucket,
            indexName=self.index_name,
            queryVector={"float32": self._embed(question)},
            topK=max(top_k * 3, top_k),
            returnMetadata=True,
        )
        seen: set[str] = set()
        hits: list[dict] = []
        for v in resp.get("vectors", []):
            meta = v.get("metadata", {}) or {}
            key = meta.get("file_path") or v.get("key", "").split("#", 1)[0]
            if not key or key in seen:
                continue
            seen.add(key)
            ctype = str(meta.get("content_type") or key.split("/", 1)[0])
            hits.append({"key": key, "content_type": ctype})
            if len(hits) >= top_k:
                break
        return hits

    def _answer_ai(self, args: dict[str, Any]) -> dict[str, Any]:
        question = (args.get("question") or "").strip()
        if not question:
            return {"status": "error", "message": "question is required."}
        top_k = int(args.get("top_k", 5))
        hits = self._retrieve(question, top_k)

        citations: list[dict] = []
        related: list[dict] = []
        context_blocks: list[str] = []
        for h in hits:
            try:
                fm, body = _split_frontmatter(self._read(h["key"]))
            except (ClientError, KeyError, FileNotFoundError):
                continue
            cid = str(fm.get("id") or h["key"].rsplit("/", 1)[-1].removesuffix(".md"))
            title = _title_of(fm, h["key"])
            ctype = h["content_type"]
            route = _ROUTE_BY_TYPE.get(ctype)
            url = f"{route}/{cid}" if route else None
            citations.append({
                "id": cid, "title": title, "content_type": ctype,
                "file_path": h["key"], "url": url,
            })
            if ctype == "qa":
                related.append({"id": cid, "question": str(fm.get("question", title)), "url": url})
            context_blocks.append(f"[{title}] ({ctype})\n{body.strip()[:800]}")

        confidence = "high" if len(citations) >= 3 else "medium" if citations else "low"
        answer = self._synthesize(question, context_blocks, citations)
        return {
            "status": "ok",
            "answer": answer,
            "citations": citations,
            "confidence": confidence,
            "related_threads": related,
        }

    def _synthesize(self, question: str, context_blocks: list[str], citations: list[dict]) -> str:
        if not context_blocks:
            return (
                "I couldn't find anything in the Knowledge Base for that question. "
                "Try rephrasing, or post it as a community thread."
            )
        context = "\n\n---\n\n".join(context_blocks)
        user_text = (
            f"Question: {question}\n\n"
            f"Knowledge Base context (each block is one source):\n\n{context}\n\n"
            "Answer the question using ONLY this context. Cite the sources you use by their "
            "[title]. If the context is insufficient, say so plainly."
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
                    system=ANSWER_SYSTEM,
                    max_tokens=900,
                    usage=usage,
                )
            text = _extract_text(resp.get("output", {}).get("message", {}))
            if text:
                return text
        except Exception:  # noqa: BLE001 — deterministic fallback to the sources
            pass
        names = ", ".join(c["title"] for c in citations[:3])
        return (
            "I couldn't synthesize a full answer just now, but the most relevant Knowledge "
            f"Base sources are: {names}. Open them for the details."
        )


def _neg(iso: str) -> str:
    # Sort helper: invert an ISO timestamp's ordering for a secondary descending sort.
    return "".join(chr(255 - ord(c)) for c in iso)


def _render_body(fm: dict) -> str:
    question = str(fm.get("question", ""))
    lines = [f"# {question}", ""]
    answers = fm.get("answers") or []
    if answers:
        lines.append("## Answers")
        lines.append("")
        for a in answers:
            lines.append(f"**{a.get('posted_by', 'demo')}** — {a.get('text', '')}")
            lines.append("")
    else:
        lines.append("_No answers yet._")
        lines.append("")
    return "\n".join(lines)


ANSWER_SYSTEM = """You are the Knowledge Base Q&A assistant for an AI consulting platform. \
You answer a question using ONLY the provided context blocks, which are excerpts from \
curated assets, regulations, tools, vendor evaluations, and prior Q&A. Cite the sources you \
draw on by their [title]. Be concise and practical. If the context does not cover the \
question, say so rather than inventing an answer. Do not mention specific company names."""


def _extract_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content", []) if "text" in block
    ).strip()
