import json

from agents.orchestrator.cache import ConfigCache
from agents.orchestrator.refresh import refresh_if_stale


def test_load_and_accessors():
    cache = ConfigCache(
        agents_md_loader=lambda: "rules v1",
        modules_loader=lambda: json.dumps({"version": 1, "modules": []}),
    )
    cache.load_or_raise()
    assert cache.agents_md == "rules v1"
    assert cache.registry.modules == []


def test_refresh_picks_up_edits():
    state = {"md": "v1"}
    cache = ConfigCache(
        agents_md_loader=lambda: state["md"],
        modules_loader=lambda: json.dumps({"version": 1, "modules": []}),
    )
    cache.load_or_raise()
    assert cache.agents_md == "v1"
    state["md"] = "v2"
    status = cache.refresh()
    assert status["agents_md"] == "ok"
    assert cache.agents_md == "v2"


def test_refresh_keeps_last_good_on_error():
    fail = {"on": False}

    def md_loader():
        if fail["on"]:
            raise RuntimeError("s3 down")
        return "good"

    cache = ConfigCache(
        agents_md_loader=md_loader,
        modules_loader=lambda: json.dumps({"version": 1, "modules": []}),
    )
    cache.load_or_raise()
    fail["on"] = True
    status = cache.refresh()
    assert status["agents_md"].startswith("error")
    assert cache.agents_md == "good"  # last good value retained


def test_is_stale_uses_wall_clock():
    cache = ConfigCache(
        agents_md_loader=lambda: "x",
        modules_loader=lambda: json.dumps({"version": 1, "modules": []}),
    )
    cache.load_or_raise()
    # Just loaded -> not stale; far future -> stale.
    assert cache.is_stale(60, now=cache._last_refresh + 10) is False
    assert cache.is_stale(60, now=cache._last_refresh + 61) is True


def test_refresh_if_stale_reloads_only_when_stale():
    state = {"md": "v1", "loads": 0}

    def md_loader():
        state["loads"] += 1
        return state["md"]

    cache = ConfigCache(
        agents_md_loader=md_loader,
        modules_loader=lambda: json.dumps({"version": 1, "modules": []}),
    )
    cache.load_or_raise()
    loads_after_init = state["loads"]

    # Fresh -> no reload.
    assert refresh_if_stale(cache, max_age=10_000) is False
    assert state["loads"] == loads_after_init

    # Force staleness by backdating the last refresh.
    cache._last_refresh -= 10_000
    state["md"] = "v2"
    assert refresh_if_stale(cache, max_age=60) is True
    assert cache.agents_md == "v2"


def test_refresh_keeps_last_good_registry_on_bad_json():
    bad = {"on": False}

    def modules_loader():
        return "{not valid json" if bad["on"] else json.dumps(
            {"version": 1, "modules": []}
        )

    cache = ConfigCache(agents_md_loader=lambda: "x", modules_loader=modules_loader)
    cache.load_or_raise()
    bad["on"] = True
    status = cache.refresh()
    assert status["modules_json"].startswith("error")
    assert cache.registry.modules == []
