from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from companyos.canonicalexec import CanonicalExecutionGateway, ExecutionRequest

from .contracts import GoalRequest, GoalRunResult
from .planner import ConservativeGoalPlanner
from .store import OrchestrationStore

class CanonicalOrchestrationBridge:
    def __init__(self, companyos_root: str | None = None):
        self.companyos_root = Path(
            companyos_root or os.environ.get(
                "COMPANYOS_ROOT",
                str(Path.home() / "companyos")
            )
        )
        self.runtime_root = self.companyos_root / "companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)

        self.gateway = CanonicalExecutionGateway(str(self.companyos_root))
        self.planner = ConservativeGoalPlanner()
        self.store = OrchestrationStore(self.runtime_root)

    def status(self) -> Dict[str, Any]:
        return {
            "ready": True,
            "reason": "canonical_orchestration_ready",
            "gateway": self.gateway.status(),
            "store": self.store.summary(),
            "planner": "ConservativeGoalPlanner",
        }

    def run_goal(self, goal: GoalRequest) -> GoalRunResult:
        self.store.write_goal(goal.goal_id, goal.to_dict())
        self.store.append("goal_received", goal.to_dict())

        tasks = self.planner.decompose(goal)
        completed = blocked = failed = 0
        results = []

        for task in tasks:
            self.store.write_task(task.task_id, task.to_dict())
            self.store.append("task_queued", task.to_dict())

            req = ExecutionRequest(
                action=task.action,
                payload=task.payload,
                source="canonical_orchestration",
                requires_human_approval=task.requires_human_approval,
                external_action=task.external_action,
                financial_action=task.financial_action,
                idempotency_key=task.task_id,
            )

            try:
                result = self.gateway.execute(req).to_dict()
                task.result = result

                if result.get("accepted"):
                    task.status = "completed"
                    completed += 1
                else:
                    task.status = "blocked"
                    blocked += 1

            except Exception as e:
                task.status = "failed"
                task.result = {"error": repr(e)}
                failed += 1

            self.store.write_task(task.task_id, task.to_dict())
            self.store.append("task_finished", task.to_dict())
            results.append(task.to_dict())

        status = "completed"
        if failed:
            status = "completed_with_failures"
        elif blocked:
            status = "completed_with_blocks"

        out = GoalRunResult(
            goal_id=goal.goal_id,
            objective=goal.objective,
            status=status,
            tasks_total=len(tasks),
            tasks_completed=completed,
            tasks_blocked=blocked,
            tasks_failed=failed,
            task_results=results,
        )

        self.store.write_goal(goal.goal_id, {
            **goal.to_dict(),
            "run_result": out.to_dict(),
        })
        self.store.append("goal_finished", out.to_dict())
        return out
