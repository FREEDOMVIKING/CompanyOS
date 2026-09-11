#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
STATE_DIR = ROOT / "companyos_runtime" / "phase18301_18400"
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class StrategyOutcome:
    strategy_id: str
    venture_id: str
    objective: str
    success: bool
    value_created: float
    execution_cost: float
    duration_units: int
    risk_realized: float
    lessons: list[str]


@dataclass(slots=True)
class VentureKnowledge:
    venture_id: str
    domain: str
    capabilities: list[str]
    recurring_patterns: list[str]
    known_risks: list[str]
    proven_strategies: list[str]


class EnterpriseLearningEngine:
    """Cross-venture learning, pattern discovery, forecasting, and planning improvement."""

    def __init__(self, state_dir: Path = STATE_DIR) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write(path: Path, payload: Any) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    @staticmethod
    def _append(path: Path, payload: Any) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    @staticmethod
    def _id(prefix: str, payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:12]}"

    def strategy_scoring(
        self,
        outcomes: list[StrategyOutcome],
    ) -> list[dict[str, Any]]:
        scored = []
        for item in outcomes:
            efficiency = (
                item.value_created / item.execution_cost
                if item.execution_cost > 0
                else item.value_created
            )
            speed = 1.0 / max(1, item.duration_units)
            risk_penalty = max(0.0, min(1.0, item.risk_realized))
            score = round(
                (1.0 if item.success else 0.0) * 0.35
                + min(1.0, max(0.0, efficiency)) * 0.30
                + min(1.0, speed * 5.0) * 0.15
                + (1.0 - risk_penalty) * 0.20,
                6,
            )
            scored.append(
                {
                    "strategy_id": item.strategy_id,
                    "venture_id": item.venture_id,
                    "objective": item.objective,
                    "success": item.success,
                    "score": score,
                    "efficiency": round(efficiency, 6),
                    "lessons": item.lessons,
                }
            )

        scored.sort(key=lambda row: row["score"], reverse=True)
        payload = {
            "generated_at": time.time(),
            "strategies": scored,
        }
        self._write(self.state_dir / "strategy_success_scores.json", payload)
        return scored

    def pattern_recognition(
        self,
        outcomes: list[StrategyOutcome],
    ) -> list[dict[str, Any]]:
        lesson_counts: dict[str, int] = {}
        success_counts: dict[str, int] = {}

        for outcome in outcomes:
            for lesson in outcome.lessons:
                lesson_counts[lesson] = lesson_counts.get(lesson, 0) + 1
                if outcome.success:
                    success_counts[lesson] = success_counts.get(lesson, 0) + 1

        patterns = []
        for lesson, count in lesson_counts.items():
            success_count = success_counts.get(lesson, 0)
            success_rate = success_count / count
            patterns.append(
                {
                    "pattern": lesson,
                    "occurrences": count,
                    "success_rate": round(success_rate, 6),
                    "classification": (
                        "repeatable_advantage"
                        if success_rate >= 0.75
                        else "mixed_signal"
                        if success_rate >= 0.40
                        else "failure_pattern"
                    ),
                }
            )

        patterns.sort(
            key=lambda row: (row["occurrences"], row["success_rate"]),
            reverse=True,
        )
        self._write(self.state_dir / "cross_venture_patterns.json", patterns)
        return patterns

    def knowledge_graph(
        self,
        ventures: list[VentureKnowledge],
    ) -> dict[str, Any]:
        nodes = []
        edges = []

        for venture in ventures:
            nodes.append(
                {
                    "id": venture.venture_id,
                    "type": "venture",
                    "domain": venture.domain,
                }
            )

            for capability in venture.capabilities:
                capability_id = f"capability:{capability}"
                nodes.append(
                    {
                        "id": capability_id,
                        "type": "capability",
                    }
                )
                edges.append(
                    {
                        "from": venture.venture_id,
                        "to": capability_id,
                        "relation": "has_capability",
                    }
                )

            for strategy in venture.proven_strategies:
                strategy_id = f"strategy:{strategy}"
                nodes.append(
                    {
                        "id": strategy_id,
                        "type": "strategy",
                    }
                )
                edges.append(
                    {
                        "from": venture.venture_id,
                        "to": strategy_id,
                        "relation": "proved_strategy",
                    }
                )

            for risk in venture.known_risks:
                risk_id = f"risk:{risk}"
                nodes.append(
                    {
                        "id": risk_id,
                        "type": "risk",
                    }
                )
                edges.append(
                    {
                        "from": venture.venture_id,
                        "to": risk_id,
                        "relation": "exposed_to",
                    }
                )

        deduped_nodes = {
            node["id"]: node
            for node in nodes
        }
        payload = {
            "generated_at": time.time(),
            "nodes": list(deduped_nodes.values()),
            "edges": edges,
        }
        self._write(self.state_dir / "enterprise_knowledge_graph.json", payload)
        return payload

    def executive_memory(
        self,
        outcomes: list[StrategyOutcome],
        patterns: list[dict[str, Any]],
    ) -> dict[str, Any]:
        timeline = [
            {
                "event_id": self._id("memory", asdict(outcome)),
                "event_type": "strategy_outcome",
                "created_at": time.time(),
                "strategy_id": outcome.strategy_id,
                "venture_id": outcome.venture_id,
                "success": outcome.success,
                "value_created": outcome.value_created,
                "lessons": outcome.lessons,
            }
            for outcome in outcomes
        ]

        payload = {
            "generated_at": time.time(),
            "timeline": timeline,
            "learned_pattern_count": len(patterns),
        }
        self._write(self.state_dir / "executive_long_term_memory.json", payload)
        return payload

    def optimization_recommendations(
        self,
        strategy_scores: list[dict[str, Any]],
        patterns: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        recommendations = []

        for row in patterns:
            if row["classification"] == "repeatable_advantage":
                action = "standardize_and_reuse"
            elif row["classification"] == "failure_pattern":
                action = "avoid_or_require_additional_validation"
            else:
                action = "run_controlled_internal_experiment"

            recommendations.append(
                {
                    "source": "pattern",
                    "subject": row["pattern"],
                    "action": action,
                    "external_action_executed": False,
                    "financial_action_executed": False,
                }
            )

        if strategy_scores:
            top = strategy_scores[0]
            recommendations.append(
                {
                    "source": "strategy_score",
                    "subject": top["strategy_id"],
                    "action": "reuse_highest_scoring_strategy_where_applicable",
                    "external_action_executed": False,
                    "financial_action_executed": False,
                }
            )

        payload = {
            "generated_at": time.time(),
            "recommendations": recommendations,
            "external_actions_require_existing_gate": True,
            "financial_actions_require_existing_gate": True,
        }
        self._write(
            self.state_dir / "optimization_recommendations.json",
            payload,
        )
        return recommendations

    def forecast(
        self,
        outcomes: list[StrategyOutcome],
        strategy_scores: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if outcomes:
            success_rate = sum(1 for item in outcomes if item.success) / len(outcomes)
            average_value = statistics.fmean(
                item.value_created for item in outcomes
            )
            average_risk = statistics.fmean(
                item.risk_realized for item in outcomes
            )
        else:
            success_rate = 0.0
            average_value = 0.0
            average_risk = 0.0

        score_signal = (
            statistics.fmean(row["score"] for row in strategy_scores)
            if strategy_scores
            else 0.0
        )

        confidence = round(
            min(
                1.0,
                max(
                    0.0,
                    success_rate * 0.45
                    + score_signal * 0.35
                    + (1.0 - average_risk) * 0.20,
                ),
            ),
            6,
        )

        payload = {
            "generated_at": time.time(),
            "historical_success_rate": round(success_rate, 6),
            "average_value_created": round(average_value, 6),
            "average_risk_realized": round(average_risk, 6),
            "forecast_confidence": confidence,
            "forecast": (
                "positive"
                if confidence >= 0.70
                else "cautiously_positive"
                if confidence >= 0.45
                else "uncertain"
            ),
        }
        self._write(self.state_dir / "executive_forecast.json", payload)
        return payload

    def planning_improvements(
        self,
        recommendations: list[dict[str, Any]],
        forecast: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "generated_at": time.time(),
            "planning_changes": [
                {
                    "change_id": self._id("plan_change", item),
                    "source": item["source"],
                    "subject": item["subject"],
                    "recommended_action": item["action"],
                    "applied_to_internal_planning_only": True,
                }
                for item in recommendations
            ],
            "forecast": forecast,
            "self_improvement_scope": "internal_planning_only",
            "external_action_executed": False,
            "financial_action_executed": False,
        }
        self._write(self.state_dir / "planning_improvements.json", payload)
        return payload

    def demo(self) -> dict[str, Any]:
        outcomes = [
            StrategyOutcome(
                "strategy_alpha",
                "venture_alpha",
                "validate customer demand",
                True,
                0.90,
                0.35,
                3,
                0.12,
                [
                    "validate demand before building",
                    "small internal experiments reduce risk",
                ],
            ),
            StrategyOutcome(
                "strategy_beta",
                "venture_beta",
                "launch shared analytics workflow",
                True,
                0.82,
                0.40,
                5,
                0.20,
                [
                    "shared capabilities improve portfolio efficiency",
                    "small internal experiments reduce risk",
                ],
            ),
            StrategyOutcome(
                "strategy_gamma",
                "venture_gamma",
                "expand before validation",
                False,
                0.20,
                0.75,
                8,
                0.65,
                [
                    "validate demand before building",
                    "premature scaling increases failure risk",
                ],
            ),
            StrategyOutcome(
                "strategy_delta",
                "venture_delta",
                "reuse proven internal workflow",
                True,
                0.76,
                0.28,
                2,
                0.10,
                [
                    "shared capabilities improve portfolio efficiency",
                    "reuse proven workflows",
                ],
            ),
        ]

        ventures = [
            VentureKnowledge(
                "venture_alpha",
                "analytics",
                ["python", "research", "testing"],
                ["customer validation"],
                ["premature scaling"],
                ["validate demand first"],
            ),
            VentureKnowledge(
                "venture_beta",
                "operations",
                ["python", "analytics", "automation"],
                ["shared services"],
                ["resource contention"],
                ["reuse shared capabilities"],
            ),
            VentureKnowledge(
                "venture_gamma",
                "software",
                ["python", "frontend"],
                ["rapid prototyping"],
                ["premature scaling"],
                ["small internal experiments"],
            ),
        ]

        scores = self.strategy_scoring(outcomes)
        patterns = self.pattern_recognition(outcomes)
        graph = self.knowledge_graph(ventures)
        memory = self.executive_memory(outcomes, patterns)
        recommendations = self.optimization_recommendations(
            scores,
            patterns,
        )
        forecast = self.forecast(outcomes, scores)
        planning = self.planning_improvements(
            recommendations,
            forecast,
        )

        return {
            "ok": True,
            "strategy_scores": scores,
            "patterns": patterns,
            "knowledge_graph": graph,
            "memory": memory,
            "recommendations": recommendations,
            "forecast": forecast,
            "planning_improvements": planning,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["demo", "status"])
    args = parser.parse_args()

    engine = EnterpriseLearningEngine()
    result = (
        engine.demo()
        if args.action == "demo"
        else {
            "ok": True,
            "state_files": sorted(
                path.name for path in engine.state_dir.glob("*")
            ),
        }
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
