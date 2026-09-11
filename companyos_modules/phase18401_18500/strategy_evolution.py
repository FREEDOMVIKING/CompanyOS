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
STATE_DIR = ROOT / "companyos_runtime" / "phase18401_18500"
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class StrategyCandidate:
    strategy_id: str
    venture_id: str
    objective: str
    expected_value: float
    confidence: float
    risk_score: float
    resource_cost: float
    time_horizon: int
    historical_score: float
    active: bool = True


@dataclass(slots=True)
class SimulationResult:
    strategy_id: str
    projected_value: float
    projected_risk: float
    projected_efficiency: float
    viability_score: float
    recommendation: str


class ExecutiveStrategyEvolution:
    """Evolves, simulates, ranks, retires, and roadmaps portfolio strategy."""

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

    @staticmethod
    def _base_score(item: StrategyCandidate) -> float:
        if not item.active:
            return -1.0
        value = max(0.0, item.expected_value)
        confidence = max(0.0, min(1.0, item.confidence))
        risk = max(0.0, min(1.0, item.risk_score))
        cost_penalty = min(1.0, max(0.0, item.resource_cost))
        historical = max(0.0, min(1.0, item.historical_score))
        horizon_penalty = min(1.0, max(1, item.time_horizon) / 12.0)

        return round(
            value * 0.30
            + confidence * 0.20
            + (1.0 - risk) * 0.20
            + historical * 0.15
            + (1.0 - cost_penalty) * 0.10
            + (1.0 - horizon_penalty) * 0.05,
            6,
        )

    def simulate(
        self,
        candidates: list[StrategyCandidate],
    ) -> list[SimulationResult]:
        results = []

        for item in candidates:
            projected_value = max(
                0.0,
                item.expected_value
                * (0.65 + item.confidence * 0.35)
                * (0.85 + item.historical_score * 0.15),
            )
            projected_risk = min(
                1.0,
                item.risk_score
                * (1.10 - item.confidence * 0.20),
            )
            projected_efficiency = (
                projected_value / item.resource_cost
                if item.resource_cost > 0
                else projected_value
            )
            viability = round(
                min(
                    1.0,
                    max(
                        0.0,
                        projected_value * 0.40
                        + (1.0 - projected_risk) * 0.25
                        + min(1.0, projected_efficiency) * 0.20
                        + item.historical_score * 0.15,
                    ),
                ),
                6,
            )

            if not item.active:
                recommendation = "retired"
            elif viability >= 0.72:
                recommendation = "advance"
            elif viability >= 0.48:
                recommendation = "refine_and_resimulate"
            else:
                recommendation = "retire"

            results.append(
                SimulationResult(
                    strategy_id=item.strategy_id,
                    projected_value=round(projected_value, 6),
                    projected_risk=round(projected_risk, 6),
                    projected_efficiency=round(projected_efficiency, 6),
                    viability_score=viability,
                    recommendation=recommendation,
                )
            )

        results.sort(key=lambda row: row.viability_score, reverse=True)
        self._write(
            self.state_dir / "strategy_simulation_results.json",
            [asdict(row) for row in results],
        )
        return results

    def evolve(
        self,
        candidates: list[StrategyCandidate],
        simulations: list[SimulationResult],
    ) -> list[dict[str, Any]]:
        sim_by_id = {row.strategy_id: row for row in simulations}
        evolved = []

        for item in candidates:
            sim = sim_by_id[item.strategy_id]

            if sim.recommendation == "advance":
                mutation = "preserve_core_and_expand"
                refined_risk = max(0.0, item.risk_score - 0.05)
                refined_value = min(1.0, item.expected_value + 0.05)
            elif sim.recommendation == "refine_and_resimulate":
                mutation = "reduce_scope_and_validation_cost"
                refined_risk = max(0.0, item.risk_score - 0.10)
                refined_value = item.expected_value
            else:
                mutation = "retire_strategy"
                refined_risk = item.risk_score
                refined_value = item.expected_value

            evolved.append(
                {
                    "strategy_id": item.strategy_id,
                    "venture_id": item.venture_id,
                    "mutation": mutation,
                    "refined_expected_value": round(refined_value, 6),
                    "refined_risk_score": round(refined_risk, 6),
                    "internal_planning_only": True,
                    "external_action_executed": False,
                    "financial_action_executed": False,
                }
            )

        self._write(self.state_dir / "evolved_strategies.json", evolved)
        return evolved

    def retire(
        self,
        candidates: list[StrategyCandidate],
        simulations: list[SimulationResult],
    ) -> dict[str, Any]:
        sim_by_id = {row.strategy_id: row for row in simulations}
        retired = []
        retained = []

        for item in candidates:
            recommendation = sim_by_id[item.strategy_id].recommendation
            if recommendation in {"retire", "retired"}:
                retired.append(item.strategy_id)
            else:
                retained.append(item.strategy_id)

        payload = {
            "generated_at": time.time(),
            "retired_strategy_ids": retired,
            "retained_strategy_ids": retained,
            "retirement_scope": "internal_strategy_registry_only",
            "external_action_executed": False,
            "financial_action_executed": False,
        }
        self._write(self.state_dir / "strategy_retirement.json", payload)
        return payload

    def roadmap(
        self,
        candidates: list[StrategyCandidate],
        simulations: list[SimulationResult],
        quarters: int = 4,
    ) -> dict[str, Any]:
        quarters = max(1, int(quarters))
        sim_by_id = {row.strategy_id: row for row in simulations}

        active = [
            item for item in candidates
            if sim_by_id[item.strategy_id].recommendation
            in {"advance", "refine_and_resimulate"}
        ]
        active.sort(
            key=lambda item: (
                sim_by_id[item.strategy_id].viability_score,
                self._base_score(item),
            ),
            reverse=True,
        )

        quarter_rows = {f"Q{index}": [] for index in range(1, quarters + 1)}
        for index, item in enumerate(active):
            quarter = f"Q{(index % quarters) + 1}"
            quarter_rows[quarter].append(
                {
                    "strategy_id": item.strategy_id,
                    "venture_id": item.venture_id,
                    "objective": item.objective,
                    "viability_score": sim_by_id[item.strategy_id].viability_score,
                    "milestone": (
                        "execute_internal_plan"
                        if sim_by_id[item.strategy_id].recommendation == "advance"
                        else "refine_and_validate"
                    ),
                }
            )

        payload = {
            "generated_at": time.time(),
            "quarters": quarter_rows,
            "external_actions_enabled": False,
            "financial_actions_enabled": False,
        }
        self._write(self.state_dir / "multi_quarter_roadmap.json", payload)
        return payload

    def resource_plan(
        self,
        candidates: list[StrategyCandidate],
        simulations: list[SimulationResult],
        total_capacity: float,
    ) -> dict[str, Any]:
        total_capacity = max(0.0, float(total_capacity))
        sim_by_id = {row.strategy_id: row for row in simulations}

        eligible = [
            item for item in candidates
            if sim_by_id[item.strategy_id].recommendation
            in {"advance", "refine_and_resimulate"}
        ]

        total_weight = sum(
            max(0.0, sim_by_id[item.strategy_id].viability_score)
            for item in eligible
        )

        allocations = []
        for item in eligible:
            weight = (
                sim_by_id[item.strategy_id].viability_score / total_weight
                if total_weight > 0
                else 0.0
            )
            allocations.append(
                {
                    "strategy_id": item.strategy_id,
                    "venture_id": item.venture_id,
                    "capacity_allocation": round(total_capacity * weight, 6),
                    "external_action_executed": False,
                    "financial_action_executed": False,
                }
            )

        payload = {
            "generated_at": time.time(),
            "total_capacity": total_capacity,
            "allocations": allocations,
            "external_actions_require_existing_gate": True,
            "financial_actions_require_existing_gate": True,
        }
        self._write(self.state_dir / "long_range_resource_plan.json", payload)
        return payload

    def opportunity_ranking(
        self,
        candidates: list[StrategyCandidate],
        simulations: list[SimulationResult],
    ) -> list[dict[str, Any]]:
        sim_by_id = {row.strategy_id: row for row in simulations}
        ranking = []

        for item in candidates:
            sim = sim_by_id[item.strategy_id]
            combined_score = round(
                self._base_score(item) * 0.45
                + sim.viability_score * 0.55,
                6,
            )
            ranking.append(
                {
                    "strategy_id": item.strategy_id,
                    "venture_id": item.venture_id,
                    "objective": item.objective,
                    "combined_score": combined_score,
                    "simulation_recommendation": sim.recommendation,
                }
            )

        ranking.sort(key=lambda row: row["combined_score"], reverse=True)
        self._write(self.state_dir / "opportunity_ranking.json", ranking)
        return ranking

    def executive_decision(
        self,
        ranking: list[dict[str, Any]],
        roadmap: dict[str, Any],
        retirement: dict[str, Any],
    ) -> dict[str, Any]:
        top = ranking[0] if ranking else None
        payload = {
            "generated_at": time.time(),
            "decision": "advance_strategy_portfolio" if top else "hold_and_reassess",
            "selected_strategy_id": top["strategy_id"] if top else None,
            "selected_venture_id": top["venture_id"] if top else None,
            "selected_score": top["combined_score"] if top else None,
            "retired_strategy_count": len(retirement["retired_strategy_ids"]),
            "roadmap_quarters": list(roadmap["quarters"].keys()),
            "internal_execution_only": True,
            "external_action_executed": False,
            "financial_action_executed": False,
        }
        self._write(self.state_dir / "executive_strategy_decision.json", payload)
        self._append(
            self.state_dir / "strategy_evolution_ledger.jsonl",
            {
                "event_id": self._id("strategy_decision", payload),
                "event": "executive_strategy_decision",
                **payload,
            },
        )
        return payload

    def demo(self) -> dict[str, Any]:
        candidates = [
            StrategyCandidate(
                "strategy_alpha",
                "venture_alpha",
                "expand validated analytics service",
                0.92,
                0.86,
                0.18,
                0.40,
                4,
                0.88,
            ),
            StrategyCandidate(
                "strategy_beta",
                "venture_beta",
                "improve operations automation",
                0.80,
                0.78,
                0.24,
                0.45,
                3,
                0.76,
            ),
            StrategyCandidate(
                "strategy_gamma",
                "venture_gamma",
                "enter unvalidated external market",
                0.88,
                0.48,
                0.62,
                0.78,
                8,
                0.32,
            ),
            StrategyCandidate(
                "strategy_delta",
                "venture_delta",
                "reuse proven internal workflow",
                0.74,
                0.90,
                0.12,
                0.25,
                2,
                0.91,
            ),
        ]

        simulations = self.simulate(candidates)
        evolved = self.evolve(candidates, simulations)
        retirement = self.retire(candidates, simulations)
        roadmap = self.roadmap(candidates, simulations, quarters=4)
        resources = self.resource_plan(
            candidates,
            simulations,
            total_capacity=100.0,
        )
        ranking = self.opportunity_ranking(candidates, simulations)
        decision = self.executive_decision(
            ranking,
            roadmap,
            retirement,
        )

        return {
            "ok": True,
            "simulations": [asdict(row) for row in simulations],
            "evolved_strategies": evolved,
            "retirement": retirement,
            "roadmap": roadmap,
            "resource_plan": resources,
            "opportunity_ranking": ranking,
            "executive_decision": decision,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["demo", "status"])
    args = parser.parse_args()

    engine = ExecutiveStrategyEvolution()
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
