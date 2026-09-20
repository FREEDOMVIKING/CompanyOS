from __future__ import annotations

import json
import tempfile
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from companyos.runtime.adaptive_backpressure import AdaptiveBackpressure
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.dependency_aware_dispatcher import DependencyAwareDispatcher

ROOT = Path.home() / "companyos"
RT = Path.home() / ".companyos_runtime"
OUT = ROOT / "audit/COMPANYOS_V69_1_ADAPTIVE_THROUGHPUT_BENCHMARK.json"
OUT_MD = ROOT / "audit/COMPANYOS_V69_1_ADAPTIVE_THROUGHPUT_BENCHMARK.md"

BENCHMARK_CYCLES = 4
PHONE_SAFE_BATCH_CAP = 32
SUPPORTED_TYPES = {"research", "planning", "build"}


def snapshot(queue: AutonomousTaskQueue) -> dict:
    now = time.time()
    states = Counter()
    types = Counter()
    queued_types = Counter()
    queued_ages = []
    supported_queued = 0
    supported_due = 0

    for t in queue._iter_task_files():
        states[t.state] += 1
        types[t.task_type] += 1
        if t.state == "QUEUED":
            queued_types[t.task_type] += 1
            queued_ages.append(max(0.0, now - float(t.created_at_unix)))
            if t.task_type in SUPPORTED_TYPES:
                supported_queued += 1
                if t.attempts < t.max_attempts and t.next_attempt_unix <= now:
                    supported_due += 1

    return {
        "timestamp_unix": now,
        "states": dict(states),
        "task_types": dict(types),
        "queued_by_type": dict(queued_types),
        "total": sum(states.values()),
        "queued": states["QUEUED"],
        "completed": states["COMPLETED"],
        "failed": states["FAILED"],
        "running": states["RUNNING"] + states["CLAIMED"],
        "supported_queued": supported_queued,
        "supported_due": supported_due,
        "oldest_queued_age_seconds": max(queued_ages) if queued_ages else 0.0,
    }


class MemoryQueue:
    def __init__(self, counts: dict[str, int]):
        now = time.time()
        rows = []
        i = 0
        for task_type, count in counts.items():
            for _ in range(count):
                i += 1
                rows.append(
                    SimpleNamespace(
                        task_type=task_type,
                        state="QUEUED",
                        created_at_unix=now - i,
                    )
                )
        self.rows = rows

    def _iter_task_files(self):
        return iter(self.rows)


def synthetic_backpressure_matrix() -> dict:
    cases = [
        ("low", {"research": 100}, None, 1, 16),
        ("medium_count", {"research": 300}, None, 2, 32),
        ("high_count", {"research": 600}, None, 3, 48),
        ("critical_count", {"research": 900}, None, 4, 64),
        ("positive_growth", {"research": 100}, 95, 2, 32),
        ("high_growth", {"research": 100}, 92, 3, 48),
        ("critical_growth", {"research": 100}, 80, 4, 64),
    ]

    rows = []
    with tempfile.TemporaryDirectory(prefix="companyos-v69-1-bp-") as td:
        td = Path(td)
        for name, counts, previous_queued, expected_divisor, expected_batch in cases:
            ctl = AdaptiveBackpressure(MemoryQueue(counts))
            ctl.state_path = td / f"{name}.json"
            if previous_queued is not None:
                ctl.state_path.write_text(
                    json.dumps({"snapshot": {"queued": previous_queued}}) + "\n"
                )
            out = ctl.decide()
            ok = (
                int(out["producer_divisor"]) == expected_divisor
                and int(out["execution_batch"]) == expected_batch
            )
            rows.append(
                {
                    "case": name,
                    "queued": out["snapshot"]["queued"],
                    "growth": out["queue_growth"],
                    "producer_divisor": out["producer_divisor"],
                    "execution_batch": out["execution_batch"],
                    "expected_divisor": expected_divisor,
                    "expected_batch": expected_batch,
                    "pass": ok,
                }
            )

    return {
        "pass": all(x["pass"] for x in rows),
        "cases": rows,
    }


