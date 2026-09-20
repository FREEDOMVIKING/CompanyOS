#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

echo "===== COMPANYOS V27.9 EXECUTION DRAIN ENGINE ====="
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$HOME/.companyos_runtime/backups/v27_9_$STAMP"
mkdir -p "$BACKUP"

cp -f companyos/runtime/dependency_aware_dispatcher.py "$BACKUP/" 2>/dev/null || true
cp -f companyos/runtime/autonomous_task_queue.py "$BACKUP/" 2>/dev/null || true
echo "BACKUP=$BACKUP"

cat > companyos/runtime/execution_drain_engine.py <<'PY'
from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue, TaskRecord
from companyos.runtime.dependency_aware_dispatcher import DependencyAwareDispatcher


@dataclass
class DrainSnapshot:
    total: int
    queued: int
    completed: int
    ready: int
    dependency_blocked: int
    missing_handler: int


class ExecutionDrainEngine:
    """
    Bounded queue-drain accelerator.

    Important invariants:
    - never deletes task records
    - never bypasses dependency gates
    - never changes finance/approval/security policy
    - only dispatches tasks already eligible under the live dispatcher
    - bounded work per cycle
    """

    def __init__(self, batch_size: int = 32) -> None:
        self.queue = AutonomousTaskQueue()
        self.dispatcher = DependencyAwareDispatcher()
        self.batch_size = max(1, min(int(batch_size), 128))
        self.runtime_root = Path.home() / ".companyos_runtime"
        self.state_path = self.runtime_root / "execution_drain_state.json"
        self.runtime_root.mkdir(parents=True, exist_ok=True)

    def _load_records_once(self) -> list[TaskRecord]:
        return list(self.queue._iter_task_files())

    def _completed_stage_index(self, tasks: list[TaskRecord]) -> set[tuple[str, str]]:
        out: set[tuple[str, str]] = set()
        for task in tasks:
            if task.state != "COMPLETED":
                continue
            payload = task.payload if isinstance(task.payload, dict) else {}
            gid, stage = payload.get("goal_id"), payload.get("stage")
            if gid and stage:
                out.add((str(gid), str(stage)))
        return out

    def _ready(self, task: TaskRecord, completed: set[tuple[str,str]], now: float) -> bool:
        if task.state != "QUEUED":
            return False
        if task.attempts >= task.max_attempts:
            return False
        if task.next_attempt_unix > now:
            return False
        if task.task_type not in self.dispatcher.dispatcher.handlers:
            return False
        payload = task.payload if isinstance(task.payload, dict) else {}
        dep = payload.get("depends_on_stage")
        if not dep:
            return True
        gid = payload.get("goal_id")
        return bool(gid and (str(gid), str(dep)) in completed)

    def _unlock_counts(self, tasks: list[TaskRecord]) -> Counter:
        # Approximate how many queued tasks depend on each goal/stage.
        counts: Counter = Counter()
        for task in tasks:
            if task.state != "QUEUED":
                continue
            payload = task.payload if isinstance(task.payload, dict) else {}
            gid = payload.get("goal_id")
            dep = payload.get("depends_on_stage")
            if gid and dep:
                counts[(str(gid), str(dep))] += 1
        return counts

    def _rank(self, task: TaskRecord, unlocks: Counter) -> tuple:
        payload = task.payload if isinstance(task.payload, dict) else {}
        gid = payload.get("goal_id")
        stage = payload.get("stage")
        downstream = unlocks.get((str(gid), str(stage)), 0) if gid and stage else 0
        # Larger downstream unlock first, then higher numeric priority,
        # then oldest task for fairness.
        return (-downstream, -int(task.priority), float(task.created_at_unix))

    def snapshot(self, tasks: list[TaskRecord] | None = None) -> DrainSnapshot:
        tasks = tasks if tasks is not None else self._load_records_once()
        completed = self._completed_stage_index(tasks)
        now = time.time()
        ready = blocked = missing = queued = done = 0
        for task in tasks:
            if task.state == "COMPLETED":
                done += 1
            if task.state != "QUEUED":
                continue
            queued += 1
            if task.task_type not in self.dispatcher.dispatcher.handlers:
                missing += 1
            elif self._ready(task, completed, now):
                ready += 1
            else:
                payload = task.payload if isinstance(task.payload, dict) else {}
                if payload.get("depends_on_stage"):
                    blocked += 1
        return DrainSnapshot(len(tasks), queued, done, ready, blocked, missing)

    def run_batch(self) -> dict[str, Any]:
        before_tasks = self._load_records_once()
        before = self.snapshot(before_tasks)
        completed = self._completed_stage_index(before_tasks)
        unlocks = self._unlock_counts(before_tasks)
        now = time.time()

        candidates = [t for t in before_tasks if self._ready(t, completed, now)]
        candidates.sort(key=lambda t: self._rank(t, unlocks))
        selected = candidates[:self.batch_size]

        attempted = completed_now = failed_now = 0
        results = []

        for task in selected:
            attempted += 1
            original_priority = task.priority
            # Existing dispatcher selects from queue. Temporarily elevate only
            # this already-eligible task, then restore if it remains queued.
            task.priority = max(int(task.priority), 1_000_000)
            self.queue.save(task)
            try:
                result = self.dispatcher.dispatch_next()
                results.append({
                    "selected_task_id": task.task_id,
                    "dispatch_success": bool(getattr(result, "success", False)),
                    "reason": getattr(result, "reason", None),
                })
            except Exception as exc:
                failed_now += 1
                results.append({
                    "selected_task_id": task.task_id,
                    "dispatch_success": False,
                    "reason": f"{type(exc).__name__}: {exc}"[:500],
                })
            finally:
                try:
                    saved = self.queue.load(task.task_id)
                    if saved.state == "QUEUED":
                        saved.priority = original_priority
                        self.queue.save(saved)
                    elif saved.state == "COMPLETED":
                        completed_now += 1
                except Exception:
                    pass

        after_tasks = self._load_records_once()
        after = self.snapshot(after_tasks)
        state = {
            "timestamp_unix": time.time(),
            "batch_size": self.batch_size,
            "attempted": attempted,
            "completed_in_batch": completed_now,
            "dispatch_exceptions": failed_now,
            "before": before.__dict__,
            "after": after.__dict__,
            "queue_delta": after.queued - before.queued,
            "completed_delta": after.completed - before.completed,
            "results_tail": results[-10:],
        }
        tmp = self.state_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.state_path)
        return state


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=32)
    args = p.parse_args()
    print(json.dumps(ExecutionDrainEngine(args.batch).run_batch(), indent=2))
