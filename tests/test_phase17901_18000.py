from pathlib import Path
import sys

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos_modules.phase17901_18000.enterprise_orchestrator import (
    EnterpriseOrchestrator,
    VentureWorkload,
)


def orchestrator():
    return EnterpriseOrchestrator(
        ROOT / "companyos_runtime" / "phase17901_18000_test"
    )


def workloads():
    return [
        VentureWorkload("alpha", 95, 0.80, 0.20, 90, 3, 1.5),
        VentureWorkload("beta", 80, 0.65, 0.30, 70, 2, 1.0),
        VentureWorkload("gamma", 75, 0.60, 0.35, 45, 2, 1.2),
        VentureWorkload("blocked", 99, 0.95, 0.10, 95, 2, 1.0, blocked=True),
    ]


def test_allocator_respects_capacity():
    o = orchestrator()
    decisions = o.allocate(workloads(), worker_capacity=5, compute_capacity=2.5)
    assert sum(item.workers_allocated for item in decisions) <= 5
    assert sum(item.compute_allocated for item in decisions) <= 2.5


def test_blocked_venture_is_never_allocated():
    o = orchestrator()
    decisions = o.allocate(workloads(), worker_capacity=10, compute_capacity=10)
    blocked = next(item for item in decisions if item.venture_id == "blocked")
    assert blocked.workers_allocated == 0
    assert blocked.compute_allocated == 0
    assert blocked.action == "hold"


def test_recovery_never_executes_external_or_financial_actions():
    o = orchestrator()
    items = workloads()
    decisions = o.allocate(items, worker_capacity=3, compute_capacity=1.5)
    bottlenecks = o.detect_bottlenecks(items, decisions)
    recovery = o.self_heal(bottlenecks)
    assert recovery["external_actions_require_existing_gate"] is True
    assert recovery["financial_actions_require_existing_gate"] is True
    assert all(not item["external_action_executed"] for item in recovery["actions"])
    assert all(not item["financial_action_executed"] for item in recovery["actions"])


def test_demo_returns_executive_decision():
    result = orchestrator().demo()
    assert result["ok"] is True
    assert result["executive_decision"]["decision"] in {
        "advance_portfolio_work",
        "hold_and_recover",
    }
