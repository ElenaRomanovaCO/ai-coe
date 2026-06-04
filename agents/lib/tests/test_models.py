from agents.lib import models


def test_tier_mapping_covers_all_tiers():
    assert set(models.TIER_TO_MODEL_ID) == {"haiku-4-5", "sonnet-4-6", "opus-4-7"}
    assert models.TIER_TO_MODEL_ID["opus-4-7"] == models.OPUS_4_7


def test_inference_profile_prefixes_anthropic_only():
    assert models.inference_profile_id(models.SONNET_4_6) == "us.anthropic.claude-sonnet-4-6"
    # Titan is invoked with the bare ID.
    assert models.inference_profile_id(models.TITAN_EMBED_V2) == models.TITAN_EMBED_V2


def test_cost_usd_input_and_output():
    cost = models.cost_usd(models.OPUS_4_7, tokens_in=1000, tokens_out=1000)
    assert cost == round(0.015 + 0.075, 6)


def test_is_opus():
    assert models.is_opus(models.OPUS_4_7)
    assert not models.is_opus(models.SONNET_4_6)