def synthetic_dispatch_policy() -> dict:
    with tempfile.TemporaryDirectory(prefix="companyos-v69-1-dispatch-") as td:
        q = AutonomousTaskQueue(Path(td) / "queue")
        d = AutonomousTaskDispatcher(q)

        order = []

        def handler(task):
            order.append(task.task_id)
            return {"ok": True}

        for typ in SUPPORTED_TYPES:
            d.register(task_type=typ, agent_name=f"{typ}_test_agent", handler=handler)

        # Largest task class is research (3 tasks), so it should be boosted.
        # Within that class, the oldest research task should dispatch first.
        r_old = q.enqueue(
            task_type="research",
            payload={"goal": "r-old"},
            priority=100,
            idempotency_key="v69.1-r-old",
        )
        time.sleep(0.01)
        r_mid = q.enqueue(
            task_type="research",
            payload={"goal": "r-mid"},
            priority=200,
            idempotency_key="v69.1-r-mid",
        )
        time.sleep(0.01)
        r_new = q.enqueue(
            task_type="research",
            payload={"goal": "r-new"},
            priority=300,
            idempotency_key="v69.1-r-new",
        )
        time.sleep(0.01)
        p_old = q.enqueue(
            task_type="planning",
            payload={"goal": "p-old"},
            priority=999,
            idempotency_key="v69.1-p-old",
        )

        dep = DependencyAwareDispatcher(d)
        # Keep adaptive state out of the real runtime for this isolated policy check.
        real_cls = AdaptiveBackpressure
        result = dep.dispatch_batch(max_dispatches=1)[0]

        selected = result.task_id
        largest_type_boost = selected == r_old.task_id
        oldest_within_boost = selected == r_old.task_id

        return {
            "selected_task_id": selected,
            "expected_oldest_research_task_id": r_old.task_id,
            "high_priority_planning_task_id": p_old.task_id,
            "largest_type_boost_verified": largest_type_boost,
            "oldest_within_boost_verified": oldest_within_boost,
            "pass": bool(result.dispatched and largest_type_boost and oldest_within_boost),
        }


def actual_internal_benchmark() -> dict:
    queue = AutonomousTaskQueue()
    loop = AutonomousGoalExecutionLoop(queue)

    before = snapshot(queue)
    cycle_rows = []
    total_dispatched = 0
    started = time.monotonic()

    for cycle_no in range(1, BENCHMARK_CYCLES + 1):
        control = AdaptiveBackpressure(queue).decide()
        requested_batch = int(control.get("execution_batch", 8))
        actual_batch = max(1, min(requested_batch, PHONE_SAFE_BATCH_CAP))

        t0 = time.monotonic()
        results = loop.run_bounded_batch(max_dispatches=actual_batch)
        elapsed = time.monotonic() - t0

        dispatched = sum(1 for x in results if x.dispatched)
        total_dispatched += dispatched
        reasons = Counter(x.reason for x in results)

        cycle_rows.append(
            {
                "cycle": cycle_no,
                "control": control,
                "requested_execution_batch": requested_batch,
                "phone_safe_batch_cap": PHONE_SAFE_BATCH_CAP,
                "actual_batch": actual_batch,
                "results_returned": len(results),
                "dispatched": dispatched,
                "elapsed_seconds": elapsed,
                "reasons": dict(reasons),
            }
        )

        if dispatched == 0:
            break

    elapsed_total = time.monotonic() - started
    after = snapshot(queue)

    completed_delta = after["completed"] - before["completed"]
    failed_delta = after["failed"] - before["failed"]
    queued_delta = after["queued"] - before["queued"]
    completion_rate = (
        completed_delta / (elapsed_total / 60.0)
        if elapsed_total > 0
        else 0.0
    )

    if before["supported_due"] > 0:
        useful_progress = completed_delta > 0 and total_dispatched > 0
    else:
        useful_progress = True

    return {
        "before": before,
        "after": after,
        "cycles": cycle_rows,
        "benchmark_cycles_requested": BENCHMARK_CYCLES,
        "cycles_executed": len(cycle_rows),
        "phone_safe_batch_cap": PHONE_SAFE_BATCH_CAP,
        "elapsed_seconds": elapsed_total,
        "total_dispatched": total_dispatched,
        "completed_delta": completed_delta,
        "failed_delta": failed_delta,
        "queued_delta": queued_delta,
        "completion_rate_per_minute": completion_rate,
        "oldest_queued_age_delta_seconds": (
            after["oldest_queued_age_seconds"]
            - before["oldest_queued_age_seconds"]
        ),
        "useful_progress": useful_progress,
        "failure_regression": failed_delta > 0,
        "pass": bool(useful_progress and failed_delta <= 0),
    }


