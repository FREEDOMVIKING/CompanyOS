from __future__ import annotations

import json
import os
import time
import uuid
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from companyos.runtime.adaptive_backpressure import AdaptiveBackpressure
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue, TaskRecord
from companyos.runtime.default_specialist_registry import register_default_specialists
from companyos.runtime.dependency_aware_dispatcher import DependencyAwareDispatcher
from companyos.runtime.productive_autonomy_watchdog import _producer_throttle_gate

REPO = Path(os.environ["COMPANYOS_REPO_ROOT"]).resolve()
TMPHOME = Path.home().resolve()
RUNTIME = TMPHOME / ".companyos_runtime"

OUT = REPO / "audit/COMPANYOS_V69_4_SUSTAINED_EQUILIBRIUM_TEST.json"
OUT_MD = REPO / "audit/COMPANYOS_V69_4_SUSTAINED_EQUILIBRIUM_TEST.md"

TASK_TYPES = ["research"] * 6 + ["planning"] * 3 + ["build"]


def seed_direct(queue: AutonomousTaskQueue, *, count: int, scenario: str, tick: int) -> Counter:
    """Fast deterministic benchmark producer; dispatch still uses real queue lifecycle."""
    queue.root.mkdir(parents=True, exist_ok=True)
    now = time.time()
    dist = Counter()

    for i in range(count):
        task_type = TASK_TYPES[i % len(TASK_TYPES)]
        dist[task_type] += 1
        task_id = f"v69-4-{scenario}-{tick:03d}-{i:04d}-{uuid.uuid4().hex[:8]}"
        rec = TaskRecord(
            task_id=task_id,
            idempotency_key=f"v69.4:{scenario}:{tick}:{i}",
            task_type=task_type,
            priority=100 + (i % 5),
            payload={
                "goal_id": f"v69-4-{scenario}",
                "goal": f"V69.4 {scenario} internal benchmark tick {tick} task {i}",
                "topic": f"V69.4 {scenario} internal benchmark tick {tick} task {i}",
                "name": f"V69.4 {scenario} internal benchmark tick {tick} task {i}",
                "internal_only": True,
                "benchmark": "V69.4",
            },
            state="QUEUED",
            assigned_agent=None,
            attempts=0,
            max_attempts=3,
            created_at_unix=now + (i * 0.000001),
            updated_at_unix=now,
            next_attempt_unix=now,
            result=None,
            last_error=None,
        )
        path = queue.root / f"{task_id}.json"
        path.write_text(json.dumps(asdict(rec), sort_keys=True) + "\n", encoding="utf-8")

    return dist


def queue_counts(queue: AutonomousTaskQueue) -> dict:
    c = Counter()
    by_type = Counter()
    for task in queue._iter_task_files():
        c[task.state] += 1
        if task.state == "QUEUED":
            by_type[task.task_type] += 1
    return {
        "queued": c["QUEUED"],
        "completed": c["COMPLETED"],
        "failed": c["FAILED"],
        "running": c["RUNNING"] + c["CLAIMED"],
        "queued_by_type": dict(by_type),
        "total": sum(c.values()),
    }


def make_dispatcher(queue: AutonomousTaskQueue) -> DependencyAwareDispatcher:
    base = AutonomousTaskDispatcher(queue)
    register_default_specialists(base)
    return DependencyAwareDispatcher(base)


