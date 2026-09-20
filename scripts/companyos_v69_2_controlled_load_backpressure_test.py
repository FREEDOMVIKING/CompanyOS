from __future__ import annotations

import hashlib
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

REPO = Path(os.environ["COMPANYOS_REPO_ROOT"]).resolve()
TMPHOME = Path.home().resolve()
RUNTIME = TMPHOME / ".companyos_runtime"
OUT = REPO / "audit/COMPANYOS_V69_2_CONTROLLED_LOAD_BACKPRESSURE_TEST.json"
OUT_MD = REPO / "audit/COMPANYOS_V69_2_CONTROLLED_LOAD_BACKPRESSURE_TEST.md"

TIERS = [
    ("LOW", 100, 1, 16),
    ("MEDIUM", 300, 2, 32),
    ("HIGH", 600, 3, 48),
    ("CRITICAL", 900, 4, 64),
]


def safe_source_refs(token: str) -> list[str]:
    hits = []
    excluded = (
        ".git/",
        "audit/",
        "tests/",
        "ops/patch_history/",
        "backups/",
        "workspace/",
    )
    for p in REPO.rglob("*.py"):
        rel = p.relative_to(REPO).as_posix()
        if rel.startswith(excluded):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if token in text:
            hits.append(rel)
    return sorted(set(hits))


def seed_queue(queue: AutonomousTaskQueue, count: int) -> Counter:
    queue.root.mkdir(parents=True, exist_ok=True)
    dist = Counter()
    now = time.time()

    # Make research the largest task class so boost behavior is measurable.
    type_cycle = ["research"] * 6 + ["planning"] * 3 + ["build"]

    for i in range(count):
        task_type = type_cycle[i % len(type_cycle)]
        dist[task_type] += 1
        created = now - (count - i) * 0.001
        task_id = f"v69-2-{count}-{i:05d}-{uuid.uuid4().hex[:8]}"
        payload = {
            "goal_id": f"v69-2-load-{count}",
            "goal": f"controlled internal benchmark {count} task {i}",
            "topic": f"controlled internal benchmark {count} task {i}",
            "name": f"controlled internal benchmark {count} task {i}",
            "internal_only": True,
            "benchmark": "V69.2",
        }
        rec = TaskRecord(
            task_id=task_id,
            idempotency_key=f"v69.2:{count}:{i}",
            task_type=task_type,
            priority=100 + (i % 7),
            payload=payload,
            state="QUEUED",
            assigned_agent=None,
            attempts=0,
            max_attempts=3,
            created_at_unix=created,
            updated_at_unix=created,
            next_attempt_unix=created,
            result=None,
            last_error=None,
        )
        # Direct seed avoids turning benchmark setup itself into an
        # idempotency/indexing benchmark. Live dispatch still uses queue.load/save.
        path = queue.root / f"{rec.task_id}.json"
        path.write_text(json.dumps(asdict(rec), sort_keys=True) + "\n", encoding="utf-8")
    return dist


def counts(queue: AutonomousTaskQueue) -> dict:
    c = Counter()
    by_type = Counter()
    for t in queue._iter_task_files():
        c[t.state] += 1
        if t.state == "QUEUED":
            by_type[t.task_type] += 1
    return {
        "states": dict(c),
        "queued_by_type": dict(by_type),
        "queued": c["QUEUED"],
        "completed": c["COMPLETED"],
        "failed": c["FAILED"],
        "running": c["RUNNING"] + c["CLAIMED"],
    }


def run_tier(name: str, load: int, expected_divisor: int, expected_batch: int) -> dict:
    tier_root = RUNTIME / "v69_2" / name.lower()
    queue = AutonomousTaskQueue(tier_root / "task_queue")
    distribution = seed_queue(queue, load)

    control = AdaptiveBackpressure(queue)
    control.state_path = tier_root / "adaptive_backpressure_state.json"
    decision = control.decide()

    before = counts(queue)

    base = AutonomousTaskDispatcher(queue)
    register_default_specialists(base)
    dispatcher = DependencyAwareDispatcher(base)

    started = time.perf_counter()
    results = dispatcher.dispatch_batch(max_dispatches=int(decision["execution_batch"]))
    elapsed = time.perf_counter() - started

    after = counts(queue)
    dispatched = sum(1 for x in results if x.dispatched)
    completed_delta = after["completed"] - before["completed"]
    failed_delta = after["failed"] - before["failed"]
    queued_delta = after["queued"] - before["queued"]
    rate_per_second = completed_delta / elapsed if elapsed > 0 else 0.0

    # All tasks were independent and valid. A full selected batch should complete.
    passed = all([
        int(decision["snapshot"]["queued"]) == load,
        int(decision["producer_divisor"]) == expected_divisor,
        int(decision["execution_batch"]) == expected_batch,
        decision["boost_type"] == "research",
        dispatched == expected_batch,
        completed_delta == expected_batch,
        failed_delta == 0,
        queued_delta == -expected_batch,
    ])

    return {
        "tier": name,
        "load": load,
        "seed_distribution": dict(distribution),
        "expected_producer_divisor": expected_divisor,
        "expected_execution_batch": expected_batch,
        "decision": decision,
        "before": before,
        "after": after,
        "results_returned": len(results),
        "dispatched": dispatched,
        "completed_delta": completed_delta,
        "failed_delta": failed_delta,
        "queued_delta": queued_delta,
        "elapsed_seconds": elapsed,
        "completion_rate_per_second": rate_per_second,
        "completion_rate_per_minute": rate_per_second * 60.0,
        "pass": passed,
    }


