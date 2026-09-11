from companyos.controlplane import DeadlockDetector, BudgetGovernor, RuntimeGuardrails

def test_deadlock():
    assert DeadlockDetector().detect([{"waiter":"a","holder":"b"},{"waiter":"b","holder":"a"}])["deadlocked"]

def test_budget():
    assert BudgetGovernor().evaluate({"amount":100},10000,12)["allowed"]

def test_guardrail():
    assert RuntimeGuardrails().evaluate({"kind":"production_deploy"})["requires_approval"]
