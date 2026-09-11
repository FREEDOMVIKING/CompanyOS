#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
STATE_DIR = ROOT / "companyos_runtime" / "phase18001_18100"
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class VentureTask:
    task_id: str
    venture_id: str
    title: str
    priority: float
    expected_value: float
    risk_score: float
    duration_units: int
    dependencies: list[str]
    required_capabilities: list[str]
    blocked: bool = False


@dataclass(slots=True)
class ScheduleDecision:
    task_id: str
    venture_id: str
    sequence: int | None
    action: str
    score: float
    reason: str


class VentureScheduler:
    """Dependency-aware portfolio scheduler and recovery planner."""

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
    def _event_id(prefix: str, payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:12]}"

    @staticmethod
    def _score(task: VentureTask) -> float:
        if task.blocked:
            return -1.0
        priority = max(0.0, min(100.0, task.priority)) / 100.0
        value = max(0.0, task.expected_value)
        risk = max(0.0, min(1.0, task.risk_score))
        duration_penalty = min(1.0, max(1, task.duration_units) / 20.0)
        return round(
            (priority * 0.40)
            + (value * 0.35)
            + ((1.0 - risk) * 0.20)
            + ((1.0 - duration_penalty) * 0.05),
            6,
        )

    def validate_dependencies(
        self,
        tasks: list[VentureTask],
        completed_task_ids: set[str],
    ) -> dict[str, Any]:
        task_ids = {task.task_id for task in tasks}
        missing: dict[str, list[str]] = {}
        cycles: list[list[str]] = []

        for task in tasks:
            unresolved = [
                dep
                for dep in task.dependencies
                if dep not in completed_task_ids and dep not in task_ids
            ]
            if unresolved:
                missing[task.task_id] = unresolved

        graph = {
            task.task_id: [dep for dep in task.dependencies if dep in task_ids]
            for task in tasks
        }

        visiting: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = []

        def visit(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                start = stack.index(node)
                cycles.append(stack[start:] + [node])
                return
            visiting.add(node)
            stack.append(node)
            for dep in graph.get(node, []):
                visit(dep)
            stack.pop()
            visiting.remove(node)
            visited.add(node)

        for node in graph:
            visit(node)

        report = {
            "generated_at": time.time(),
            "missing_dependencies": missing,
            "cycles": cycles,
            "valid": not missing and not cycles,
        }
        self._write(self.state_dir / "dependency_validation.json", report)
        return report

    def schedule(
        self,
        tasks: list[VentureTask],
        *,
        completed_task_ids: set[str] | None = None,
        capability_pool: set[str] | None = None,
        max_parallel: int = 3,
    ) -> list[ScheduleDecision]:
        completed = completed_task_ids or set()
        capabilities = capability_pool or set()
        max_parallel = max(1, int(max_parallel))

        remaining = {task.task_id: task for task in tasks}
        decisions: list[ScheduleDecision] = []
        scheduled_ids: set[str] = set()
        sequence = 1

        while remaining:
            eligible: list[VentureTask] = []
            stalled: list[VentureTask] = []

            for task in remaining.values():
                deps_ok = all(
                    dep in completed or dep in scheduled_ids
                    for dep in task.dependencies
                )
                caps_ok = all(
                    cap in capabilities
                    for cap in task.required_capabilities
                )

                if task.blocked or not deps_ok or not caps_ok:
                    stalled.append(task)
                else:
                    eligible.append(task)

            if not eligible:
                for task in stalled:
                    if task.blocked:
                        reason = "task_blocked"
                    elif not all(
                        dep in completed or dep in scheduled_ids
                        for dep in task.dependencies
                    ):
                        reason = "dependencies_unresolved"
                    else:
                        reason = "required_capability_missing"

                    decisions.append(
                        ScheduleDecision(
                            task_id=task.task_id,
                            venture_id=task.venture_id,
                            sequence=None,
                            action="hold",
                            score=self._score(task),
                            reason=reason,
                        )
                    )
                    remaining.pop(task.task_id, None)
                break

            eligible.sort(
                key=lambda task: (
                    self._score(task),
                    -task.duration_units,
                ),
                reverse=True,
            )

            batch = eligible[:max_parallel]
            for task in batch:
                decisions.append(
                    ScheduleDecision(
                        task_id=task.task_id,
                        venture_id=task.venture_id,
                        sequence=sequence,
                        action="schedule",
                        score=self._score(task),
                        reason="highest_value_dependency_ready_task",
                    )
                )
                scheduled_ids.add(task.task_id)
                remaining.pop(task.task_id, None)
                sequence += 1

        payload = {
            "generated_at": time.time(),
            "completed_task_ids": sorted(completed),
            "capability_pool": sorted(capabilities),
            "max_parallel": max_parallel,
            "decisions": [asdict(item) for item in decisions],
        }
        self._write(self.state_dir / "latest_schedule.json", payload)
        self._append(
            self.state_dir / "schedule_ledger.jsonl",
            {
                "event_id": self._event_id("schedule", payload),
                "event": "portfolio_schedule_generated",
                **payload,
            },
        )
        return decisions

    def rebalance(
        self,
        decisions: list[ScheduleDecision],
        *,
        worker_capacity: int,
        capability_pool: set[str],
    ) -> dict[str, Any]:
        scheduled = [
            item for item in decisions
            if item.action == "schedule" and item.sequence is not None
        ]
        scheduled.sort(key=lambda item: item.sequence or 10**9)

        worker_capacity = max(0, int(worker_capacity))
        assignments = []
        for index, decision in enumerate(scheduled):
            worker_slot = index + 1 if index < worker_capacity else None
            assignments.append(
                {
                    "task_id": decision.task_id,
                    "venture_id": decision.venture_id,
                    "worker_slot": worker_slot,
                    "status": "assigned" if worker_slot else "queued",
                }
            )

        payload = {
            "generated_at": time.time(),
            "worker_capacity": worker_capacity,
            "capability_pool": sorted(capability_pool),
            "assignments": assignments,
            "queued_count": sum(
                1 for item in assignments if item["status"] == "queued"
            ),
        }
        self._write(self.state_dir / "latest_rebalance.json", payload)
        return payload

    def recovery_plan(
        self,
        decisions: list[ScheduleDecision],
    ) -> dict[str, Any]:
        actions = []
        for decision in decisions:
            if decision.action != "hold":
                continue

            mapping = {
                "task_blocked": "escalate_existing_blocker",
                "dependencies_unresolved": "repair_dependency_chain",
                "required_capability_missing": "request_internal_specialist",
            }
            actions.append(
                {
                    "task_id": decision.task_id,
                    "venture_id": decision.venture_id,
                    "action": mapping.get(
                        decision.reason,
                        "inspect_scheduler_state",
                    ),
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
        self._write(self.state_dir / "latest_scheduler_recovery.json", payload)
        return payload

    def executive_plan(
        self,
        decisions: list[ScheduleDecision],
        rebalance: dict[str, Any],
        recovery: dict[str, Any],
    ) -> dict[str, Any]:
        scheduled = [
            item for item in decisions if item.action == "schedule"
        ]
        selected = max(
            scheduled,
            key=lambda item: item.score,
            default=None,
        )

        payload = {
            "generated_at": time.time(),
            "decision": (
                "execute_internal_schedule"
                if selected
                else "repair_before_scheduling"
            ),
            "selected_task_id": selected.task_id if selected else None,
            "selected_venture_id": selected.venture_id if selected else None,
            "selected_score": selected.score if selected else None,
            "queued_count": rebalance["queued_count"],
            "recovery_action_count": len(recovery["actions"]),
            "external_action_executed": False,
            "financial_action_executed": False,
        }
        self._write(self.state_dir / "latest_executive_plan.json", payload)
        return payload

    def demo(self) -> dict[str, Any]:
        tasks = [
            VentureTask(
                "discover_alpha",
                "venture_alpha",
                "Validate customer problem",
                95,
                0.90,
                0.15,
                2,
                [],
                ["research"],
            ),
            VentureTask(
                "build_alpha",
                "venture_alpha",
                "Build MVP",
                92,
                0.86,
                0.20,
                6,
                ["discover_alpha"],
                ["python"],
            ),
            VentureTask(
                "test_alpha",
                "venture_alpha",
                "Run internal validation",
                88,
                0.78,
                0.18,
                3,
                ["build_alpha"],
                ["testing"],
            ),
            VentureTask(
                "research_beta",
                "venture_beta",
                "Research second opportunity",
                84,
                0.72,
                0.25,
                3,
                [],
                ["research"],
            ),
            VentureTask(
                "launch_gamma",
                "venture_gamma",
                "Prepare external launch",
                90,
                0.88,
                0.30,
                4,
                [],
                ["deployment"],
                blocked=True,
            ),
        ]

        capabilities = {"research", "python", "testing"}
        dependency_report = self.validate_dependencies(tasks, set())
        decisions = self.schedule(
            tasks,
            capability_pool=capabilities,
            max_parallel=2,
        )
        rebalance = self.rebalance(
            decisions,
            worker_capacity=3,
            capability_pool=capabilities,
        )
        recovery = self.recovery_plan(decisions)
        executive = self.executive_plan(
            decisions,
            rebalance,
            recovery,
        )

        return {
            "ok": True,
            "dependency_report": dependency_report,
            "decisions": [asdict(item) for item in decisions],
            "rebalance": rebalance,
            "recovery": recovery,
            "executive_plan": executive,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["demo", "status"])
    args = parser.parse_args()

    scheduler = VentureScheduler()
    result = (
        scheduler.demo()
        if args.action == "demo"
        else {
            "ok": True,
            "state_files": sorted(
                path.name for path in scheduler.state_dir.glob("*")
            ),
        }
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
