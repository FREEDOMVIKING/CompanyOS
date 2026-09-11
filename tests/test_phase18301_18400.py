from pathlib import Path
import sys

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos_modules.phase18301_18400.enterprise_learning_engine import (
    EnterpriseLearningEngine,
    StrategyOutcome,
    VentureKnowledge,
)


def engine():
    return EnterpriseLearningEngine(
        ROOT / "companyos_runtime" / "phase18301_18400_test"
    )


def outcomes():
    return [
        StrategyOutcome(
            "a",
            "alpha",
            "validate",
            True,
            0.9,
            0.3,
            2,
            0.1,
            ["validate demand first", "reuse proven workflows"],
        ),
        StrategyOutcome(
            "b",
            "beta",
            "scale",
            False,
            0.2,
            0.8,
            8,
            0.7,
            ["validate demand first", "avoid premature scaling"],
        ),
    ]


def test_strategy_scoring_orders_successful_strategy_first():
    scores = engine().strategy_scoring(outcomes())
    assert scores[0]["strategy_id"] == "a"
    assert scores[0]["score"] > scores[1]["score"]


def test_pattern_recognition_detects_failure_pattern():
    result = engine().pattern_recognition(outcomes())
    failure = next(
        row for row in result if row["pattern"] == "avoid premature scaling"
    )
    assert failure["classification"] == "failure_pattern"


def test_knowledge_graph_contains_edges():
    graph = engine().knowledge_graph(
        [
            VentureKnowledge(
                "alpha",
                "analytics",
                ["python"],
                ["validation"],
                ["scaling"],
                ["validate first"],
            )
        ]
    )
    assert graph["nodes"]
    assert graph["edges"]


def test_recommendations_preserve_external_and_financial_gates():
    e = engine()
    scores = e.strategy_scoring(outcomes())
    patterns = e.pattern_recognition(outcomes())
    recommendations = e.optimization_recommendations(scores, patterns)
    assert recommendations
    state = (
        ROOT
        / "companyos_runtime"
        / "phase18301_18400_test"
        / "optimization_recommendations.json"
    )
    data = __import__("json").loads(state.read_text())
    assert data["external_actions_require_existing_gate"] is True
    assert data["financial_actions_require_existing_gate"] is True
    assert all(
        item["external_action_executed"] is False
        for item in recommendations
    )
    assert all(
        item["financial_action_executed"] is False
        for item in recommendations
    )


def test_demo_returns_forecast_and_planning_improvements():
    result = engine().demo()
    assert result["ok"] is True
    assert "forecast" in result
    assert "planning_improvements" in result
    assert (
        result["planning_improvements"]["self_improvement_scope"]
        == "internal_planning_only"
    )
