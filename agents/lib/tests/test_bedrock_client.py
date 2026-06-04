import pytest

from agents.lib import models
from agents.lib.base_agent import Usage
from agents.lib.bedrock_client import BedrockClient, _estimate_input_tokens
from agents.lib.cost_cap import OpusCapExceeded


class FakeBedrock:
    def __init__(self, response):
        self.response = response
        self.kwargs = None

    def converse(self, **kwargs):
        self.kwargs = kwargs
        return self.response


def test_estimate_input_tokens():
    msgs = [{"role": "user", "content": [{"text": "a" * 40}]}]
    assert _estimate_input_tokens(msgs, system="b" * 4) == (40 + 4) // 4


def test_converse_fills_usage_and_uses_inference_profile():
    fake = FakeBedrock({"usage": {"inputTokens": 100, "outputTokens": 50}, "output": {}})
    bc = BedrockClient(client=fake)
    usage = Usage()
    bc.converse(
        model_id=models.SONNET_4_6,
        messages=[{"role": "user", "content": [{"text": "hi"}]}],
        usage=usage,
    )
    assert usage.tokens_in == 100
    assert usage.tokens_out == 50
    assert usage.cost_usd > 0
    assert fake.kwargs["modelId"].startswith("us.anthropic")


def test_opus_cap_blocks_call():
    class AlwaysOverCap:
        def pre_check(self, estimate):
            raise OpusCapExceeded(5.0, estimate, 5.0)

        def add_usage(self, *a, **k):  # pragma: no cover - never reached
            raise AssertionError("should not record usage when capped")

    fake = FakeBedrock({"usage": {}})
    bc = BedrockClient(client=fake, cost_cap=AlwaysOverCap())
    with pytest.raises(OpusCapExceeded):
        bc.converse(
            model_id=models.OPUS_4_7,
            messages=[{"role": "user", "content": [{"text": "x"}]}],
        )
    assert fake.kwargs is None  # never called Bedrock
