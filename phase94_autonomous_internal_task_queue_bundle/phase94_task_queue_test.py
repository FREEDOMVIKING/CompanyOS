#!/usr/bin/env python3
from pathlib import Path
import tempfile
import time

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

with tempfile.TemporaryDirectory(prefix="phase94_queue_") as td:
    q = AutonomousTaskQueue(Path(td))

    low = q.enqueue(
        task_type="research",
        payload={"topic": "low"},
        priority=50,
        idempotency_key="low",
    )

    high = q.enqueue(
        task_type="research",
        payload={"topic": "high"},
        priority=10,
        idempotency_key="high",
    )

    duplicate = q.enqueue(
        task_type="research",
        payload={"topic": "changed"},
        priority=1,
        idempotency_key="high",
    )

    claimed = q.claim_next(agent_name="research_agent")
    q.mark_running(claimed)
    q.complete(claimed, {"ok": True})

    stale = q.enqueue(
        task_type="build",
        payload={"name": "recover-me"},
        priority=20,
        idempotency_key="stale",
    )
    stale = q.claim_next(agent_name="builder_agent")
    q.mark_running(stale)
    stale.updated_at_unix = time.time() - 9999
    q.save(stale)

    recovered = q.recover_stale(stale_after_seconds=60)

    checks = {
        "priority_order": claimed.task_id == high.task_id,
        "duplicate_protection": duplicate.task_id == high.task_id,
        "completion_persisted": q.load(high.task_id).state == "COMPLETED",
        "stale_recovered": len(recovered) == 1,
        "stale_requeued": q.load(stale.task_id).state == "QUEUED",
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("TASK_QUEUE_SIGNS_TRANSACTION: False")
    print("TASK_QUEUE_BROADCASTS: False")
    print("PHASE94_TASK_QUEUE_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
