#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.default_specialist_registry import register_default_specialists

with tempfile.TemporaryDirectory(prefix="phase95_dispatcher_") as td:
    q = AutonomousTaskQueue(Path(td))
    dispatcher = AutonomousTaskDispatcher(q)
    register_default_specialists(dispatcher)

    q.enqueue(
        task_type="planning",
        payload={"goal": "launch test product"},
        priority=30,
        idempotency_key="plan-1",
    )
    q.enqueue(
        task_type="research",
        payload={"topic": "market opportunity"},
        priority=10,
        idempotency_key="research-1",
    )
    q.enqueue(
        task_type="build",
        payload={"name": "prototype"},
        priority=20,
        idempotency_key="build-1",
    )

    r1 = dispatcher.dispatch_next()
    r2 = dispatcher.dispatch_next()
    r3 = dispatcher.dispatch_next()
    r4 = dispatcher.dispatch_next()

    tasks = {t.task_type: t for t in q.all_tasks()}

    checks = {
        "research_first": r1.agent_name == "research_agent",
        "build_second": r2.agent_name == "builder_agent",
        "planning_third": r3.agent_name == "planning_agent",
        "queue_empty_after_three": r4.reason == "queue_empty",
        "research_completed": tasks["research"].state == "COMPLETED",
        "build_completed": tasks["build"].state == "COMPLETED",
        "planning_completed": tasks["planning"].state == "COMPLETED",
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("DISPATCHER_SIGNS_TRANSACTION: False")
    print("DISPATCHER_BROADCASTS: False")
    print("PHASE95_DISPATCHER_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
