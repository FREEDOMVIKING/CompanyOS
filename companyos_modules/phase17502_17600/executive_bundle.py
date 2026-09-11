#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path.home() / "companyos"
STATE_DIR = ROOT / "companyos_runtime" / "phase17502_17600"
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class Opportunity:
    opportunity_id: str
    title: str
    expected_revenue: float
    estimated_cost: float
    confidence: float
    execution_complexity: float
    strategic_fit: float
    risk: float

    def score(self) -> float:
        margin = max(self.expected_revenue - self.estimated_cost, 0.0)
        return round(
            (margin * 0.0001)
            + (self.confidence * 30.0)
            + (self.strategic_fit * 25.0)
            - (self.execution_complexity * 15.0)
            - (self.risk * 20.0),
            4,
        )


@dataclass(slots=True)
class Specialist:
    specialist_id: str
    role: str
    capabilities: set[str]
    workload: int = 0
    reliability: float = 0.8

    def suitability(self, required: set[str]) -> float:
        if not required:
            overlap = 1.0
        else:
            overlap = len(self.capabilities & required) / len(required)
        workload_penalty = min(self.workload / 20.0, 0.5)
        return round((overlap * 0.65) + (self.reliability * 0.35) - workload_penalty, 4)


@dataclass(slots=True)
class WorkItem:
    work_id: str
    title: str
    required_capabilities: set[str]
    priority: int
    depends_on: list[str] = field(default_factory=list)
    assigned_to: str | None = None
    status: str = "queued"


@dataclass(slots=True)
class Decision:
    decision_id: str
    opportunity_id: str
    action: str
    score: float
    rationale: list[str]
    created_at: float


class AutonomousExecutiveBundle:
    """Deterministic executive planner for opportunity ranking and delegation."""

    def __init__(self, state_dir: Path = STATE_DIR) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _stable_id(prefix: str, payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True, default=list).encode("utf-8")
        return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:12]}"

    def evaluate_opportunity(self, opportunity: Opportunity) -> Decision:
        score = opportunity.score()
        rationale: list[str] = []

        if opportunity.confidence >= 0.7:
            rationale.append("confidence_above_execution_threshold")
        else:
            rationale.append("confidence_requires_more_validation")

        if opportunity.risk <= 0.4:
            rationale.append("risk_within_autonomous_planning_limit")
        else:
            rationale.append("risk_requires_guarded_execution")

        if opportunity.expected_revenue > opportunity.estimated_cost:
            rationale.append("positive_expected_margin")
        else:
            rationale.append("non_positive_expected_margin")

        if score >= 45 and opportunity.risk <= 0.4:
            action = "advance_to_planning"
        elif score >= 25:
            action = "validate_further"
        else:
            action = "deprioritize"

        decision = Decision(
            decision_id=self._stable_id("decision", asdict(opportunity)),
            opportunity_id=opportunity.opportunity_id,
            action=action,
            score=score,
            rationale=rationale,
            created_at=time.time(),
        )
        self._append_jsonl(self.state_dir / "decision_ledger.jsonl", asdict(decision))
        return decision

    def rank_opportunities(
        self,
        opportunities: Iterable[Opportunity],
    ) -> list[dict[str, Any]]:
        ranked = [
            {
                "opportunity": asdict(item),
                "score": item.score(),
            }
            for item in opportunities
        ]
        ranked.sort(key=lambda row: row["score"], reverse=True)
        return ranked

    def assign_work(
        self,
        work_items: list[WorkItem],
        specialists: list[Specialist],
    ) -> list[WorkItem]:
        completed: set[str] = set()
        pending = sorted(work_items, key=lambda item: (-item.priority, item.work_id))
        assigned: list[WorkItem] = []

        while pending:
            progress = False
            for item in list(pending):
                if any(dep not in completed for dep in item.depends_on):
                    continue

                ranked = sorted(
                    specialists,
                    key=lambda specialist: (
                        specialist.suitability(item.required_capabilities),
                        -specialist.workload,
                        specialist.specialist_id,
                    ),
                    reverse=True,
                )

                if ranked and ranked[0].suitability(item.required_capabilities) > 0:
                    chosen = ranked[0]
                    item.assigned_to = chosen.specialist_id
                    item.status = "assigned"
                    chosen.workload += 1
                else:
                    item.status = "blocked_no_specialist"

                assigned.append(item)
                completed.add(item.work_id)
                pending.remove(item)
                progress = True

            if not progress:
                for item in pending:
                    item.status = "blocked_dependency_cycle"
                    assigned.append(item)
                break

        self._write_json(
            self.state_dir / "latest_assignments.json",
            [asdict(item) for item in assigned],
        )
        return assigned

    def build_execution_packet(
        self,
        opportunity: Opportunity,
        decision: Decision,
        work_items: list[WorkItem],
    ) -> dict[str, Any]:
        packet = {
            "packet_id": self._stable_id(
                "packet",
                {
                    "opportunity": asdict(opportunity),
                    "decision": asdict(decision),
                    "work": [asdict(item) for item in work_items],
                },
            ),
            "created_at": time.time(),
            "opportunity": asdict(opportunity),
            "decision": asdict(decision),
            "work_items": [asdict(item) for item in work_items],
            "external_actions_allowed": False,
            "financial_actions_allowed": False,
            "requires_existing_approval_gates": True,
        }
        self._write_json(self.state_dir / "latest_execution_packet.json", packet)
        return packet

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=list) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    @staticmethod
    def _append_jsonl(path: Path, payload: Any) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, default=list) + "\n")


def demo() -> dict[str, Any]:
    bundle = AutonomousExecutiveBundle()

    opportunity = Opportunity(
        opportunity_id="demo_venture",
        title="Automated recurring-service business",
        expected_revenue=120000.0,
        estimated_cost=18000.0,
        confidence=0.78,
        execution_complexity=0.35,
        strategic_fit=0.9,
        risk=0.28,
    )

    specialists = [
        Specialist("research_1", "research", {"research", "validation"}, reliability=0.9),
        Specialist("builder_1", "builder", {"python", "api", "testing"}, reliability=0.86),
        Specialist("ops_1", "operations", {"operations", "launch"}, reliability=0.84),
    ]

    work = [
        WorkItem("w1", "Validate customer problem", {"research", "validation"}, 100),
        WorkItem("w2", "Build minimum viable product", {"python", "api"}, 90, ["w1"]),
        WorkItem("w3", "Verify implementation", {"testing"}, 80, ["w2"]),
        WorkItem("w4", "Prepare controlled launch", {"operations", "launch"}, 70, ["w3"]),
    ]

    decision = bundle.evaluate_opportunity(opportunity)
    assigned = bundle.assign_work(work, specialists)
    packet = bundle.build_execution_packet(opportunity, decision, assigned)

    return {
        "ok": True,
        "decision": asdict(decision),
        "assignments": [asdict(item) for item in assigned],
        "packet_id": packet["packet_id"],
        "external_actions_allowed": packet["external_actions_allowed"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("demo", "status"))
    args = parser.parse_args()

    if args.action == "demo":
        print(json.dumps(demo(), indent=2, sort_keys=True, default=list))
        return 0

    files = sorted(str(path.name) for path in STATE_DIR.glob("*"))
    print(json.dumps({"ok": True, "state_files": files}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
