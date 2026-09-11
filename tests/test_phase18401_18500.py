from pathlib import Path
import sys

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos_modules.phase18401_18500.strategy_evolution import (
    ExecutiveStrategyEvolution,
    StrategyCandidate,
)


def engine():
    return ExecutiveStrategyEvolution(
        ROOT / "companyos_runtime" / "phase18401_18500_test"
    )


def candidates():
    return [
        StrategyCandidate(
            "a", "alpha", "validated expansion", 0.9, 0.9, 0.1, 0.3, 3, 0.9
        ),
        StrategyCandidate(
            "b", "beta", "high-risk expansion", 0.8, 0.4, 0.8, 0.9, 10, 0.2
        ),
    ]


def test_simulation_ranks_stronger_strategy_first():
    results = engine().simulate(candidates())
    assert results[0].strategy_id == "a"
    assert results[0].viability_score > results[1].viability_score


def test_retirement_detects_low_viability_strategy():
    e = engine()
    sims = e.simulate(candidates())
    result = e.retire(candidates(), sims)
    assert "b" in result["retired_strategy_ids"]
    assert result["external_action_executed"] is False
    assert result["financial_action_executed"] is False


def test_resource_plan_preserves_existing_gates():
    e = engine()
    sims = e.simulate(candidates())
    plan = e.resource_plan(candidates(), sims, total_capacity=100)
    assert plan["external_actions_require_existing_gate"] is True
    assert plan["financial_actions_require_existing_gate"] is True
    assert all(
        item["external_action_executed"] is False
        for item in plan["allocations"]
    )
    assert all(
        item["financial_action_executed"] is False
        for item in plan["allocations"]
    )


def test_roadmap_is_internal_only():
    e = engine()
    sims = e.simulate(candidates())
    result = e.roadmap(candidates(), sims)
    assert result["external_actions_enabled"] is False
    assert result["financial_actions_enabled"] is False
    assert set(result["quarters"]) == {"Q1", "Q2", "Q3", "Q4"}


def test_demo_returns_strategy_decision():
    result = engine().demo()
    assert result["ok"] is True
    assert result["executive_decision"]["internal_execution_only"] is True
    assert result["executive_decision"]["external_action_executed"] is False
    assert result["executive_decision"]["financial_action_executed"] is False
