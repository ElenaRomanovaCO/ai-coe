"""``invoke_module`` — route to a module agent via Lambda (FR-008, FR-009).

Wraps ``lambda:InvokeFunction`` on ``aicoe-module-agents-lambda`` with a routing
payload of ``{agent_id, args}``. In Wave 1 no module agents are enabled yet, so
the common path is the graceful ``not_implemented`` stub: a disabled (or unknown)
module never reaches Lambda. The orchestrator surfaces that stub to the user
rather than crashing (FR-009 routes correctly but degrades cleanly).
"""

from __future__ import annotations

import json
from typing import Any

from agents.lib.registry import ModuleRegistry

DEFAULT_MODULE_AGENTS_FN = "aicoe-module-agents-lambda"


class ModuleInvoker:
    """Holds the target function name and a lazily-created Lambda client."""

    def __init__(
        self,
        *,
        registry_provider: Any,
        function_name: str = DEFAULT_MODULE_AGENTS_FN,
        region: str = "us-east-1",
        lambda_client: Any = None,
    ) -> None:
        self._registry_provider = registry_provider
        self.function_name = function_name
        self.region = region
        self._lambda = lambda_client

    @property
    def lambda_client(self) -> Any:
        if self._lambda is None:
            import boto3

            self._lambda = boto3.client("lambda", region_name=self.region)
        return self._lambda

    def invoke(self, module_id: str, payload: dict) -> dict:
        registry: ModuleRegistry = self._registry_provider.registry
        module = registry.by_id(module_id)
        if module is None:
            return {
                "status": "not_implemented",
                "module_id": module_id,
                "message": f"Module '{module_id}' is not in the registry.",
            }
        if not module.enabled:
            return {
                "status": "not_implemented",
                "module_id": module_id,
                "agent_id": module.agent_id,
                "message": (
                    f"Module '{module.name}' ({module.agent_id}) is not yet available. "
                    "It will be enabled in a later wave."
                ),
            }

        request = {"agent_id": module.agent_id, "args": payload}
        resp = self.lambda_client.invoke(
            FunctionName=self.function_name,
            Payload=json.dumps(request).encode("utf-8"),
        )
        if resp.get("FunctionError"):
            raw = resp.get("Payload")
            detail = raw.read().decode("utf-8") if hasattr(raw, "read") else str(raw)
            return {
                "status": "error",
                "module_id": module_id,
                "agent_id": module.agent_id,
                "message": "The module agent failed to process the request.",
                "detail": detail[:500],
            }
        raw = resp.get("Payload")
        body = raw.read().decode("utf-8") if hasattr(raw, "read") else (raw or "")
        try:
            return json.loads(body) if body else {"status": "empty"}
        except json.JSONDecodeError:
            return {
                "status": "error",
                "module_id": module_id,
                "message": "Malformed module response.",
            }


def invoke_module(module_id: str, payload: dict, *, invoker: ModuleInvoker) -> dict:
    return invoker.invoke(module_id, payload)