producer_refs = safe_source_refs("producer_divisor")
batch_refs = safe_source_refs("execution_batch")

producer_definition = "companyos/runtime/adaptive_backpressure.py"
producer_consumers = [x for x in producer_refs if x != producer_definition]
batch_consumers = [x for x in batch_refs if x != producer_definition]

tiers = [run_tier(*spec) for spec in TIERS]

load_scaling_pass = all(t["pass"] for t in tiers)
producer_throttle_wired = bool(producer_consumers)
execution_batch_wired = bool(batch_consumers)

if load_scaling_pass and producer_throttle_wired and execution_batch_wired:
    status = "PASS"
elif load_scaling_pass and execution_batch_wired and not producer_throttle_wired:
    status = "PASS_WITH_PRODUCER_THROTTLE_GAP"
else:
    status = "FAIL"

report = {
    "schema": "companyos.v69_2.controlled_load_backpressure_test.v1",
    "generated_at_unix": time.time(),
    "mode": "ISOLATED_TEMP_HOME_REAL_QUEUE_AND_REAL_INTERNAL_SPECIALISTS",
    "temporary_home": str(TMPHOME),
    "load_scaling_pass": load_scaling_pass,
    "producer_divisor_source_refs": producer_refs,
    "producer_divisor_consumers": producer_consumers,
    "producer_throttle_wired": producer_throttle_wired,
    "execution_batch_source_refs": batch_refs,
    "execution_batch_consumers": batch_consumers,
    "execution_batch_wired": execution_batch_wired,
    "tiers": tiers,
    "external_actions_performed": False,
    "financial_actions_performed": False,
    "email_actions_performed": False,
    "deployment_actions_performed": False,
    "real_companyos_queue_modified": False,
    "overall_status": status,
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

lines = [
    "# CompanyOS V69.2 Controlled Load + Backpressure Wiring Test",
    "",
    f"Overall status: **{status}**",
    f"Load scaling: **{'PASS' if load_scaling_pass else 'FAIL'}**",
    f"Execution batch consumer present: **{execution_batch_wired}**",
    f"Producer divisor consumer present: **{producer_throttle_wired}**",
    "",
    "## Controlled load tiers",
]
for t in tiers:
    lines += [
        f"- {t['tier']} ({t['load']} queued): "
        f"divisor={t['decision']['producer_divisor']}, "
        f"batch={t['decision']['execution_batch']}, "
        f"completed={t['completed_delta']}, "
        f"failed={t['failed_delta']}, "
        f"rate={t['completion_rate_per_minute']:.1f}/min, "
        f"status={'PASS' if t['pass'] else 'FAIL'}"
    ]

lines += [
    "",
    "## Wiring",
    "- `execution_batch` references: " + ", ".join(batch_refs),
    "- `producer_divisor` references: " + ", ".join(producer_refs),
    "",
    "The benchmark uses an isolated temporary HOME and does not modify the real CompanyOS task queue.",
    "No external web research, email, deployment, transaction, or financial action is performed.",
]
OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(json.dumps({
    "overall_status": status,
    "load_scaling_pass": load_scaling_pass,
    "execution_batch_wired": execution_batch_wired,
    "producer_throttle_wired": producer_throttle_wired,
    "producer_divisor_consumers": producer_consumers,
    "tiers": [
        {
            "tier": t["tier"],
            "load": t["load"],
            "producer_divisor": t["decision"]["producer_divisor"],
            "execution_batch": t["decision"]["execution_batch"],
            "boost_type": t["decision"]["boost_type"],
            "dispatched": t["dispatched"],
            "completed_delta": t["completed_delta"],
            "failed_delta": t["failed_delta"],
            "completion_rate_per_minute": round(t["completion_rate_per_minute"], 2),
            "pass": t["pass"],
        }
        for t in tiers
    ],
}, indent=2, sort_keys=True))
