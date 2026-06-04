"""Bedrock wrapper: Converse API with retry, cost computation, and Opus cap.

Thin enough to unit-test with a fake client (any object exposing ``converse``),
but production-ready: it estimates cost before each Opus call, enforces the daily
cap, records actual usage afterward, and retries throttling with backoff.
"""

from __future__ import annotations

import time
from typing import Any

from . import models
from .base_agent import Usage
from .cost_cap import OpusCostCap

_RETRYABLE = {"ThrottlingException", "ModelTimeoutException", "ServiceUnavailableException"}
_MAX_ATTEMPTS = 4


def _estimate_input_tokens(messages: list[dict], system: str | None) -> int:
    """Rough pre-call estimate: ~4 chars per token over all text content."""
    chars = len(system or "")
    for m in messages:
        for block in m.get("content", []):
            if isinstance(block, dict):
                chars += len(block.get("text", ""))
            elif isinstance(block, str):
                chars += len(block)
    return max(1, chars // 4)


class BedrockClient:
    def __init__(
        self,
        *,
        region: str = models.REGION,
        client: Any = None,
        cost_cap: OpusCostCap | None = None,
    ) -> None:
        self.region = region
        self._client = client
        self.cost_cap = cost_cap

    @property
    def client(self) -> Any:
        if self._client is None:
            import boto3

            self._client = boto3.client("bedrock-runtime", region_name=self.region)
        return self._client

    def converse(
        self,
        *,
        model_id: str,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        usage: Usage | None = None,
        use_inference_profile: bool = True,
    ) -> dict:
        """Call Bedrock Converse, enforce the Opus cap, and return the raw response.

        If ``usage`` is supplied (e.g. from an ``instrumented`` block) its token
        and cost fields are populated from the response.
        """
        if models.is_opus(model_id) and self.cost_cap is not None:
            est_in = _estimate_input_tokens(messages, system)
            estimate = models.cost_usd(model_id, est_in, max_tokens)
            self.cost_cap.pre_check(estimate)

        invoke_id = models.inference_profile_id(model_id) if use_inference_profile else model_id
        kwargs: dict[str, Any] = {
            "modelId": invoke_id,
            "messages": messages,
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
        }
        if system:
            kwargs["system"] = [{"text": system}]

        response = self._call_with_retry(kwargs)

        u = response.get("usage", {})
        tokens_in = int(u.get("inputTokens", 0))
        tokens_out = int(u.get("outputTokens", 0))
        call_cost = models.cost_usd(model_id, tokens_in, tokens_out)

        if usage is not None:
            usage.tokens_in += tokens_in
            usage.tokens_out += tokens_out
            usage.cost_usd += call_cost
            usage.model_id = model_id

        if models.is_opus(model_id) and self.cost_cap is not None:
            self.cost_cap.add_usage(tokens_in + tokens_out, call_cost)

        return response

    def _call_with_retry(self, kwargs: dict) -> dict:
        from botocore.exceptions import ClientError

        last: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                return self.client.converse(**kwargs)
            except ClientError as exc:
                code = exc.response.get("Error", {}).get("Code", "")
                if code not in _RETRYABLE or attempt == _MAX_ATTEMPTS - 1:
                    raise
                last = exc
                time.sleep(0.5 * (2**attempt))
        assert last is not None
        raise last
