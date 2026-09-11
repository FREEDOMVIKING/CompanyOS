from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class VentureSignal:
    venture_id: str
    throughput: float
    backlog: int
    health_score: float
    expected_value: float
    risk_score: float
    dependency_pressure: float
    workers_current: int
    workers_minimum: int
    workers_maximum: int
    blocked: bool = False


class PortfolioBalancer:
    def __init__(self, state_dir: Path | None = None) -> None:
        root = Path.home() / "companyos"
        self.state_dir = state_dir or (
            root / "companyos_runtime" / "phase18101_18200"
        )
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _score(signal: VentureSignal) -> float:
        if signal.blocked:
            return -1.0
        backlog_pressure = min(1.0, max(0, signal.backlog) / 20.0)
        throughput_pressure = 1.0 - max(0.0, min(1.0, signal.throughput))
        health = max(0.0, min(100.0, signal.health_score)) / 100.0
        value = max(0.0, signal.expected_value)
        risk = max(0.0, min(1.0, signal.risk_score))
        dependency = max(0.0, min(1.0, signal.dependency_pressure))
        return round(
            value * 0.30
            + backlog_pressure * 0.20
            + dependency * 0.15
            + (1.0 - risk) * 0.15
            + health * 0.10
            + throughput_pressure * 0.10,
            6,
        )

    def rank(self, signals: list[VentureSignal]) -> list[dict[str, Any]]:
        rows = sorted(
            (
                {
                    "venture_id": signal.venture_id,
                    "score": self._score(signal),
                    "blocked": signal.blocked,
                }
                for signal in signals
            ),
            key=lambda row: row["score"],
            reverse=True,
        )
        path = self.state_dir / "latest_priority_ranking.json"
        path.write_text(
            json.dumps(
                {"generated_at": time.time(), "ranking": rows},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return rows

    def demo(self) -> dict[str, Any]:
        signals = [
            VentureSignal("alpha", 0.72, 9, 88, 0.90, 0.18, 0.45, 3, 2, 5),
            VentureSignal("beta", 0.48, 14, 76, 0.78, 0.25, 0.70, 2, 1, 4),
            VentureSignal(
                "blocked", 0.10, 18, 35, 0.88, 0.40, 0.90, 1, 0, 2, True
            ),
        ]
        return {
            "ok": True,
            "ranking": self.rank(signals),
            "external_actions_enabled": False,
            "financial_actions_enabled": False,
            "external_actions_require_existing_gate": True,
            "financial_actions_require_existing_gate": True,
        }


if __name__ == "__main__":
    print(json.dumps(PortfolioBalancer().demo(), indent=2, sort_keys=True))
