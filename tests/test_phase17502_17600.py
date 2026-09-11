from pathlib import Path
import sys

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos_modules.phase17502_17600.executive_bundle import (
    AutonomousExecutiveBundle,
    Opportunity,
    Specialist,
    WorkItem,
)


def test_opportunity_scoring():
    item = Opportunity("x", "test", 100000, 10000, 0.8, 0.2, 0.9, 0.2)
    assert item.score() > 40


def test_delegation_respects_dependencies():
    bundle = AutonomousExecutiveBundle(
        ROOT / "companyos_runtime" / "phase17502_17600_test"
    )
    specialists = [
        Specialist("research", "research", {"research"}),
        Specialist("builder", "builder", {"python"}),
    ]
    work = [
        WorkItem("a", "research", {"research"}, 100),
        WorkItem("b", "build", {"python"}, 90, ["a"]),
    ]
    result = bundle.assign_work(work, specialists)
    assert [item.work_id for item in result] == ["a", "b"]
    assert all(item.status == "assigned" for item in result)


def test_external_actions_remain_gated():
    bundle = AutonomousExecutiveBundle(
        ROOT / "companyos_runtime" / "phase17502_17600_test"
    )
    opportunity = Opportunity("x", "test", 100000, 10000, 0.8, 0.2, 0.9, 0.2)
    decision = bundle.evaluate_opportunity(opportunity)
    packet = bundle.build_execution_packet(opportunity, decision, [])
    assert packet["external_actions_allowed"] is False
    assert packet["financial_actions_allowed"] is False
    assert packet["requires_existing_approval_gates"] is True
