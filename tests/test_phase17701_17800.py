from pathlib import Path
import sys

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos_modules.phase17701_17800.portfolio_orchestrator import (
    AutonomousPortfolioOrchestrator,
    KnowledgeAsset,
    ResourcePool,
    VentureDemand,
)


def test_high_value_venture_receives_resources_first():
    orchestrator = AutonomousPortfolioOrchestrator(
        ROOT / "companyos_runtime" / "phase17701_17800_test"
    )
    resources = [
        ResourcePool("builder", "engineering", 5.0, 100.0, {"python"})
    ]
    demands = [
        VentureDemand("low", 0.3, 10000.0, 0.5, {"python"}, 5.0),
        VentureDemand("high", 0.9, 100000.0, 0.1, {"python"}, 5.0),
    ]
    result = orchestrator.allocate_shared_resources(resources, demands)
    assert result[0]["venture_id"] == "high"
    assert result[0]["granted_capacity"] == 5.0


def test_knowledge_routes_only_reusable_quality_assets():
    orchestrator = AutonomousPortfolioOrchestrator(
        ROOT / "companyos_runtime" / "phase17701_17800_test"
    )
    assets = [
        KnowledgeAsset("good", "a", "pricing", 0.9, True, {"subscription"}),
        KnowledgeAsset("bad", "a", "launch", 0.4, True, {"operations"}),
        KnowledgeAsset("private", "a", "sales", 0.9, False, {"crm"}),
    ]
    routes = orchestrator.route_knowledge(
        assets,
        {"b": {"pricing", "subscription", "launch", "sales"}},
    )
    assert len(routes) == 1
    assert routes[0]["asset_id"] == "good"
    assert routes[0]["copy_only"] is True


def test_command_center_preserves_action_gates():
    orchestrator = AutonomousPortfolioOrchestrator(
        ROOT / "companyos_runtime" / "phase17701_17800_test"
    )
    center = orchestrator.command_center([], [], [])
    assert center["external_actions_allowed"] is False
    assert center["financial_transfers_allowed"] is False