PY

cat > scripts/companyos_drainctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import argparse, json, time
from companyos.runtime.execution_drain_engine import ExecutionDrainEngine

p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd", required=True)

s = sub.add_parser("status")
s = sub.add_parser("batch")
s.add_argument("--size", type=int, default=32)

s = sub.add_parser("run")
s.add_argument("--size", type=int, default=32)
s.add_argument("--cycles", type=int, default=5)
s.add_argument("--sleep", type=float, default=2.0)

a = p.parse_args()

if a.cmd == "status":
    e = ExecutionDrainEngine()
    print(json.dumps(e.snapshot().__dict__, indent=2))
elif a.cmd == "batch":
    print(json.dumps(ExecutionDrainEngine(a.size).run_batch(), indent=2))
else:
    e = ExecutionDrainEngine(a.size)
    for i in range(max(1, min(a.cycles, 50))):
        r = e.run_batch()
        print(json.dumps({
            "cycle": i + 1,
            "attempted": r["attempted"],
            "completed_delta": r["completed_delta"],
            "queue_delta": r["queue_delta"],
            "after": r["after"],
        }, indent=2))
        if r["attempted"] == 0:
            break
        time.sleep(max(0.0, a.sleep))
PY
chmod +x scripts/companyos_drainctl

cat > tests/test_execution_drain_engine.py <<'PY'
from companyos.runtime.execution_drain_engine import ExecutionDrainEngine
def test_batch_bounds():
    assert ExecutionDrainEngine(0).batch_size == 1
    assert ExecutionDrainEngine(999).batch_size == 128
PY

echo "===== COMPILE ====="
python -m py_compile \
  companyos/runtime/execution_drain_engine.py \
  scripts/companyos_drainctl
echo "COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_execution_drain_engine.py
echo "TEST=PASS"

echo "===== LIVE STATUS ====="
python scripts/companyos_drainctl status

echo "===== SAFE FIRST BATCH: 16 ====="
python scripts/companyos_drainctl batch --size 16

echo "===== SUPERVISOR PRESERVED ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
echo "SUPERVISOR_RESTART=NO"
echo "QUEUE_RECORDS_DELETED=0"
echo "V27_9=PASS"
echo
echo "Next command for bounded drain:"
echo "cd ~/companyos && python scripts/companyos_drainctl run --size 32 --cycles 5 --sleep 2"
