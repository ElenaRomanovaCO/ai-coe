"""End-to-end contract test: orchestrator invoke_module -> module-agents router -> AGENT-03.

This is the exact wire that is otherwise only exercised at deploy time (the user
flagged it). It proves:
  - ModuleInvoker serializes {agent_id, args: payload} as the router expects.
  - The payload shapes the orchestrator LLM is steered to produce (query / asset_id
    / filters) dispatch to the right AGENT-03 operation.

A fake Lambda client closes the loop: it decodes the Payload the orchestrator
would send and calls router.route() directly, returning router's result as the
Lambda response — so no AWS and no real Lambda, but the same contract.
"""

from __future__ import annotations

import io
import json

from agents.lib.registry import ModuleRegistry
from agents.orchestrator.tools.invoke_module import ModuleInvoker

from .conftest import ASSET_KEYS, FakeBedrockEmbed, FakeMetrics, FakeS3, FakeS3Vectors, vec

MODULE_2 = {
    "id": "module-2",
    "name": "Asset Library",
    "wave": 1,
    "purpose": "Browse, filter, and read curated AI delivery assets.",
    "when_to_use": ["find an asset"],
    "example_queries": ["show me healthcare assets"],
    "agent_id": "AGENT-03",
    "model_tier": "haiku-4-5",
    "worker_ids": [],
    "enabled": True,
}


class _RegistryProvider:
    """Stands in for the orchestrator's ConfigCache (exposes .registry)."""

    def __init__(self, registry: ModuleRegistry):
        self._registry = registry

    @property
    def registry(self) -> ModuleRegistry:
        return self._registry


class RouterBackedLambda:
    """Fake Lambda client: decodes the invoke payload and runs the real router."""

    def __init__(self, route_fn):
        self._route = route_fn
        self.last_event = None

    def invoke(self, *, FunctionName, Payload):
        self.last_event = json.loads(Payload.decode("utf-8"))
        result = self._route(self.last_event)
        return {"Payload": io.BytesIO(json.dumps(result).encode("utf-8"))}


def _invoker(monkeypatch, *, vectors=None):
    # Point the router's AGENT-03 factory at a fully-faked agent (no AWS).
    from agents.lambdas.modules import router
    from agents.lambdas.modules.agent_03_asset_library import AssetLibraryAgent

    def fake_agent():
        return AssetLibraryAgent(
            vault_bucket="vault-bucket",
            s3=FakeS3(dict(ASSET_KEYS)),
            bedrock=FakeBedrockEmbed(),
            s3vectors=FakeS3Vectors(vectors or []),
            metrics_client=FakeMetrics(),
        )

    monkeypatch.setitem(router.REGISTRY, "AGENT-03", fake_agent)
    registry = ModuleRegistry.model_validate({"version": 1, "modules": [MODULE_2]})
    return ModuleInvoker(
        registry_provider=_RegistryProvider(registry),
        lambda_client=RouterBackedLambda(router.route),
    )


def test_contract_query_payload_routes_to_search(monkeypatch):
    vectors = [vec("assets/healthcare/2/reference-arch-clinical-notes-rag.md")]
    invoker = _invoker(monkeypatch, vectors=vectors)
    # The shape the orchestrator builds for "find a clinical notes architecture".
    out = invoker.invoke("module-2", {"query": "clinical notes rag"})
    assert out["status"] == "ok"
    assert out["assets"][0]["id"] == "reference-arch-clinical-notes-rag"
    # The wire really carried {agent_id, args}.
    assert invoker.lambda_client.last_event == {
        "agent_id": "AGENT-03",
        "args": {"query": "clinical notes rag"},
    }


def test_contract_asset_id_payload_routes_to_get(monkeypatch):
    invoker = _invoker(monkeypatch)
    out = invoker.invoke("module-2", {"asset_id": "solution-pattern-fraud-scoring-agent"})
    assert out["status"] == "ok"
    assert out["asset"]["summary"]["industry"] == "financial-services"


def test_contract_id_alias_routes_to_get(monkeypatch):
    invoker = _invoker(monkeypatch)
    out = invoker.invoke("module-2", {"id": "reference-arch-clinical-notes-rag"})
    assert out["status"] == "ok"
    assert out["asset"]["summary"]["ai_stage"] == 2


def test_contract_filter_payload_routes_to_list(monkeypatch):
    invoker = _invoker(monkeypatch)
    out = invoker.invoke("module-2", {"industry": "healthcare"})
    assert out["status"] == "ok"
    assert [a["industry"] for a in out["assets"]] == ["healthcare"]


def test_contract_empty_payload_lists_all(monkeypatch):
    invoker = _invoker(monkeypatch)
    out = invoker.invoke("module-2", {})
    assert out["status"] == "ok"
    assert len(out["assets"]) == len(ASSET_KEYS)


def test_contract_disabled_module_never_reaches_router(monkeypatch):
    # If module-2 were disabled, ModuleInvoker returns the stub without invoking.
    invoker = _invoker(monkeypatch)
    invoker._registry_provider._registry.modules[0].enabled = False
    out = invoker.invoke("module-2", {"query": "x"})
    assert out["status"] == "not_implemented"
    assert invoker.lambda_client.last_event is None