def run_sustained_scenario() -> dict:
    """
    Sustainable load:
      - 30 controller ticks
      - producer burst of 80 tasks when gate allows
      - execution batch comes directly from AdaptiveBackpressure
    """
    scenario = "sustainable"
    queue = AutonomousTaskQueue(RUNTIME / "v69_4" / scenario / "task_queue")
    dispatcher = make_dispatcher(queue)
    bp = AdaptiveBackpressure(queue)
    bp.state_path = RUNTIME / "v69_4" / scenario / "adaptive_backpressure_state.json"
    ws = {}

    ticks = 30
    burst = 80
    rows = []
    produced_total = 0
    dispatched_total = 0
    max_queued_after_production = 0
    max_queued_after_execution = 0
    blocked_ticks = 0
    allowed_ticks = 0

    start = time.perf_counter()

    for tick in range(1, ticks + 1):
        decision = bp.decide()
        gate = _producer_throttle_gate(decision, ws)

        produced = 0
        if gate["allow_producer"]:
            seed_direct(queue, count=burst, scenario=scenario, tick=tick)
            produced = burst
            produced_total += burst
            allowed_ticks += 1
        else:
            blocked_ticks += 1

        pre_exec = queue_counts(queue)
        max_queued_after_production = max(max_queued_after_production, pre_exec["queued"])

        results = dispatcher.dispatch_batch(max_dispatches=int(decision["execution_batch"]))
        dispatched = sum(1 for x in results if x.dispatched)
        dispatched_total += dispatched

        after = queue_counts(queue)
        max_queued_after_execution = max(max_queued_after_execution, after["queued"])

        rows.append({
            "tick": tick,
            "producer_allowed": gate["allow_producer"],
            "producer_action": gate["action"],
            "producer_divisor": gate["producer_divisor"],
            "execution_batch": decision["execution_batch"],
            "boost_type": decision["boost_type"],
            "produced": produced,
            "dispatched": dispatched,
            "queued_after_production": pre_exec["queued"],
            "queued_after_execution": after["queued"],
            "failed": after["failed"],
        })

    elapsed = time.perf_counter() - start
    final = queue_counts(queue)

    passed = all([
        produced_total > 0,
        blocked_ticks > 0,
        final["failed"] == 0,
        final["queued"] <= burst,
        max_queued_after_production <= 200,
        max_queued_after_execution <= 128,
        dispatched_total > 0,
    ])

    return {
        "scenario": scenario,
        "ticks": ticks,
        "producer_burst": burst,
        "producer_allowed_ticks": allowed_ticks,
        "producer_blocked_ticks": blocked_ticks,
        "produced_total": produced_total,
        "dispatched_total": dispatched_total,
        "final": final,
        "max_queued_after_production": max_queued_after_production,
        "max_queued_after_execution": max_queued_after_execution,
        "elapsed_seconds": elapsed,
        "completion_rate_per_minute": (final["completed"] / elapsed * 60.0) if elapsed > 0 else 0.0,
        "rows": rows,
        "pass": passed,
    }


def run_overload_recovery_scenario() -> dict:
    """
    Controlled overload:
      - 24 ticks with burst 120 when producer is allowed
      - verifies hard-stop activation above 300
      - then 20 recovery-only ticks with production disabled
    """
    scenario = "overload_recovery"
    queue = AutonomousTaskQueue(RUNTIME / "v69_4" / scenario / "task_queue")
    dispatcher = make_dispatcher(queue)
    bp = AdaptiveBackpressure(queue)
    bp.state_path = RUNTIME / "v69_4" / scenario / "adaptive_backpressure_state.json"
    ws = {}

    load_ticks = 24
    recovery_ticks = 20
    burst = 120

    rows = []
    produced_total = 0
    hard_stop_ticks = 0
    producer_blocked_ticks = 0
    producer_allowed_ticks = 0
    max_queue = 0

    start = time.perf_counter()

    for tick in range(1, load_ticks + 1):
        decision = bp.decide()
        gate = _producer_throttle_gate(decision, ws)

        produced = 0
        if gate["allow_producer"]:
            seed_direct(queue, count=burst, scenario=scenario, tick=tick)
            produced = burst
            produced_total += burst
            producer_allowed_ticks += 1
        else:
            producer_blocked_ticks += 1

        if gate["action"] == "backpressure_execution_first":
            hard_stop_ticks += 1

        before_exec = queue_counts(queue)
        max_queue = max(max_queue, before_exec["queued"])

        results = dispatcher.dispatch_batch(max_dispatches=int(decision["execution_batch"]))
        dispatched = sum(1 for x in results if x.dispatched)

        after = queue_counts(queue)
        max_queue = max(max_queue, after["queued"])

        rows.append({
            "phase": "load",
            "tick": tick,
            "producer_allowed": gate["allow_producer"],
            "producer_action": gate["action"],
            "producer_divisor": gate["producer_divisor"],
            "execution_batch": decision["execution_batch"],
            "produced": produced,
            "dispatched": dispatched,
            "queued_after_production": before_exec["queued"],
            "queued_after_execution": after["queued"],
            "failed": after["failed"],
        })

    end_load = queue_counts(queue)

    for i in range(1, recovery_ticks + 1):
        tick = load_ticks + i
        decision = bp.decide()

        # Recovery intentionally disables production to measure executor drain.
        before_exec = queue_counts(queue)
        results = dispatcher.dispatch_batch(max_dispatches=int(decision["execution_batch"]))
        dispatched = sum(1 for x in results if x.dispatched)
        after = queue_counts(queue)

        rows.append({
            "phase": "recovery",
            "tick": tick,
            "producer_allowed": False,
            "producer_action": "recovery_execution_only",
            "producer_divisor": decision["producer_divisor"],
            "execution_batch": decision["execution_batch"],
            "produced": 0,
            "dispatched": dispatched,
            "queued_after_production": before_exec["queued"],
            "queued_after_execution": after["queued"],
            "failed": after["failed"],
        })

        if after["queued"] == 0:
            break

    elapsed = time.perf_counter() - start
    final = queue_counts(queue)
    actual_recovery_ticks = sum(1 for x in rows if x["phase"] == "recovery")

    passed = all([
        produced_total > 0,
        hard_stop_ticks > 0,
        producer_blocked_ticks > 0,
        max_queue <= 500,
        end_load["queued"] <= 400,
        end_load["failed"] == 0,
        final["queued"] == 0,
        final["failed"] == 0,
        actual_recovery_ticks <= recovery_ticks,
    ])

    return {
        "scenario": scenario,
        "load_ticks": load_ticks,
        "recovery_ticks_budget": recovery_ticks,
        "recovery_ticks_used": actual_recovery_ticks,
        "producer_burst": burst,
        "producer_allowed_ticks": producer_allowed_ticks,
        "producer_blocked_ticks": producer_blocked_ticks,
        "hard_stop_ticks": hard_stop_ticks,
        "produced_total": produced_total,
        "end_load": end_load,
        "final": final,
        "max_queue": max_queue,
        "elapsed_seconds": elapsed,
        "completion_rate_per_minute": (final["completed"] / elapsed * 60.0) if elapsed > 0 else 0.0,
        "rows": rows,
        "pass": passed,
    }


