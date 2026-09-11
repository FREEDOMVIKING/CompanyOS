#!/usr/bin/env python3
import tempfile
from pathlib import Path

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
from companyos.runtime.autonomous_ceo_runtime_service import AutonomousCEORuntimeService

with tempfile.TemporaryDirectory(prefix="phase101_ceo_runtime_") as td:
    base = Path(td)

    queue = AutonomousTaskQueue(base / "task_queue")
    ceo = AutonomousCEOOrchestrator(queue=queue, root=base)

    record = ceo.start(
        goal="research, plan, and build an internal test product concept",
        orchestration_id="phase101-test",
        max_cycles=20,
        max_follow_up_depth=1,
        priority_base=10,
    )

    service = AutonomousCEORuntimeService(
        interval_seconds=2,
        max_consecutive_failures=3,
        state_path=base / "ceo_runtime_state.json",
    )
    service.ceo = ceo

    state = service.startup()

    for _ in range(10):
        state = service.cycle(state)
        final = ceo.load(record.orchestration_id)
        if final.state in ("COMPLETED", "FAILED", "HALTED"):
            break

    final = ceo.load(record.orchestration_id)

    checks = {
        "runtime_started": state.running is True,
        "orchestration_completed": final.state == "COMPLETED",
        "service_cycles_advanced": state.cycle_count > 0,
        "completed_count_visible": state.completed_orchestrations >= 1,
        "no_external_actions": state.external_actions_performed is False,
        "no_transaction_broadcasts": state.transaction_broadcasts is False,
        "service_state_persisted": (base / "ceo_runtime_state.json").exists(),
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("PHASE101_CEO_RUNTIME_ONCE:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
