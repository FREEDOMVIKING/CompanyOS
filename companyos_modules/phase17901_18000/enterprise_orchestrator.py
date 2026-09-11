#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
STATE_DIR = ROOT / "companyos_runtime" / "phase17901_18000"
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class VentureWorkload:
    venture_id: str
    priority: float
    expected_roi: float
    risk_score: float
    health_score: float
    required_workers: int
    required_compute: float
    blocked: bool = False


@dataclass(slots=True)
class AllocationDecision:
    venture_id: str
    workers_allocated: int
    compute_allocated: float
    score: float
    action: str
    reason: str


class EnterpriseOrchestrator:
    """Portfolio-wide scheduler, optimizer, telemetry, and recovery coordinator."""

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
    def _stable_id(prefix: str, payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:12]}"

    @staticmethod
    def _score(item: VentureWorkload) -> float:
        if item.blocked:
            return -1.0
        priority = max(0.0, min(100.0, item.priority)) / 100.0
        roi = max(0.0, item.expected_roi)
        risk = max(0.0, min(1.0, item.risk_score))
        health = max(0.0, min(100.0, item.health_score)) / 100.0
        return round((priority * 0.35) + (roi * 0.30) + ((1.0 - risk) * 0.20) + (health * 0.15), 6)

    def allocate(
        self,
        workloads: list[VentureWorkload],
        *,
        worker_capacity: int,
        compute_capacity: float,
    ) -> list[AllocationDecision]:
        worker_capacity = max(0, int(worker_capacity))
        compute_capacity = max(0.0, float(compute_capacity))

        ranked = sorted(
            workloads,
            key=lambda item: (self._score(item), item.health_score),
            reverse=True,
        )

        decisions: list[AllocationDecision] = []
        workers_left = worker_capacity
        compute_left = compute_capacity

        for item in ranked:
            score = self._score(item)

            if item.blocked:
                decisions.append(
                    AllocationDecision(
                        venture_id=item.venture_id,
                        workers_allocated=0,
                        compute_allocated=0.0,
                        score=score,
                        action="hold",
                        reason="venture_blocked",
                    )
                )
                continue

            workers = min(item.required_workers, workers_left)
            compute = min(item.required_compute, compute_left)

            if workers <= 0 or compute <= 0:
                action = "queue"
                reason = "capacity_exhausted"
                workers = 0
                compute = 0.0
            elif workers < item.required_workers or compute < item.required_compute:
                action = "partial_allocate"
                reason = "partial_capacity_available"
            else:
                action = "allocate"
                reason = "highest_available_portfolio_value"

            workers_left -= workers
            compute_left -= compute

            decisions.append(
                AllocationDecision(
                    venture_id=item.venture_id,
                    workers_allocated=workers,
                    compute_allocated=round(compute, 4),
                    score=score,
                    action=action,
                    reason=reason,
                )
            )

        payload = {
            "generated_at": time.time(),
            "worker_capacity": worker_capacity,
            "compute_capacity": compute_capacity,
            "workers_remaining": workers_left,
            "compute_remaining": round(compute_left, 4),
            "decisions": [asdict(item) for item in decisions],
        }
        self._write(self.state_dir / "latest_allocation.json", payload)
        self._append(
            self.state_dir / "allocation_ledger.jsonl",
            {
                "event_id": self._stable_id("allocation", payload),
                "event": "portfolio_resources_allocated",
                **payload,
            },
        )
        return decisions

    def detect_bottlenecks(
        self,
        workloads: list[VentureWorkload],
        decisions: list[AllocationDecision],
    ) -> list[dict[str, Any]]:
        by_id = {item.venture_id: item for item in workloads}
        bottlenecks: list[dict[str, Any]] = []

        for decision in decisions:
            workload = by_id[decision.venture_id]
            if workload.blocked:
                bottlenecks.append(
                    {
                        "venture_id": workload.venture_id,
                        "type": "blocked_state",
                        "severity": "high",
                        "recommended_action": "resolve_existing_blocker",
                    }
                )
            elif decision.action == "queue":
                bottlenecks.append(
                    {
                        "venture_id": workload.venture_id,
                        "type": "resource_capacity",
                        "severity": "medium",
                        "recommended_action": "defer_or_reallocate_capacity",
                    }
                )
            elif workload.health_score < 50:
                bottlenecks.append(
                    {
                        "venture_id": workload.venture_id,
                        "type": "venture_health",
                        "severity": "high",
                        "recommended_action": "run_recovery_workflow",
                    }
                )

        self._write(self.state_dir / "latest_bottlenecks.json", bottlenecks)
        return bottlenecks

    def self_heal(self, bottlenecks: list[dict[str, Any]]) -> dict[str, Any]:
        actions = []
        for item in bottlenecks:
            if item["type"] == "venture_health":
                action = "schedule_health_recovery"
            elif item["type"] == "resource_capacity":
                action = "rebalance_shared_resources"
            else:
                action = "escalate_existing_blocker"
            actions.append(
                {
                    "venture_id": item["venture_id"],
                    "action": action,
                    "external_action_executed": False,
                    "financial_action_executed": False,
                }
            )

        payload = {
            "generated_at": time.time(),
            "actions": actions,
            "external_actions_require_existing_gate": True,
            "financial_actions_require_existing_gate": True,
        }
        self._write(self.state_dir / "latest_recovery_plan.json", payload)
        return payload

    def telemetry(
        self,
        workloads: list[VentureWorkload],
        decisions: list[AllocationDecision],
        bottlenecks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        allocated_workers = sum(item.workers_allocated for item in decisions)
        allocated_compute = sum(item.compute_allocated for item in decisions)
        avg_health = (
            sum(item.health_score for item in workloads) / len(workloads)
            if workloads
            else 0.0
        )
        avg_score = (
            sum(max(0.0, item.score) for item in decisions) / len(decisions)
            if decisions
            else 0.0
        )

        payload = {
            "generated_at": time.time(),
            "venture_count": len(workloads),
            "allocated_workers": allocated_workers,
            "allocated_compute": round(allocated_compute, 4),
            "average_health": round(avg_health, 4),
            "average_priority_score": round(avg_score, 6),
            "bottleneck_count": len(bottlenecks),
            "blocked_venture_count": sum(1 for item in workloads if item.blocked),
            "external_actions_enabled": False,
            "financial_actions_enabled": False,
        }
        self._write(self.state_dir / "enterprise_telemetry.json", payload)
        return payload

    def executive_decision(
        self,
        workloads: list[VentureWorkload],
        decisions: list[AllocationDecision],
        bottlenecks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        candidates = [
            decision
            for decision in decisions
            if decision.action in {"allocate", "partial_allocate"}
        ]
        selected = max(candidates, key=lambda item: item.score, default=None)

        payload = {
            "generated_at": time.time(),
            "decision": "advance_portfolio_work" if selected else "hold_and_recover",
            "selected_venture_id": selected.venture_id if selected else None,
            "selected_score": selected.score if selected else None,
            "bottleneck_count": len(bottlenecks),
            "rationale": (
                "advance highest-value unblocked venture"
                if selected
                else "no venture currently satisfies execution criteria"
            ),
            "external_action_executed": False,
            "financial_action_executed": False,
        }
        self._write(self.state_dir / "latest_executive_decision.json", payload)
        return payload

    def demo(self) -> dict[str, Any]:
        workloads = [
            VentureWorkload("venture_alpha", 95, 0.82, 0.18, 88, 3, 1.5),
            VentureWorkload("venture_beta", 82, 0.68, 0.25, 73, 2, 1.0),
            VentureWorkload("venture_gamma", 70, 0.55, 0.40, 42, 2, 1.2),
            VentureWorkload("venture_delta", 90, 0.90, 0.15, 91, 2, 1.0, blocked=True),
        ]
        decisions = self.allocate(
            workloads,
            worker_capacity=6,
            compute_capacity=3.5,
        )
        bottlenecks = self.detect_bottlenecks(workloads, decisions)
        recovery = self.self_heal(bottlenecks)
        telemetry = self.telemetry(workloads, decisions, bottlenecks)
        executive = self.executive_decision(workloads, decisions, bottlenecks)

        return {
            "ok": True,
            "workload_count": len(workloads),
            "decisions": [asdict(item) for item in decisions],
            "bottlenecks": bottlenecks,
            "recovery": recovery,
            "telemetry": telemetry,
            "executive_decision": executive,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["demo", "status"])
    args = parser.parse_args()

    orchestrator = EnterpriseOrchestrator()
    result = (
        orchestrator.demo()
        if args.action == "demo"
        else {
            "ok": True,
            "state_files": sorted(
                path.name for path in orchestrator.state_dir.glob("*")
            ),
        }
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