sustainable = run_sustained_scenario()
overload = run_overload_recovery_scenario()

overall = sustainable["pass"] and overload["pass"]

report = {
    "schema": "companyos.v69_4.sustained_equilibrium_test.v1",
    "generated_at_unix": time.time(),
    "mode": "ISOLATED_REAL_CONTROLLER_REAL_QUEUE_REAL_INTERNAL_DISPATCH",
    "sustainable_load": sustainable,
    "overload_recovery": overload,
    "external_actions_performed": False,
    "financial_actions_performed": False,
    "email_actions_performed": False,
    "deployment_actions_performed": False,
    "real_companyos_queue_modified": False,
    "overall_status": "PASS" if overall else "FAIL",
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

lines = [
    "# CompanyOS V69.4 Sustained Producer/Executor Equilibrium Test",
    "",
    f"Overall status: **{report['overall_status']}**",
    "",
    "## Sustainable load",
    f"- Ticks: **{sustainable['ticks']}**",
    f"- Producer burst: **{sustainable['producer_burst']}**",
    f"- Producer allowed ticks: **{sustainable['producer_allowed_ticks']}**",
    f"- Producer blocked ticks: **{sustainable['producer_blocked_ticks']}**",
    f"- Produced total: **{sustainable['produced_total']}**",
    f"- Completed total: **{sustainable['final']['completed']}**",
    f"- Final queued: **{sustainable['final']['queued']}**",
    f"- Max queued after production: **{sustainable['max_queued_after_production']}**",
    f"- Max queued after execution: **{sustainable['max_queued_after_execution']}**",
    "",
    "## Overload + recovery",
    f"- Load ticks: **{overload['load_ticks']}**",
    f"- Hard-stop ticks: **{overload['hard_stop_ticks']}**",
    f"- Max queue: **{overload['max_queue']}**",
    f"- Queue at end of load: **{overload['end_load']['queued']}**",
    f"- Recovery ticks used: **{overload['recovery_ticks_used']}**",
    f"- Final queued: **{overload['final']['queued']}**",
    f"- Final failed: **{overload['final']['failed']}**",
    "",
    "The benchmark runs in an isolated temporary HOME and does not modify the real CompanyOS queue.",
    "No external research, email, deployment, transaction, or financial action is performed.",
]
OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(json.dumps({
    "overall_status": report["overall_status"],
    "sustainable": {
        "pass": sustainable["pass"],
        "producer_allowed_ticks": sustainable["producer_allowed_ticks"],
        "producer_blocked_ticks": sustainable["producer_blocked_ticks"],
        "produced_total": sustainable["produced_total"],
        "completed_total": sustainable["final"]["completed"],
        "final_queued": sustainable["final"]["queued"],
        "max_queued_after_production": sustainable["max_queued_after_production"],
        "max_queued_after_execution": sustainable["max_queued_after_execution"],
    },
    "overload_recovery": {
        "pass": overload["pass"],
        "producer_allowed_ticks": overload["producer_allowed_ticks"],
        "producer_blocked_ticks": overload["producer_blocked_ticks"],
        "hard_stop_ticks": overload["hard_stop_ticks"],
        "produced_total": overload["produced_total"],
        "max_queue": overload["max_queue"],
        "end_load_queued": overload["end_load"]["queued"],
        "recovery_ticks_used": overload["recovery_ticks_used"],
        "final_queued": overload["final"]["queued"],
        "final_failed": overload["final"]["failed"],
    },
}, indent=2, sort_keys=True))
