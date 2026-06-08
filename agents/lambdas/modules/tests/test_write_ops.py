"""Save / Rate / Flag write ops (FR-012/013) — round-trip via the agent's S3 fakes."""

from .conftest import make_agent

A_ID = "reference-arch-clinical-notes-rag"


def test_save_then_unsave_roundtrip():
    agent = make_agent()
    out = agent.handle({"op": "save_asset", "asset_id": A_ID, "display_name": "Alex"})
    assert out["status"] == "ok"
    assert out["saved"] is True
    assert out["saved_count"] == 1

    # Reflected in get_asset user-state.
    got = agent.handle({"op": "get_asset", "asset_id": A_ID, "display_name": "Alex"})
    assert got["user"]["saved"] is True
    assert got["aggregates"]["saved_count"] == 1

    # Idempotent save doesn't double-count.
    again = agent.handle({"op": "save_asset", "asset_id": A_ID, "display_name": "Alex"})
    assert again["saved_count"] == 1

    # Unsave decrements.
    un = agent.handle(
        {"op": "save_asset", "asset_id": A_ID, "display_name": "Alex", "saved": False}
    )
    assert un["saved"] is False
    assert un["saved_count"] == 0


def test_rate_updates_average():
    agent = make_agent()
    a = agent.handle({"op": "rate_asset", "asset_id": A_ID, "display_name": "Alex", "rating": 4})
    assert a["status"] == "ok"
    assert a["average_rating"] == 4.0
    assert a["rating_count"] == 1

    # Same user re-rates: count stays 1, average follows the new value.
    b = agent.handle({"op": "rate_asset", "asset_id": A_ID, "display_name": "Alex", "rating": 2})
    assert b["rating_count"] == 1
    assert b["average_rating"] == 2.0

    # A second user adds to the average.
    c = agent.handle({"op": "rate_asset", "asset_id": A_ID, "display_name": "Sam", "rating": 4})
    assert c["rating_count"] == 2
    assert c["average_rating"] == 3.0


def test_rate_validates_range():
    agent = make_agent()
    assert agent.handle(
        {"op": "rate_asset", "asset_id": A_ID, "display_name": "Alex", "rating": 9}
    )["status"] == "error"
    assert agent.handle(
        {"op": "rate_asset", "asset_id": A_ID, "display_name": "Alex"}
    )["status"] == "error"


def test_flag_is_idempotent_per_user():
    agent = make_agent()
    first = agent.handle({"op": "flag_asset", "asset_id": A_ID, "display_name": "Alex"})
    assert first["flagged"] is True
    assert first["flag_count"] == 1
    second = agent.handle({"op": "flag_asset", "asset_id": A_ID, "display_name": "Alex"})
    assert second["flag_count"] == 1  # not double-counted
    # A different user increments.
    other = agent.handle({"op": "flag_asset", "asset_id": A_ID, "display_name": "Sam"})
    assert other["flag_count"] == 2


def test_write_ops_require_display_name():
    agent = make_agent()
    assert agent.handle({"op": "save_asset", "asset_id": A_ID})["status"] == "error"


def test_get_asset_without_user_has_aggregates_no_user_block():
    agent = make_agent()
    got = agent.handle({"op": "get_asset", "asset_id": A_ID})
    assert got["aggregates"]["rating_count"] == 0
    assert "user" not in got
