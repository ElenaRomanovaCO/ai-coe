import pytest
from pydantic import ValidationError

from agents.lib.registry import json_schema, load_registry


def test_empty_registry_loads():
    reg = load_registry('{"version": 1, "modules": []}')
    assert reg.version == 1
    assert reg.modules == []
    assert reg.enabled_modules() == []


def test_module_entry_defaults_and_lookup():
    reg = load_registry(
        {
            "version": 1,
            "modules": [
                {
                    "id": "module-2",
                    "name": "Asset Library",
                    "wave": 1,
                    "purpose": "Find and reuse assets",
                    "agent_id": "AGENT-03",
                    "model_tier": "sonnet-4-6",
                }
            ],
        }
    )
    entry = reg.by_id("module-2")
    assert entry is not None
    assert entry.name == "Asset Library"
    assert entry.enabled is False  # defaults off until implemented
    assert entry.worker_ids == []
    assert reg.enabled_modules() == []


def test_invalid_wave_rejected():
    with pytest.raises(ValidationError):
        load_registry(
            {
                "version": 1,
                "modules": [
                    {
                        "id": "m",
                        "name": "n",
                        "wave": 8,  # out of 1..7
                        "purpose": "p",
                        "agent_id": "A",
                        "model_tier": "sonnet-4-6",
                    }
                ],
            }
        )


def test_invalid_model_tier_rejected():
    with pytest.raises(ValidationError):
        load_registry(
            {
                "version": 1,
                "modules": [
                    {
                        "id": "m",
                        "name": "n",
                        "wave": 1,
                        "purpose": "p",
                        "agent_id": "A",
                        "model_tier": "gpt-4",
                    }
                ],
            }
        )


def test_json_schema_exposes_modules():
    schema = json_schema()
    assert "modules" in schema["properties"]
    assert schema["properties"]["version"]["default"] == 1
