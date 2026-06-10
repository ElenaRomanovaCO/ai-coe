from agents.lambdas.workers.worker_05_checklist_generator import ChecklistGeneratorWorker

from .conftest import FakeMetrics


def gen(regulations, context):
    w = ChecklistGeneratorWorker(metrics_client=FakeMetrics())
    return w.handle({"regulations": regulations, "engagement_context": context})


def test_reg_items_link_back_and_sort_by_priority():
    out = gen(
        [{"id": "reg-eu-ai-act", "name": "EU AI Act"}, {"id": "reg-hipaa-ai", "name": "HIPAA"}],
        {"industry": "healthcare", "data_types": ["phi"]},
    )
    assert out["status"] == "ok"
    checklist = out["checklist"]
    # Critical items lead.
    priorities = [c["priority"] for c in checklist]
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    assert priorities == sorted(priorities, key=lambda p: order[p])
    # HIPAA BAA item (critical) links to its regulation.
    baa = next(c for c in checklist if "Business Associate Agreement" in c["statement"])
    assert baa["priority"] == "critical"
    assert "reg-hipaa-ai" in baa["regulation_links"]
    # Sequential ids assigned.
    assert [c["id"] for c in checklist] == [f"chk-{i:02d}" for i in range(1, len(checklist) + 1)]


def test_phi_data_type_skipped_when_hipaa_present():
    out = gen([{"id": "reg-hipaa-ai", "name": "HIPAA"}], {"data_types": ["phi"]})
    statements = [c["statement"] for c in out["checklist"]]
    # The generic PHI item is suppressed (HIPAA items already cover PHI).
    assert not any("Treat health data as PHI" in s for s in statements)
    assert any("Business Associate Agreement" in s for s in statements)


def test_phi_data_type_added_when_no_hipaa():
    out = gen([], {"data_types": ["phi"]})
    statements = [c["statement"] for c in out["checklist"]]
    assert any("Treat health data as PHI" in s for s in statements)


def test_baseline_always_present_even_with_no_regs():
    out = gen([], {"data_types": []})
    statements = [c["statement"] for c in out["checklist"]]
    assert any("human oversight" in s for s in statements)
    assert any("Document the use case" in s for s in statements)


def test_deterministic_same_inputs():
    regs = [{"id": "reg-eu-ai-act", "name": "EU AI Act"}]
    ctx = {"data_types": ["pii"]}
    assert gen(regs, ctx)["checklist"] == gen(regs, ctx)["checklist"]
