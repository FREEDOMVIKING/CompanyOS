#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACK="$HOME/.companyos_runtime/backups/v28_3_$STAMP"
mkdir -p "$BACK/companyos/runtime"

FILES=(
  companyos/runtime/dependency_aware_dispatcher.py
  companyos/runtime/autonomous_goal_execution_loop.py
)

for f in "${FILES[@]}"; do
  cp -a "$f" "$BACK/$f"
done

restore() {
  echo "V28.3_FAIL_RESTORING_BACKUP"
  for f in "${FILES[@]}"; do
    cp -a "$BACK/$f" "$f"
  done
}
trap restore ERR

cat > companyos/runtime/dependency_aware_dispatcher.py <<'PY'
from __future__ import annotations

import os
import time

from companyos.runtime.autonomous_task_dispatcher import (
    AutonomousTaskDispatcher,
    DispatchResult,
)


class DependencyAwareDispatcher:
    """
    Dependency-aware exact dispatcher.

    V28.3 removes the O(window * entire_queue) dependency scan. A completed
    (goal_id, stage) index is built once per bounded batch and updated as
    tasks complete.
    """

    def __init__(self, dispatcher: AutonomousTaskDispatcher) -> None:
        self.dispatcher = dispatcher
        self.queue = dispatcher.queue

    @staticmethod
    def _payload(task):
        return task.payload if isinstance(task.payload, dict) else {}

    def _completed_stage_index(self) -> set[tuple[str, str]]:
        done: set[tuple[str, str]] = set()
        for task in self.queue._iter_task_files():
            if task.state != "COMPLETED":
                continue
            payload = self._payload(task)
            goal_id = payload.get("goal_id")
            stage = payload.get("stage")
            if goal_id and stage:
                done.add((str(goal_id), str(stage)))
        return done

    def _dependency_satisfied_with_index(
        self,
        task,
        completed: set[tuple[str, str]],
    ) -> bool:
        payload = self._payload(task)
        dep = payload.get("depends_on_stage")
        if not dep:
            return True
        goal_id = payload.get("goal_id")
        return bool(goal_id) and (str(goal_id), str(dep)) in completed

    def _window(self, limit: int):
        cursor_path = self.queue.root.parent / "dispatcher_scan_cursor.txt"
        try:
            cursor = int(cursor_path.read_text().strip()) if cursor_path.exists() else 0
        except Exception:
            cursor = 0

        source = self.queue.bounded_candidates_window(limit, cursor)
        total = sum(1 for _ in self.queue.root.glob("*.json"))
        try:
            cursor_path.write_text(str((cursor + limit) % max(1, total)))
        except Exception:
            pass
        return source

    def dispatch_batch(self, max_dispatches: int = 8) -> list[DispatchResult]:
        max_dispatches = max(1, min(int(max_dispatches), 64))
        scan_limit = max(
            max_dispatches * 16,
            int(os.getenv("COMPANYOS_QUEUE_SCAN_LIMIT", "1000")),
        )

        now = time.time()
        completed = self._completed_stage_index()
        source = self._window(scan_limit)

        candidates = [
            t
            for t in source
            if t.state == "QUEUED"
            and t.attempts < t.max_attempts
            and t.next_attempt_unix <= now
            and t.task_type in self.dispatcher.handlers
        ]
        candidates.sort(
            key=lambda t: (-int(t.priority), float(t.created_at_unix), t.task_id)
        )

        results: list[DispatchResult] = []
        remaining = list(candidates)

        while remaining and len(results) < max_dispatches:
            chosen_index = None
            for i, task in enumerate(remaining):
                if self._dependency_satisfied_with_index(task, completed):
                    chosen_index = i
                    break

            if chosen_index is None:
                break

            task = remaining.pop(chosen_index)
            result = self.dispatcher.dispatch_task(task)
            results.append(result)

            if result.dispatched and result.reason == "completed":
                payload = self._payload(task)
                goal_id = payload.get("goal_id")
                stage = payload.get("stage")
                if goal_id and stage:
                    completed.add((str(goal_id), str(stage)))

        if not results:
            results.append(
                DispatchResult(
                    False,
                    None,
                    None,
                    None,
                    "no_dependency_ready_task",
                    None,
                )
            )
        return results

    def dispatch_next(self) -> DispatchResult:
        return self.dispatch_batch(max_dispatches=1)[0]
PY

cat > companyos/runtime/autonomous_goal_execution_loop.py <<'PY'
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.default_specialist_registry import register_default_specialists
from companyos.runtime.dependency_aware_dispatcher import DependencyAwareDispatcher


@dataclass(frozen=True)
class GoalLoopCycleResult:
    dispatched: bool
    task_id: Optional[str]
    agent_name: Optional[str]
    state: Optional[str]
    reason: str
    completed_tasks: int
    failed_tasks: int
    queued_tasks: int
    running_tasks: int


