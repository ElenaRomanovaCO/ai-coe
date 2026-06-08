"""Bedrock wrapper: Converse API with retry, cost computation, and Opus cap.

Thin enough to unit-test with a fake client (any object exposing ``converse``),
but production-ready: it estimates cost before each Opus call, enforces the daily
cap, records actual usage afterward, and retries throttling with backoff.
"""

from __future__ import annotations

import json
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

    def _prepare(
        self,
        *,
        model_id: str,
        messages: list[dict],
        system: str | None,
        max_tokens: int,
        temperature: float,
        use_inference_profile: bool,
        tool_config: dict | None,
        guardrail_id: str | None,
        guardrail_version: str,
    ) -> dict[str, Any]:
        """Build Converse kwargs and run the Opus pre-check. Shared by both modes."""
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
        if tool_config:
            kwargs["toolConfig"] = tool_config
        if guardrail_id:
            kwargs["guardrailConfig"] = {
                "guardrailIdentifier": guardrail_id,
                "guardrailVersion": guardrail_version,
            }
        return kwargs

    def _record_usage(self, model_id: str, u: dict, usage: Usage | None) -> None:
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
        tool_config: dict | None = None,
        guardrail_id: str | None = None,
        guardrail_version: str = "DRAFT",
    ) -> dict:
        """Call Bedrock Converse, enforce the Opus cap, and return the raw response.

        If ``usage`` is supplied (e.g. from an ``instrumented`` block) its token
        and cost fields are populated from the response. Pass ``tool_config`` for
        tool use and ``guardrail_id`` to apply a Bedrock guardrail.
        """
        kwargs = self._prepare(
            model_id=model_id,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            use_inference_profile=use_inference_profile,
            tool_config=tool_config,
            guardrail_id=guardrail_id,
            guardrail_version=guardrail_version,
        )
        response = self._call_with_retry(kwargs)
        self._record_usage(model_id, response.get("usage", {}), usage)
        return response

    def converse_stream(
        self,
        *,
        model_id: str,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        usage: Usage | None = None,
        use_inference_profile: bool = True,
        tool_config: dict | None = None,
        guardrail_id: str | None = None,
        guardrail_version: str = "DRAFT",
    ) -> Any:
        """Stream a Converse turn, yielding normalized events.

        Yields dicts of one of these shapes (the agent loop consumes them):
          - ``{"type": "text", "text": <delta>}``
          - ``{"type": "tool_use", "tool_use": {"toolUseId", "name", "input"}}``
          - ``{"type": "stop", "stop_reason": <reason>}``
        ``usage`` (if given) is filled from the trailing metadata event. Streaming
        is not retried mid-stream; transient errors before the first event surface
        to the caller.
        """
        kwargs = self._prepare(
            model_id=model_id,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            use_inference_profile=use_inference_profile,
            tool_config=tool_config,
            guardrail_id=guardrail_id,
            guardrail_version=guardrail_version,
        )
        response = self.client.converse_stream(**kwargs)
        return self._iter_stream(model_id, response["stream"], usage)

    def _iter_stream(self, model_id: str, stream: Any, usage: Usage | None):
        # Accumulates streamed toolUse input (partial JSON across deltas) per
        # content-block index, emitting a single tool_use event at block stop.
        tool_blocks: dict[int, dict[str, Any]] = {}
        for event in stream:
            if "contentBlockStart" in event:
                ev = event["contentBlockStart"]
                idx = ev.get("contentBlockIndex", 0)
                start = ev.get("start", {})
                if "toolUse" in start:
                    tu = start["toolUse"]
                    tool_blocks[idx] = {
                        "toolUseId": tu.get("toolUseId"),
                        "name": tu.get("name"),
                        "input_json": "",
                    }
            elif "contentBlockDelta" in event:
                ev = event["contentBlockDelta"]
                idx = ev.get("contentBlockIndex", 0)
                delta = ev.get("delta", {})
                if "text" in delta:
                    yield {"type": "text", "text": delta["text"]}
                elif "toolUse" in delta and idx in tool_blocks:
                    tool_blocks[idx]["input_json"] += delta["toolUse"].get("input", "")
            elif "contentBlockStop" in event:
                idx = event["contentBlockStop"].get("contentBlockIndex", 0)
                if idx in tool_blocks:
                    block = tool_blocks.pop(idx)
                    raw = block.pop("input_json") or "{}"
                    try:
                        block["input"] = json.loads(raw)
                    except json.JSONDecodeError:
                        block["input"] = {}
                    yield {"type": "tool_use", "tool_use": block}
            elif "messageStop" in event:
                yield {"type": "stop", "stop_reason": event["messageStop"].get("stopReason")}
            elif "metadata" in event:
                self._record_usage(model_id, event["metadata"].get("usage", {}), usage)

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
