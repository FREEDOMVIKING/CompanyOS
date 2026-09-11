#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.default_specialist_registry import register_default_specialists
from companyos.runtime.ceo_goal_decomposer import CEOGoalDecomposer
from companyos.runtime.dependency_aware_dispatcher import DependencyAwareDispatcher

with tempfile.TemporaryDirectory(prefix="phase96_goal_") as td:
    q = AutonomousTaskQueue(Path(td))
    dispatcher = AutonomousTaskDispatcher(q)
    register_default_specialists(dispatcher)
    dep = DependencyAwareDispatcher(dispatcher)
    decomposer = CEOGoalDecomposer(q)

    result = decomposer.decompose(
        goal="launch a test digital product",
        priority_base=10,
        goal_id="goal-test-001",
    )

    before = {t.task_type: t.state for t in q.all_tasks()}

    r1 = dep.dispatch_next()
    r2 = dep.dispatch_next()
    r3 = dep.dispatch_next()
    r4 = dep.dispatch_next()

    after = {t.task_type: t.state for t in q.all_tasks()}

    checks = {
        "three_tasks_created": result.tasks_created == 3,
        "task_types_correct": result.task_types == ["research", "planning", "build"],
        "all_initially_queued": all(v == "QUEUED" for v in before.values()),
        "research_dispatched_first": r1.agent_name == "research_agent",
        "planning_dispatched_second": r2.agent_name == "planning_agent",
        "build_dispatched_third": r3.agent_name == "builder_agent",
        "none_ready_after_completion": r4.reason == "no_dependency_ready_task",
        "all_completed": all(v == "COMPLETED" for v in after.values()),
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("GOAL_DECOMPOSER_SIGNS_TRANSACTION: False")
    print("GOAL_DECOMPOSER_BROADCASTS: False")
    print("PHASE96_GOAL_DECOMPOSITION_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
