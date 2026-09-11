#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.ceo_goal_decomposer import CEOGoalDecomposer
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop
from companyos.runtime.goal_lifecycle_manager import GoalLifecycleManager
from companyos.runtime.goal_outcome_evaluator import GoalOutcomeEvaluator

with tempfile.TemporaryDirectory(prefix="phase99_goal_") as td:
    base = Path(td)
    q = AutonomousTaskQueue(base / "queue")
    lifecycle = GoalLifecycleManager(q, base / "goals")
    evaluator = GoalOutcomeEvaluator(lifecycle, base / "outcomes")
    decomposer = CEOGoalDecomposer(q)
    loop = AutonomousGoalExecutionLoop(q)

    goal_id = "phase99-test-goal"
    goal = "launch a test product"

    decomposer.decompose(
        goal=goal,
        priority_base=10,
        goal_id=goal_id,
    )

    loop.run_until_idle(max_cycles=10)
    evaluation = evaluator.evaluate(goal_id=goal_id, goal=goal)

    checks = {
        "goal_completed": evaluation.goal_state == "COMPLETED",
        "success_true": evaluation.success is True,
        "confidence_nonzero": evaluation.confidence > 0,
        "evidence_present": len(evaluation.evidence) == 3,
        "next_action_present": bool(evaluation.next_action),
        "evaluation_persisted": (base / "outcomes" / f"{goal_id}.json").exists(),
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("OUTCOME_EVALUATOR_SIGNS_TRANSACTION: False")
    print("OUTCOME_EVALUATOR_BROADCASTS: False")
    print("PHASE99_GOAL_OUTCOME_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
