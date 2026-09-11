#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.ceo_goal_decomposer import CEOGoalDecomposer
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop
from companyos.runtime.goal_lifecycle_manager import GoalLifecycleManager

with tempfile.TemporaryDirectory(prefix="phase98_goal_") as td:
    base = Path(td)
    q = AutonomousTaskQueue(base / "queue")
    lifecycle = GoalLifecycleManager(q, base / "goals")
    decomposer = CEOGoalDecomposer(q)
    loop = AutonomousGoalExecutionLoop(q)

    goal_id = "phase98-test-goal"
    goal = "launch a small internal test product"

    decomposer.decompose(
        goal=goal,
        priority_base=10,
        goal_id=goal_id,
    )

    s1 = lifecycle.refresh(goal_id=goal_id, goal=goal)
    loop.cycle()
    s2 = lifecycle.refresh(goal_id=goal_id, goal=goal)
    loop.cycle()
    s3 = lifecycle.refresh(goal_id=goal_id, goal=goal)
    loop.cycle()
    s4 = lifecycle.refresh(goal_id=goal_id, goal=goal)

    checks = {
        "initial_executing": s1.state == "EXECUTING",
        "after_research_executing": s2.state == "EXECUTING",
        "after_planning_executing": s3.state == "EXECUTING",
        "final_completed": s4.state == "COMPLETED",
        "three_completed": s4.completed_tasks == 3,
        "final_result_present": isinstance(s4.final_result, dict),
        "outputs_aggregated": len(s4.final_result["outputs"]) == 3,
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("GOAL_LIFECYCLE_SIGNS_TRANSACTION: False")
    print("GOAL_LIFECYCLE_BROADCASTS: False")
    print("PHASE98_GOAL_LIFECYCLE_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
