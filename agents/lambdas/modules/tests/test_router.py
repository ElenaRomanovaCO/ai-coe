from agents.lambdas.modules import router
from agents.lambdas.modules.base import ModuleAgent


def test_unknown_agent_returns_not_implemented():
    out = router.route({"agent_id": "AGENT-99", "args": {}})
    assert out["status"] == "not_implemented"
    assert out["agent_id"] == "AGENT-99"


def test_missing_agent_id_is_not_implemented():
    out = router.route({"args": {"op": "list_assets"}})
    assert out["status"] == "not_implemented"


def test_non_dict_args_is_error():
    out = router.route({"agent_id": "AGENT-03", "args": ["not", "a", "dict"]})
    assert out["status"] == "error"


def test_registry_dispatches_to_agent(monkeypatch):
    calls = {}

    class Stub(ModuleAgent):
        agent_id = "AGENT-TEST"

        def handle(self, args):
            calls["args"] = args
            return {"status": "ok", "echo": args}

    monkeypatch.setitem(router.REGISTRY, "AGENT-TEST", Stub)
    out = router.route({"agent_id": "AGENT-TEST", "args": {"op": "x"}})
    assert out == {"status": "ok", "echo": {"op": "x"}}
    assert calls["args"] == {"op": "x"}


def test_agent_exception_becomes_error(monkeypatch):
    class Boom(ModuleAgent):
        def handle(self, args):
            raise RuntimeError("kaboom")

    monkeypatch.setitem(router.REGISTRY, "AGENT-BOOM", Boom)
    out = router.route({"agent_id": "AGENT-BOOM", "args": {}})
    assert out["status"] == "error"
    assert "failed" in out["message"]


def test_agent_03_registered():
    assert "AGENT-03" in router.REGISTRY
