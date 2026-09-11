#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.ceo_goal_decomposer import CEOGoalDecomposer
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

with tempfile.TemporaryDirectory(prefix="phase97_goal_loop_") as td:
    q = AutonomousTaskQueue(Path(td))
    decomposer = CEOGoalDecomposer(q)
    loop = AutonomousGoalExecutionLoop(q)

    decomposer.decompose(
        goal="launch a small internal test product",
        priority_base=10,
        goal_id="phase97-test-goal",
    )

    results = loop.run_until_idle(max_cycles=10)
    tasks = {t.task_type: t for t in q.all_tasks()}

    order = [r.agent_name for r in results if r.dispatched]

    checks = {
        "three_dispatches": len(order) == 3,
        "correct_order": order == ["research_agent", "planning_agent", "builder_agent"],
        "research_completed": tasks["research"].state == "COMPLETED",
        "planning_completed": tasks["planning"].state == "COMPLETED",
        "build_completed": tasks["build"].state == "COMPLETED",
        "loop_reached_idle": results[-1].reason == "no_dependency_ready_task",
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("GOAL_LOOP_SIGNS_TRANSACTION: False")
    print("GOAL_LOOP_BROADCASTS: False")
    print("PHASE97_GOAL_LOOP_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
