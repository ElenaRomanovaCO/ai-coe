from agents.lambdas.workers.dimensions import DIMENSIONS
from agents.lambdas.workers.worker_01_question_picker import QuestionPickerWorker

from .conftest import FakeMetrics, qa

STRONG = "production systems, formal governance, committed budget, prioritized roadmap"
WEAK = "None really, no tooling, manual processes, not sure, ad hoc."


def pick(history):
    return QuestionPickerWorker(metrics_client=FakeMetrics()).handle({"history": history})


def test_phase1_covers_each_dimension_in_order():
    history = []
    asked = []
    for _ in range(len(DIMENSIONS)):
        out = pick(history)
        assert out["is_final"] is False
        asked.append(out["dimension"])
        history.append(qa(out["dimension"], STRONG, out["question_text"]))
    assert asked == DIMENSIONS  # primaries asked once each, in order


def test_strong_answers_stop_at_minimum_8():
    # All-strong answers -> no weak dimensions -> target == MIN (8).
    history = []
    count = 0
    while True:
        out = pick(history)
        if out["is_final"]:
            break
        history.append(qa(out["dimension"], STRONG, out["question_text"]))
        count += 1
        assert count <= 12
    assert len(history) == 8


def test_weak_answers_extend_toward_12():
    # All-weak answers -> 6 weak dims -> target clamps to 12.
    history = []
    while True:
        out = pick(history)
        if out["is_final"]:
            break
        history.append(qa(out["dimension"], WEAK, out["question_text"]))
    assert len(history) == 12
    # Every dimension covered at least once.
    assert {h["dimension"] for h in history} == set(DIMENSIONS)


def test_deterministic_same_history_same_question():
    history = [qa(DIMENSIONS[0], STRONG)]
    assert pick(history) == pick(history)
