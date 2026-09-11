#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path.home() / "companyos"
STATE_DIR = ROOT / "companyos_runtime" / "phase17601_17700"
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class VentureState:
    venture_id: str
    name: str
    monthly_revenue: float
    monthly_cost: float
    growth_rate: float
    confidence: float
    strategic_fit: float
    risk: float
    execution_health: float

    def margin(self) -> float:
        return self.monthly_revenue - self.monthly_cost

    def health_score(self) -> float:
        margin_component = max(min(self.margin() / 10000.0, 3.0), -3.0) * 8.0
        score = (
            45.0
            + margin_component
            + self.growth_rate * 20.0
            + self.confidence * 15.0
            + self.strategic_fit * 10.0
            + self.execution_health * 15.0
            - self.risk * 25.0
        )
        return round(max(0.0, min(score, 100.0)), 4)


@dataclass(slots=True)
class CapitalPlan:
    venture_id: str
    recommended_budget: float
    reserve_budget: float
    action: str
    rationale: list[str]


@dataclass(slots=True)
class PortfolioDecision:
    decision_id: str
    venture_id: str
    action: str
    priority_score: float
    rationale: list[str]
    created_at: float


class AutonomousPortfolioDirector:
    """Cross-venture prioritization and guarded capital-allocation engine."""

    def __init__(self, state_dir: Path = STATE_DIR) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _stable_id(prefix: str, payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:12]}"

    def rank_ventures(self, ventures: Iterable[VentureState]) -> list[dict[str, Any]]:
        rows = []
        for venture in ventures:
            rows.append(
                {
                    "venture": asdict(venture),
                    "health_score": venture.health_score(),
                    "margin": venture.margin(),
                }
            )
        rows.sort(
            key=lambda row: (
                row["health_score"],
                row["margin"],
                row["venture"]["growth_rate"],
            ),
            reverse=True,
        )
        self._write_json(self.state_dir / "latest_portfolio_ranking.json", rows)
        return rows

    def decide(self, venture: VentureState) -> PortfolioDecision:
        score = venture.health_score()
        rationale: list[str] = []

        if venture.margin() > 0:
            rationale.append("positive_operating_margin")
        else:
            rationale.append("negative_operating_margin")

        if venture.growth_rate >= 0.15:
            rationale.append("strong_growth")
        elif venture.growth_rate >= 0:
            rationale.append("non_negative_growth")
        else:
            rationale.append("contracting_revenue")

        if venture.risk <= 0.35:
            rationale.append("risk_within_scaling_band")
        else:
            rationale.append("elevated_risk")

        if venture.execution_health >= 0.7:
            rationale.append("execution_health_sufficient")
        else:
            rationale.append("execution_health_requires_repair")

        if score >= 75 and venture.risk <= 0.35:
            action = "scale"
        elif score >= 55:
            action = "continue"
        elif score >= 35:
            action = "repair"
        else:
            action = "pause"

        decision = PortfolioDecision(
            decision_id=self._stable_id("portfolio", asdict(venture)),
            venture_id=venture.venture_id,
            action=action,
            priority_score=score,
            rationale=rationale,
            created_at=time.time(),
        )
        self._append_jsonl(self.state_dir / "portfolio_decisions.jsonl", asdict(decision))
        return decision

    def allocate_capital(
        self,
        ventures: Iterable[VentureState],
        available_budget: float,
        reserve_ratio: float = 0.20,
    ) -> list[CapitalPlan]:
        ventures = list(ventures)
        available_budget = max(float(available_budget), 0.0)
        reserve_ratio = max(0.0, min(float(reserve_ratio), 0.8))

        reserve_total = round(available_budget * reserve_ratio, 2)
        allocatable = round(available_budget - reserve_total, 2)

        weights: dict[str, float] = {}
        for venture in ventures:
            score = venture.health_score()
            decision = self.decide(venture)
            multiplier = {
                "scale": 1.0,
                "continue": 0.65,
                "repair": 0.30,
                "pause": 0.0,
            }[decision.action]
            weights[venture.venture_id] = max(score * multiplier, 0.0)

        weight_total = sum(weights.values())
        plans: list[CapitalPlan] = []

        for venture in ventures:
            decision = self.decide(venture)
            weight = weights[venture.venture_id]
            share = (weight / weight_total) if weight_total > 0 else 0.0
            recommended = round(allocatable * share, 2)
            reserve = round(reserve_total / max(len(ventures), 1), 2)

            rationale = [
                f"portfolio_health_score={venture.health_score()}",
                f"allocation_weight={round(weight, 4)}",
                f"reserve_ratio={reserve_ratio}",
                "recommendation_only_no_fund_transfer",
            ]

            plans.append(
                CapitalPlan(
                    venture_id=venture.venture_id,
                    recommended_budget=recommended,
                    reserve_budget=reserve,
                    action=decision.action,
                    rationale=rationale,
                )
            )

        payload = {
            "created_at": time.time(),
            "available_budget": available_budget,
            "reserve_total": reserve_total,
            "allocatable_budget": allocatable,
            "plans": [asdict(plan) for plan in plans],
            "funds_transferred": False,
            "requires_existing_financial_approval_gates": True,
        }
        self._write_json(self.state_dir / "latest_capital_plan.json", payload)
        return plans

    def executive_dashboard(self, ventures: Iterable[VentureState]) -> dict[str, Any]:
        ventures = list(ventures)
        ranking = self.rank_ventures(ventures)
        decisions = [asdict(self.decide(venture)) for venture in ventures]

        dashboard = {
            "generated_at": time.time(),
            "venture_count": len(ventures),
            "total_monthly_revenue": round(sum(v.monthly_revenue for v in ventures), 2),
            "total_monthly_cost": round(sum(v.monthly_cost for v in ventures), 2),
            "total_monthly_margin": round(sum(v.margin() for v in ventures), 2),
            "average_health_score": round(
                sum(v.health_score() for v in ventures) / max(len(ventures), 1),
                4,
            ),
            "ranking": ranking,
            "decisions": decisions,
        }
        self._write_json(self.state_dir / "latest_executive_dashboard.json", dashboard)
        return dashboard

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    @staticmethod
    def _append_jsonl(path: Path, payload: Any) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def demo() -> dict[str, Any]:
    director = AutonomousPortfolioDirector()

    ventures = [
        VentureState(
            "venture_alpha",
            "Recurring analytics service",
            48000.0,
            17000.0,
            0.24,
            0.84,
            0.92,
            0.22,
            0.88,
        ),
        VentureState(
            "venture_beta",
            "Operations automation product",
            22000.0,
            15000.0,
            0.11,
            0.72,
            0.80,
            0.33,
            0.74,
        ),
        VentureState(
            "venture_gamma",
            "Experimental marketplace",
            6000.0,
            14000.0,
            -0.05,
            0.48,
            0.60,
            0.61,
            0.42,
        ),
    ]

    dashboard = director.executive_dashboard(ventures)
    plans = director.allocate_capital(ventures, available_budget=50000.0)

    return {
        "ok": True,
        "top_venture": dashboard["ranking"][0]["venture"]["venture_id"],
        "portfolio_margin": dashboard["total_monthly_margin"],
        "capital_plans": [asdict(plan) for plan in plans],
        "funds_transferred": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("demo", "status"))
    args = parser.parse_args()

    if args.action == "demo":
        print(json.dumps(demo(), indent=2, sort_keys=True))
        return 0

    print(
        json.dumps(
            {
                "ok": True,
                "state_files": sorted(path.name for path in STATE_DIR.glob("*")),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
