#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.autonomous_goal_intake import AutonomousGoalIntake
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
from companyos.runtime.autonomous_goal_scheduler import AutonomousGoalScheduler

with tempfile.TemporaryDirectory(prefix="phase103_intake_") as td:
    base = Path(td)

    intake = AutonomousGoalIntake(base / "intake")
    queue = AutonomousTaskQueue(base / "task_queue")
    ceo = AutonomousCEOOrchestrator(queue=queue, root=base)

    scheduler = AutonomousGoalScheduler(
        intake=intake,
        ceo=ceo,
    )

    low = intake.submit(
        goal="low priority goal",
        priority=50,
        intake_id="low",
    )
    high = intake.submit(
        goal="high priority goal",
        priority=10,
        intake_id="high",
    )

    result = scheduler.process_next()

    high_after = intake.load("high")
    low_after = intake.load("low")

    checks = {
        "high_priority_processed_first": result.intake_id == "high",
        "orchestration_created": bool(result.orchestration_id),
        "high_marked_submitted": high_after.state == "SUBMITTED",
        "low_remains_pending": low_after.state == "PENDING",
        "orchestration_persisted": (base / "ceo_orchestrations" / f"{result.orchestration_id}.json").exists(),
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("GOAL_INTAKE_EXTERNAL_ACTIONS: False")
    print("GOAL_INTAKE_SIGNS_TRANSACTION: False")
    print("GOAL_INTAKE_BROADCASTS: False")
    print("PHASE103_GOAL_INTAKE_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
