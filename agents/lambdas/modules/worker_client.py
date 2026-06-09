"""``invoke_worker`` — module agents call Layer 3 workers via the workers Lambda.

Mirrors :class:`ModuleInvoker`: lambda:Invoke ``aicoe-workers-lambda`` with the
router's ``{worker_id, args}`` contract. Injectable for tests (a fake client that
calls ``workers.router.route`` directly closes the loop without AWS).
"""

from __future__ import annotations

import json
from typing import Any

DEFAULT_WORKERS_FN = "aicoe-workers-lambda"


class WorkerInvoker:
    def __init__(
        self,
        *,
        function_name: str = DEFAULT_WORKERS_FN,
        region: str = "us-east-1",
        lambda_client: Any = None,
    ) -> None:
        self.function_name = function_name
        self.region = region
        self._lambda = lambda_client

    @property
    def lambda_client(self) -> Any:
        if self._lambda is None:
            import boto3

            self._lambda = boto3.client("lambda", region_name=self.region)
        return self._lambda

    def invoke(self, worker_id: str, args: dict) -> dict:
        resp = self.lambda_client.invoke(
            FunctionName=self.function_name,
            Payload=json.dumps({"worker_id": worker_id, "args": args}).encode("utf-8"),
        )
        if resp.get("FunctionError"):
            raw = resp.get("Payload")
            detail = raw.read().decode("utf-8") if hasattr(raw, "read") else str(raw)
            return {"status": "error", "worker_id": worker_id, "detail": detail[:500]}
        raw = resp.get("Payload")
        body = raw.read().decode("utf-8") if hasattr(raw, "read") else (raw or "")
        try:
            return json.loads(body) if body else {"status": "empty"}
        except json.JSONDecodeError:
            return {"status": "error", "worker_id": worker_id, "message": "Malformed response."}
