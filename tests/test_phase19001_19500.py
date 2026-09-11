from pathlib import Path
import sys

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos_modules.phase19001_19500.production_supervisor import (
    ProductionSupervisor,
    RuntimeSignal,
)


def supervisor(name: str) -> ProductionSupervisor:
    return ProductionSupervisor(
        ROOT / "companyos_runtime" / "phase19001_19500_test" / name
    )


def test_healthy_component_continues():
    s = supervisor("healthy")
    decisions = s.evaluate([
        RuntimeSignal("worker", True, 100, 0.01, 2, 10, 0)
    ])
    assert decisions[0].action == "continue"


def test_unhealthy_component_gets_internal_restart():
    s = supervisor("restart")
    decisions = s.evaluate([
        RuntimeSignal("worker", False, 800, 0.10, 5, 60, 1)
    ])
    assert decisions[0].action == "restart_internal_component"
    assert decisions[0].autonomous_internal_action is True


def test_critical_failure_enters_safe_mode():
    s = supervisor("critical")
    decisions = s.evaluate([
        RuntimeSignal("kernel", False, 1000, 0.2, 20, 600, 0, True)
    ])
    assert decisions[0].action == "enter_safe_internal_mode"


def test_recovery_plan_preserves_all_gates():
    s = supervisor("gates")
    decisions = s.evaluate([
        RuntimeSignal("worker", False, 800, 0.10, 5, 60, 1)
    ])
    plan = s.recovery_plan(decisions)
    assert plan["external_actions_require_existing_gate"] is True
    assert plan["financial_actions_require_existing_gate"] is True
    assert plan["irreversible_actions_require_existing_gate"] is True


def test_demo_returns_dashboard():
    result = supervisor("demo").demo()
    assert result["ok"] is True
    assert result["dashboard"]["status"] == "production_supervisor_online"
    assert result["dashboard"]["external_actions_enabled"] is False
    assert result["dashboard"]["financial_actions_enabled"] is False
    assert result["dashboard"]["irreversible_actions_enabled"] is False