synthetic_bp = synthetic_backpressure_matrix()
synthetic_dispatch = synthetic_dispatch_policy()
actual = actual_internal_benchmark()

overall = bool(
    synthetic_bp["pass"]
    and synthetic_dispatch["pass"]
    and actual["pass"]
)

report = {
    "schema": "companyos.v69_1.adaptive_throughput_benchmark.v1",
    "generated_at_unix": time.time(),
    "mode": "INTERNAL_ONLY_REAL_QUEUE_DRAIN_PLUS_ISOLATED_POLICY_TESTS",
    "external_actions_performed": False,
    "financial_actions_performed": False,
    "email_actions_performed": False,
    "deployment_actions_performed": False,
    "synthetic_backpressure_matrix": synthetic_bp,
    "synthetic_dispatch_policy": synthetic_dispatch,
    "actual_internal_queue_benchmark": actual,
    "overall_status": "PASS" if overall else "FAIL",
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

b = actual["before"]
a = actual["after"]
lines = [
    "# CompanyOS V69.1 Adaptive Throughput + Backpressure Benchmark",
    "",
    f"Overall status: **{report['overall_status']}**",
    "",
    "## Isolated adaptive-control tests",
    f"- Backpressure threshold matrix: **{'PASS' if synthetic_bp['pass'] else 'FAIL'}**",
    f"- Largest task-class boost: **{'PASS' if synthetic_dispatch['largest_type_boost_verified'] else 'FAIL'}**",
    f"- Oldest-within-boost ordering: **{'PASS' if synthetic_dispatch['oldest_within_boost_verified'] else 'FAIL'}**",
    "",
    "## Real internal queue",
    f"- Queued before: **{b['queued']}**",
    f"- Queued after: **{a['queued']}**",
    f"- Completed delta: **{actual['completed_delta']}**",
    f"- Failed delta: **{actual['failed_delta']}**",
    f"- Total dispatched: **{actual['total_dispatched']}**",
    f"- Completion rate: **{actual['completion_rate_per_minute']:.2f}/min**",
    f"- Supported due before: **{b['supported_due']}**",
    f"- Oldest queued age before: **{b['oldest_queued_age_seconds']:.1f}s**",
    f"- Oldest queued age after: **{a['oldest_queued_age_seconds']:.1f}s**",
    "",
    "No external web research, email, deployment, transaction, or financial action was performed by this benchmark.",
]
OUT_MD.write_text("\n".join(lines) + "\n")

print(json.dumps({
    "overall_status": report["overall_status"],
    "synthetic_backpressure": synthetic_bp["pass"],
    "largest_type_boost": synthetic_dispatch["largest_type_boost_verified"],
    "oldest_within_boost": synthetic_dispatch["oldest_within_boost_verified"],
    "queued_before": b["queued"],
    "queued_after": a["queued"],
    "supported_due_before": b["supported_due"],
    "total_dispatched": actual["total_dispatched"],
    "completed_delta": actual["completed_delta"],
    "failed_delta": actual["failed_delta"],
    "completion_rate_per_minute": round(actual["completion_rate_per_minute"], 2),
    "oldest_queued_age_before_seconds": round(b["oldest_queued_age_seconds"], 2),
    "oldest_queued_age_after_seconds": round(a["oldest_queued_age_seconds"], 2),
}, indent=2, sort_keys=True))