class AutonomousGoalExecutionLoop:
    """
    Continuous dependency-ready execution loop.

    V28.3 performs stale recovery once per batch, dependency indexing once per
    batch, and queue counting once per batch instead of once per task.
    """

    def __init__(self, queue: AutonomousTaskQueue | None = None) -> None:
        self.queue = queue or AutonomousTaskQueue()
        base_dispatcher = AutonomousTaskDispatcher(self.queue)
        register_default_specialists(base_dispatcher)
        required = {"research", "planning", "build"}
        missing = sorted(required.difference(base_dispatcher.handlers))
        if missing:
            raise RuntimeError(
                "missing_default_specialist_handlers:" + ",".join(missing)
            )
        self.dispatcher = DependencyAwareDispatcher(base_dispatcher)

    def _counts(self):
        completed = failed = queued = running = 0
        for task in self.queue._iter_task_files():
            if task.state == "COMPLETED":
                completed += 1
            elif task.state == "FAILED":
                failed += 1
            elif task.state == "QUEUED":
                queued += 1
            elif task.state in ("CLAIMED", "RUNNING"):
                running += 1
        return completed, failed, queued, running

    @staticmethod
    def _to_cycle(result, counts):
        completed, failed, queued, running = counts
        return GoalLoopCycleResult(
            dispatched=result.dispatched,
            task_id=result.task_id,
            agent_name=result.agent_name,
            state=result.state,
            reason=result.reason,
            completed_tasks=completed,
            failed_tasks=failed,
            queued_tasks=queued,
            running_tasks=running,
        )

    def cycle(self) -> GoalLoopCycleResult:
        return self.run_bounded_batch(max_dispatches=1)[0]

    def run_bounded_batch(self, *, max_dispatches: int = 8):
        # One stale scan per batch, not once per task.
        self.queue.recover_stale(stale_after_seconds=300)

        raw = self.dispatcher.dispatch_batch(max_dispatches=max_dispatches)

        # One count scan per batch, not once per task.
        counts = self._counts()
        return [self._to_cycle(result, counts) for result in raw]

    def run_until_idle(
        self,
        *,
        max_cycles: int = 100,
        sleep_seconds: float = 0.0,
    ) -> list[GoalLoopCycleResult]:
        results = []
        for _ in range(max(1, int(max_cycles))):
            batch = self.run_bounded_batch(max_dispatches=8)
            results.extend(batch)
            if not any(item.dispatched for item in batch):
                break
            if sleep_seconds > 0:
                time.sleep(float(sleep_seconds))
        return results
PY

python -m py_compile \
  companyos/runtime/dependency_aware_dispatcher.py \
  companyos/runtime/autonomous_goal_execution_loop.py

python - <<'PY'
import tempfile
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

q=AutonomousTaskQueue(Path(tempfile.mkdtemp()))
loop=AutonomousGoalExecutionLoop(q)

for i in range(12):
    g=f"g{i}"
    q.enqueue(task_type="research",
              payload={"goal_id":g,"stage":"research"},
              priority=100,
              idempotency_key=f"{g}-r")
    q.enqueue(task_type="planning",
              payload={"goal_id":g,"stage":"planning","depends_on_stage":"research"},
              priority=100,
              idempotency_key=f"{g}-p")
    q.enqueue(task_type="build",
              payload={"goal_id":g,"stage":"build","depends_on_stage":"planning"},
              priority=100,
              idempotency_key=f"{g}-b")

before=sum(1 for t in q._iter_task_files() if t.state=="COMPLETED")
r=loop.run_bounded_batch(max_dispatches=8)
after=sum(1 for t in q._iter_task_files() if t.state=="COMPLETED")

assert sum(1 for x in r if x.dispatched) == 8, r
assert after-before == 8, (before,after)
print("V28_3_BATCH_REGRESSION=PASS")
PY

echo "===== CONTROLLED CHILD RELOAD ====="
SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
OLD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
echo "SUPERVISOR_PID=${SUP:-none}"
echo "OLD_CHILD=${OLD:-none}"
[ -n "${SUP:-}" ] || { echo "ABORT=no_supervisor"; exit 2; }

if [ -n "${OLD:-}" ]; then
  kill "$OLD" 2>/dev/null || true
fi

NEW=""
for i in $(seq 1 30); do
  sleep 1
  C="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
  if [ -n "${C:-}" ] && [ "$C" != "${OLD:-}" ]; then
    NEW="$C"
    break
  fi
  echo "waiting=${i}s"
done

[ -n "${NEW:-}" ] || { echo "ACTIVATION_FAIL=no_new_child"; exit 3; }
echo "NEW_CHILD=$NEW"
echo "V28_3_ACTIVATION=PASS"

echo "===== 75 SECOND LIVE THROUGHPUT ====="
python - <<'PY'
import json,time
from pathlib import Path
from collections import Counter
root=Path.home()/".companyos_runtime"/"task_queue"

def snap():
    c=Counter()
    for p in root.glob("*.json"):
        try:
            c[str(json.loads(p.read_text()).get("state","UNKNOWN")).upper()] += 1
        except Exception:
            c["UNREADABLE"] += 1
    return c

a=snap()
print("T+000",dict(a),flush=True)
b=a
for sec in (15,30,45,60,75):
    time.sleep(15)
    b=snap()
    print(
        f"T+{sec:03d}",
        dict(b),
        "completed_delta=",b["COMPLETED"]-a["COMPLETED"],
        "queued_delta=",b["QUEUED"]-a["QUEUED"],
        "failed_delta=",b["FAILED"]-a["FAILED"],
        flush=True,
    )

print("FINAL_COMPLETED_DELTA=",b["COMPLETED"]-a["COMPLETED"])
print("FINAL_QUEUED_DELTA=",b["QUEUED"]-a["QUEUED"])
print("FINAL_FAILED_DELTA=",b["FAILED"]-a["FAILED"])
PY

echo "===== STATE ====="
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/".companyos_runtime"/"continuous_goal_runtime_state.json"
if p.exists():
    d=json.loads(p.read_text())
    print("LAST_REASON=",d.get("last_reason"))
    print("CYCLES=",d.get("cycles"))
    print("FAILURES=",d.get("consecutive_failures"))
PY

pgrep -af 'companyos.runtime.service_supervisor' || true
pgrep -af 'companyos.runtime.continuous_goal_runtime' || true

echo "V28_3_COMPLETE"
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_RESTARTED=NO"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "BACKUP=$BACK"
trap - ERR
