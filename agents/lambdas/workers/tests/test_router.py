from agents.lambdas.workers import router

from .conftest import qa


def test_unknown_worker_not_implemented():
    out = router.route({"worker_id": "WORKER-99", "args": {}})
    assert out["status"] == "not_implemented"


def test_non_dict_args_error():
    out = router.route({"worker_id": "WORKER-01", "args": "nope"})
    assert out["status"] == "error"


def test_all_three_registered():
    assert set(router.REGISTRY) == {"WORKER-01", "WORKER-02", "WORKER-03"}


def test_route_worker_01():
    out = router.route({"worker_id": "WORKER-01", "args": {"history": []}})
    assert out["status"] == "ok"
    assert out["is_final"] is False
    assert out["dimension"]


def test_route_worker_02():
    history = [qa(d, "production formal budget") for d in
               ["data_readiness", "org_culture", "ai_tooling", "use_case_clarity",
                "governance", "budget_sponsorship"]]
    out = router.route({"worker_id": "WORKER-02", "args": {"history": history}})
    assert out["status"] == "ok"
    assert 0 <= out["stage"] <= 5
