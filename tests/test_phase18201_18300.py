from pathlib import Path
import sys

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos_modules.phase18201_18300.executive_mission_control import (
    ExecutiveMissionControl,
    OpportunityRecord,
    VentureSnapshot,
)


def control():
    return ExecutiveMissionControl(
        ROOT / "companyos_runtime" / "phase18201_18300_test"
    )


def ventures():
    return [
        VentureSnapshot(
            "alpha", 0.9, 0.8, 0.8, 90, 3, 2, 0, 0.2
        ),
        VentureSnapshot(
            "beta", 0.7, 0.6, 0.4, 60, 12, 0, 2, 0.3
        ),
        VentureSnapshot(
            "blocked", 0.8, 0.7, 0.2, 30, 10, 1, 0, 0.5, True
        ),
    ]


def test_kpi_aggregation():
    result = control().aggregate_kpis(ventures())
    assert result["venture_count"] == 3
    assert result["total_backlog"] == 25
    assert result["blocked_venture_count"] == 1


def test_resource_exchange_never_executes_actions():
    result = control().resource_exchange(ventures())
    assert result["external_actions_require_existing_gate"] is True
    assert result["financial_actions_require_existing_gate"] is True
    assert all(
        transfer["external_action_executed"] is False
        for transfer in result["transfers"]
    )
    assert all(
        transfer["financial_action_executed"] is False
        for transfer in result["transfers"]
    )


def test_opportunity_queue_prioritizes_capability_match():
    opportunities = [
        OpportunityRecord(
            "a", "Matched", 0.8, 0.8, 0.8, ["python"], ["alpha"]
        ),
        OpportunityRecord(
            "b", "Missing", 0.8, 0.8, 0.8, ["integration"], ["beta"]
        ),
    ]
    queue = control().opportunity_queue(opportunities, {"python"})
    assert queue[0]["opportunity_id"] == "a"
    assert queue[0]["capability_match"] is True


def test_event_bus_preserves_gates():
    event = control().publish_event("test", "pytest", {"ok": True})
    assert event["external_action_executed"] is False
    assert event["financial_action_executed"] is False


def test_demo_returns_mission_control_dashboard():
    result = control().demo()
    assert result["ok"] is True
    assert result["dashboard"]["status"] == "mission_control_online"
    assert result["dashboard"]["external_actions_enabled"] is False
    assert result["dashboard"]["financial_actions_enabled"] is False
