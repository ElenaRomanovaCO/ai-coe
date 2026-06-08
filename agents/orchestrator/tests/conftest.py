"""Shared test fixtures and fakes for the orchestrator suite."""

from __future__ import annotations

import json

from agents.orchestrator.cache import ConfigCache

SAMPLE_MODULES = {
    "version": 1,
    "modules": [
        {
            "id": "module-1",
            "name": "AI Maturity Screener",
            "wave": 2,
            "purpose": "Assess an organization's AI maturity stage.",
            "when_to_use": ["evaluate readiness"],
            "example_queries": ["assess our AI readiness"],
            "agent_id": "AGENT-02",
            "model_tier": "sonnet-4-6",
            "worker_ids": [],
            "enabled": False,
        },
        {
            "id": "module-2",
            "name": "Asset Library",
            "wave": 1,
            "purpose": "Browse reference architectures and templates.",
            "when_to_use": ["find an asset"],
            "example_queries": ["show me healthcare architectures"],
            "agent_id": "AGENT-03",
            "model_tier": "haiku-4-5",
            "worker_ids": [],
            "enabled": False,
        },
        {
            "id": "module-4",
            "name": "Kit Builder",
            "wave": 3,
            "purpose": "Assemble an engagement kit from reusable parts.",
            "when_to_use": ["build a kit"],
            "example_queries": ["build a fraud detection kit"],
            "agent_id": "AGENT-05",
            "model_tier": "sonnet-4-6",
            "worker_ids": [],
            "enabled": False,
        },
    ],
}


def make_cache(
    modules: dict | None = None, agents_md: str = "## Test rules\nBe brief."
) -> ConfigCache:
    payload = json.dumps(modules or SAMPLE_MODULES)
    cache = ConfigCache(
        agents_md_loader=lambda: agents_md,
        modules_loader=lambda: payload,
    )
    cache.load_or_raise()
    return cache


class FakeLowLevelBedrock:
    """Stands in for a boto3 bedrock-runtime client.

    ``converse_responses`` is a list of full Converse responses returned in order.
    ``stream_specs`` is a list of event-lists returned by ``converse_stream``.
    """

    def __init__(self, converse_responses=None, stream_specs=None):
        self._converse = list(converse_responses or [])
        self._streams = list(stream_specs or [])
        self.calls: list[dict] = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return self._converse.pop(0)

    def converse_stream(self, **kwargs):
        self.calls.append(kwargs)
        return {"stream": iter(self._streams.pop(0))}


def converse_response(*, stop_reason: str, content: list[dict], tokens=(10, 5)) -> dict:
    return {
        "stopReason": stop_reason,
        "output": {"message": {"role": "assistant", "content": content}},
        "usage": {"inputTokens": tokens[0], "outputTokens": tokens[1]},
    }


def text_stream(text: str, *, stop_reason: str = "end_turn") -> list[dict]:
    """Build a converse_stream event list that emits ``text`` then stops."""
    return [
        {"messageStart": {"role": "assistant"}},
        {"contentBlockDelta": {"contentBlockIndex": 0, "delta": {"text": text}}},
        {"contentBlockStop": {"contentBlockIndex": 0}},
        {"messageStop": {"stopReason": stop_reason}},
        {"metadata": {"usage": {"inputTokens": 10, "outputTokens": 4}}},
    ]


def tool_use_stream(name: str, tool_use_id: str, input_obj: dict) -> list[dict]:
    """Build a converse_stream event list that requests one tool call."""
    return [
        {"messageStart": {"role": "assistant"}},
        {
            "contentBlockStart": {
                "contentBlockIndex": 0,
                "start": {"toolUse": {"toolUseId": tool_use_id, "name": name}},
            }
        },
        {
            "contentBlockDelta": {
                "contentBlockIndex": 0,
                "delta": {"toolUse": {"input": json.dumps(input_obj)}},
            }
        },
        {"contentBlockStop": {"contentBlockIndex": 0}},
        {"messageStop": {"stopReason": "tool_use"}},
        {"metadata": {"usage": {"inputTokens": 12, "outputTokens": 6}}},
    ]
