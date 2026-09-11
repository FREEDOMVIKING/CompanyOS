from companyos_phase433_448 import PriorityEngine, FailurePolicy, LifecycleManager

def test_priority_penalizes_failures():
    a = {"priority":0.8,"failures":0,"metrics":{"validation_score":8}}
    b = {"priority":0.8,"failures":3,"metrics":{"validation_score":8}}
    assert PriorityEngine().score(a) > PriorityEngine().score(b)

def test_failure_policy():
    assert FailurePolicy().decide(0,0)["action"] == "retry"
    assert FailurePolicy().decide(3,0)["action"] == "pause"

def test_lifecycle():
    assert LifecycleManager().transition("queued","building")["success"] is True
    assert LifecycleManager().transition("queued","scaling")["success"] is False
