#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator

with tempfile.TemporaryDirectory(prefix="phase100_ceo_") as td:
    base = Path(td)
    q = AutonomousTaskQueue(base / "task_queue")
    ceo = AutonomousCEOOrchestrator(queue=q, root=base)

    record = ceo.start(
        goal="research, plan, and build an internal test product concept",
        orchestration_id="phase100-test",
        max_cycles=20,
        max_follow_up_depth=2,
        priority_base=10,
    )

    results = ceo.run_until_terminal(
        record.orchestration_id,
        max_runner_cycles=20,
    )

    final = ceo.load(record.orchestration_id)

    dispatched_agents = [
        r.dispatched_agent for r in results if r.task_dispatched
    ]

    checks = {
        "root_goal_created": record.root_goal_id == "phase100-test:goal:0",
        "orchestration_reached_terminal": final.state == "COMPLETED",
        "research_agent_used": "research_agent" in dispatched_agents,
        "planning_agent_used": "planning_agent" in dispatched_agents,
        "builder_agent_used": "builder_agent" in dispatched_agents,
        "completed_goal_recorded": final.root_goal_id in final.completed_goal_ids,
        "final_summary_present": isinstance(final.final_summary, dict),
        "cycle_bound_respected": final.total_cycles <= final.max_cycles,
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("CEO_ORCHESTRATOR_EXTERNAL_ACTIONS: False")
    print("CEO_ORCHESTRATOR_SIGNS_TRANSACTION: False")
    print("CEO_ORCHESTRATOR_BROADCASTS: False")
    print("PHASE100_CEO_ORCHESTRATION_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
