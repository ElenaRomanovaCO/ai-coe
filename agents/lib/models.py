"""Model IDs, tiers, and cost helpers for AWS Bedrock (us-east-1).

Model IDs confirmed via ``aws bedrock list-foundation-models --region us-east-1``.
Pricing is demo-grade and used only for the daily cost cap and observability
metrics — confirm against the Bedrock pricing page before relying on dollar
figures in production.
"""

from __future__ import annotations

from typing import Literal

REGION = "us-east-1"

# --- Base model IDs --------------------------------------------------------
SONNET_4_6 = "anthropic.claude-sonnet-4-6"
HAIKU_4_5 = "anthropic.claude-haiku-4-5-20251001-v1:0"
OPUS_4_7 = "anthropic.claude-opus-4-7"
TITAN_EMBED_V2 = "amazon.titan-embed-text-v2:0"

EMBED_DIMENSIONS = 1024

# Model tier as stored in modules.json (see registry.py).
ModelTier = Literal["haiku-4-5", "sonnet-4-6", "opus-4-7"]

TIER_TO_MODEL_ID: dict[ModelTier, str] = {
    "haiku-4-5": HAIKU_4_5,
    "sonnet-4-6": SONNET_4_6,
    "opus-4-7": OPUS_4_7,
}

# Models that count against the daily Opus cost cap (see cost_cap.py).
OPUS_MODEL_IDS: frozenset[str] = frozenset({OPUS_4_7})


def inference_profile_id(model_id: str, region_prefix: str = "us") -> str:
    """Regional cross-region inference profile ID.

    On-demand Anthropic invocation in us-east-1 generally requires a regional
    inference profile (e.g. ``us.anthropic.claude-sonnet-4-6``) rather than the
    bare model ID. Titan models are invoked with the bare ID.
    """
    if model_id.startswith("anthropic."):
        return f"{region_prefix}.{model_id}"
    return model_id


# --- Pricing ---------------------------------------------------------------
# USD per 1,000 tokens, as (input_rate, output_rate). Embedding models bill on
# input only.
PRICING_USD_PER_1K: dict[str, tuple[float, float]] = {
    SONNET_4_6: (0.003, 0.015),
    HAIKU_4_5: (0.0008, 0.004),
    OPUS_4_7: (0.015, 0.075),
    TITAN_EMBED_V2: (0.00002, 0.0),
}


def cost_usd(model_id: str, tokens_in: int, tokens_out: int = 0) -> float:
    """Estimated USD cost for a single call. Raises KeyError for unknown models."""
    rate_in, rate_out = PRICING_USD_PER_1K[model_id]
    return round((tokens_in / 1000) * rate_in + (tokens_out / 1000) * rate_out, 6)


def is_opus(model_id: str) -> bool:
    return model_id in OPUS_MODEL_IDS
