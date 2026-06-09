"""AGENT-02 — AI Maturity Assessment (Module 1), Sonnet 4.6 tier.

The first stateful, worker-orchestrating module agent. It runs a conversational
assessment by delegating to three deterministic workers (WORKER-01 question_picker,
WORKER-02 scorer, WORKER-03 recommender) and persists in-progress state to S3
(AD-04, no DB). Per the hard guardrail it NEVER scores directly — WORKER-02 owns
the (deterministic) stage. Conversational phrasing is mechanical in this Wave-1
build (the question bank is already plain-language); LLM acknowledgments can be
layered on later without changing the contract.

Operations (dispatched from :meth:`handle` on ``op``):
  - ``start``  — begin an assessment, return the first question
  - ``answer`` — record an answer, return the next question or the final result
  - ``get``    — fetch an assessment's state/result
  - ``list``   — list a user's assessments
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import ClientError

from agents.lib import models as lib_models

from .base import ModuleAgent
from .worker_client import WorkerInvoker

AGENT_ID = "AGENT-02"
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}
_SLUG_UNSAFE = re.compile(r"[^a-zA-Z0-9._-]+")

# Coarse industry inference from free-text client context.
_INDUSTRIES = {
    "healthcare": ["health", "clinical", "patient", "hospital", "insurer", "payer", "provider"],
    "financial-services": ["bank", "fintech", "financial", "fraud", "insurance", "lending", "pay"],
    "retail": ["retail", "ecommerce", "e-commerce", "shopper", "merchand", "store"],
    "manufacturing": ["manufactur", "factory", "plant", "supply chain", "predictive maintenance"],
    "energy": ["energy", "utility", "grid", "oil", "gas", "renewable"],
    "public-sector": ["government", "public sector", "agency", "municipal", "citizen"],
}


def _slug(name: str) -> str:
    s = _SLUG_UNSAFE.sub("-", (name or "").strip()).strip("-").lower()
    return s or "anon"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _infer_industry(context: str | None) -> str:
    text = (context or "").lower()
    for industry, kws in _INDUSTRIES.items():
        if any(k in text for k in kws):
            return industry
    return ""


class AssessmentAgent(ModuleAgent):
    agent_id = AGENT_ID
    model_id = lib_models.SONNET_4_6

    def __init__(
        self,
        *,
        vault_bucket: str | None = None,
        sessions_bucket: str | None = None,
        region: str = lib_models.REGION,
        s3: Any = None,
        worker_invoker: WorkerInvoker | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.vault_bucket = vault_bucket or os.environ.get("VAULT_BUCKET", "")
        self.sessions_bucket = sessions_bucket or os.environ.get("SESSIONS_BUCKET", "")
        self.region = region
        self._s3 = s3
        self.workers = worker_invoker or WorkerInvoker(region=region)

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3

            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    # --- dispatch ----------------------------------------------------------
    def handle(self, args: dict[str, Any]) -> dict[str, Any]:
        op = args.get("op", "start")
        if op == "start":
            if not args.get("display_name"):
                return {"status": "error", "message": "display_name is required."}
            return self.run_tool("start_assessment", lambda _u: self._start(args))
        if op == "answer":
            if not args.get("assessment_id") or args.get("user_answer") is None:
                return {"status": "error", "message": "assessment_id and user_answer are required."}
            return self.run_tool("assessment_turn", lambda _u: self._answer(args))
        if op == "get":
            return self.run_tool("get_assessment", lambda _u: self._get(args.get("assessment_id")))
        if op == "list":
            name = args.get("display_name")
            return self.run_tool("list_assessments", lambda _u: self._list(name))
        return {"status": "error", "message": f"Unknown op '{op}'."}

    # --- state I/O ---------------------------------------------------------
    def _state_key(self, display_name: str, assessment_id: str) -> str:
        return f"assessments/{_slug(display_name)}/{assessment_id}.json"

    def _load_state(self, assessment_id: str, display_name: str | None = None) -> dict | None:
        # assessment_id encodes nothing about the user, so locate by listing if the
        # display_name isn't supplied (answer turns don't carry it).
        if display_name:
            keys = [self._state_key(display_name, assessment_id)]
        else:
            keys = self._find_state_keys(assessment_id)
        for key in keys:
            try:
                raw = self.s3.get_object(Bucket=self.sessions_bucket, Key=key)["Body"].read()
            except ClientError as exc:
                if exc.response.get("Error", {}).get("Code") in _NOT_FOUND:
                    continue
                raise
            except (KeyError, FileNotFoundError):
                continue
            return json.loads(raw)
        return None

    def _find_state_keys(self, assessment_id: str) -> list[str]:
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix="assessments/")
        return [
            o["Key"]
            for o in resp.get("Contents", [])
            if o["Key"].endswith(f"/{assessment_id}.json")
        ]

    def _save_state(self, state: dict) -> None:
        key = self._state_key(state["display_name"], state["assessment_id"])
        self.s3.put_object(
            Bucket=self.sessions_bucket,
            Key=key,
            Body=json.dumps(state, separators=(",", ":")).encode("utf-8"),
            ContentType="application/json",
        )

    # --- operations --------------------------------------------------------
    def _start(self, args: dict[str, Any]) -> dict[str, Any]:
        assessment_id = "assess-" + uuid.uuid4().hex[:12]
        context = args.get("client_context")
        state = {
            "assessment_id": assessment_id,
            "display_name": args["display_name"],
            "client_context": context,
            "industry": _infer_industry(context),
            "status": "in_progress",
            "created_at": _now_iso(),
            "history": [],
            "pending": None,
            "result": None,
        }
        q = self.workers.invoke("WORKER-01", {"history": []})
        if q.get("status") != "ok":
            return {"status": "error", "message": "Could not start the assessment."}
        state["pending"] = {"question": q["question_text"], "dimension": q["dimension"]}
        self._save_state(state)
        return {
            "status": "ok",
            "assessment_id": assessment_id,
            "is_complete": False,
            "next_question": q["question_text"],
        }

    def _answer(self, args: dict[str, Any]) -> dict[str, Any]:
        assessment_id = args["assessment_id"]
        state = self._load_state(assessment_id, args.get("display_name"))
        if state is None:
            return {"status": "not_found", "assessment_id": assessment_id}
        if state["status"] == "complete":
            return {"status": "ok", "is_complete": True, "result": state["result"]}
        pending = state.get("pending")
        if not pending:
            return {"status": "error", "message": "No pending question for this assessment."}

        state["history"].append(
            {
                "question": pending["question"],
                "dimension": pending["dimension"],
                "answer": args["user_answer"],
            }
        )
        state["pending"] = None

        nxt = self.workers.invoke("WORKER-01", {"history": state["history"]})
        if nxt.get("status") != "ok":
            return {"status": "error", "message": "Assessment flow error."}

        if not nxt.get("is_final"):
            state["pending"] = {"question": nxt["question_text"], "dimension": nxt["dimension"]}
            self._save_state(state)
            return {"status": "ok", "is_complete": False, "next_question": nxt["question_text"]}

        return self._finalize(state)

    def _finalize(self, state: dict) -> dict[str, Any]:
        score = self.workers.invoke("WORKER-02", {"history": state["history"]})
        if score.get("status") != "ok":
            return {"status": "error", "message": "Scoring failed."}
        dimension_scores = score["dimension_scores"]
        weak = [d for d, s in dimension_scores.items() if s <= 2]
        industry = state.get("industry") or ""

        recs = self.workers.invoke(
            "WORKER-03",
            {"stage": score["stage"], "industry": industry, "weak_dimensions": weak},
        )
        recommendations = recs.get("recommendations", []) if recs.get("status") == "ok" else []

        vault_path = self._write_assessment_file(state, score, recommendations)
        result = {
            "assessment_id": state["assessment_id"],
            "stage": score["stage"],
            "rationale": score["rationale"],
            "dimension_scores": dimension_scores,
            "recommendations": recommendations,
            "vault_file_path": vault_path,
        }
        state["status"] = "complete"
        state["result"] = result
        self._save_state(state)
        return {"status": "ok", "is_complete": True, "result": result}

    def _write_assessment_file(self, state: dict, score: dict, recommendations: list[dict]) -> str:
        ts_key = state["created_at"].replace(":", "-")
        key = f"assessments/{_slug(state['display_name'])}/{ts_key}.md"
        scores_yaml = "\n".join(f"  {d}: {s}" for d, s in score["dimension_scores"].items())
        recs_md = "\n".join(
            f"- {r.get('title', r.get('id'))} (`{r.get('file_path')}`)" for r in recommendations
        ) or "- (none)"
        body = (
            f"---\n"
            f"id: {state['assessment_id']}\n"
            f"type: assessment\n"
            f"display_name: {state['display_name']}\n"
            f"client_context: {state.get('client_context') or ''}\n"
            f"industry: {state.get('industry') or ''}\n"
            f"stage: {score['stage']}\n"
            f"dimension_scores:\n{scores_yaml}\n"
            f"created_at: {state['created_at']}\n"
            f"---\n\n"
            f"# AI Maturity Assessment — Stage {score['stage']} of 5\n\n"
            f"{score['rationale']}\n\n"
            f"## Recommended next steps\n\n{recs_md}\n"
        )
        self.s3.put_object(
            Bucket=self.vault_bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="text/markdown",
        )
        return key

    def _get(self, assessment_id: str | None) -> dict[str, Any]:
        if not assessment_id:
            return {"status": "error", "message": "assessment_id is required."}
        state = self._load_state(assessment_id)
        if state is None:
            return {"status": "not_found", "assessment_id": assessment_id}
        if state["status"] == "complete":
            return {"status": "ok", "is_complete": True, "result": state["result"]}
        return {
            "status": "ok",
            "is_complete": False,
            "next_question": (state.get("pending") or {}).get("question"),
        }

    def _list(self, display_name: str | None) -> dict[str, Any]:
        if not display_name:
            return {"status": "error", "message": "display_name is required."}
        prefix = f"assessments/{_slug(display_name)}/"
        resp = self.s3.list_objects_v2(Bucket=self.sessions_bucket, Prefix=prefix)
        out = []
        for o in resp.get("Contents", []):
            if not o["Key"].endswith(".json"):
                continue
            aid = o["Key"].rsplit("/", 1)[-1].removesuffix(".json")
            state = self._load_state(aid, display_name)
            if not state:
                continue
            out.append(
                {
                    "assessment_id": state["assessment_id"],
                    "status": state["status"],
                    "stage": (state.get("result") or {}).get("stage"),
                    "created_at": state.get("created_at"),
                }
            )
        out.sort(key=lambda a: a.get("created_at") or "", reverse=True)
        return {"status": "ok", "assessments": out}
