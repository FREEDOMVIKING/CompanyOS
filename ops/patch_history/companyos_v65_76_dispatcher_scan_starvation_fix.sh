#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.76 DISPATCHER SCAN STARVATION FIX ====="

python - <<'PY'
from pathlib import Path
import ast, json, os, py_compile, shutil, subprocess, sys, tempfile, time

ROOT = Path.home() / "companyos"
SRC = ROOT / "companyos/runtime/dependency_aware_dispatcher.py"
DISPATCHER = ROOT / "companyos/runtime/autonomous_task_dispatcher.py"

if not SRC.exists():
    raise SystemExit("V65_76_ABORT=dependency_dispatcher_missing")
if not DISPATCHER.exists():
    raise SystemExit("V65_76_ABORT=autonomous_dispatcher_missing")

stamp = int(time.time())
backup = SRC.with_name(f"{SRC.name}.v65_76_backup_{stamp}")
shutil.copy2(SRC, backup)
print("BACKUP=", backup)

dtext = DISPATCHER.read_text(errors="ignore")
required_dispatch = [
    "V35_1_FENCED_HANDLER_CALL",
    "V27_9_4A_LIVE_HANDLER_TIMEOUT",
    "run_bounded(lambda: handler(task))",
    "_v35_guard.execute",
]
missing = [x for x in required_dispatch if x not in dtext]
print("BASE_DISPATCH_CONTRACT_MISSING=", missing)
if missing:
    raise SystemExit("V65_76_ABORT=base_dispatch_contract_missing")

text = SRC.read_text(errors="ignore")

start = text.find("    def dispatch_batch(self, max_dispatches: int = 8) -> list[DispatchResult]:")
end = text.find("    def dispatch_next(self) -> DispatchResult:", start)

if start < 0 or end < 0:
    raise SystemExit("V65_76_ABORT=dispatch_batch_method_not_found")

replacement = '''    def dispatch_batch(self, max_dispatches: int = 8) -> list[DispatchResult]:
        # V65.76 scan-window starvation fix.
        # Keep the rotating window as the fast path, but before declaring idle
        # search the remaining eligible queue so ready work outside the current
        # window cannot be hidden by thousands of completed records.
        max_dispatches = max(1, min(int(max_dispatches), 64))
        scan_limit = max(
            max_dispatches * 16,
            int(os.getenv("COMPANYOS_QUEUE_SCAN_LIMIT", "1000")),
        )

        now = time.time()
        completed = self._completed_stage_index()
        source = self._window(scan_limit)

        try:
            from companyos.runtime.adaptive_backpressure import AdaptiveBackpressure
            boost_type = AdaptiveBackpressure(self.queue).decide().get("boost_type")
        except Exception:
            boost_type = None

        def eligible(task) -> bool:
            return (
                task.state == "QUEUED"
                and task.attempts < task.max_attempts
                and task.next_attempt_unix <= now
                and task.task_type in self.dispatcher.handlers
            )

        def sort_key(task):
            return (
                0 if boost_type and task.task_type == boost_type else 1,
                float(task.created_at_unix),
                -int(task.priority),
                task.task_id,
            )

        results: list[DispatchResult] = []
        dispatched_ids: set[str] = set()

        def drain(candidates) -> None:
            remaining = [
                t for t in candidates
                if t.task_id not in dispatched_ids
            ]
            remaining.sort(key=sort_key)

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
                dispatched_ids.add(task.task_id)

                if result.dispatched and result.reason == "completed":
                    payload = self._payload(task)
                    goal_id = payload.get("goal_id")
                    stage = payload.get("stage")
                    if goal_id and stage:
                        completed.add((str(goal_id), str(stage)))

        # Fast rotating window first.
        drain([t for t in source if eligible(t)])

        # V65.76 starvation fallback: only pay for a whole-queue scan if the
        # fast path could not fill the requested batch.
        if len(results) < max_dispatches:
            fallback = [
                t for t in self.queue._iter_task_files()
                if eligible(t) and t.task_id not in dispatched_ids
            ]
            drain(fallback)

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

'''

patched = text[:start] + replacement + text[end:]
SRC.write_text(patched)

try:
    ast.parse(SRC.read_text())
    py_compile.compile(str(SRC), doraise=True)
except Exception:
    shutil.copy2(backup, SRC)
    print("PATCH_COMPILE=FAIL")
    print("SOURCE_RESTORED=TRUE")
    raise

print("PATCH_COMPILE=PASS")

proof = SRC.read_text(errors="ignore")
tokens = [
    "V65.76 scan-window starvation fix",
    "starvation fallback",
    "self.queue._iter_task_files()",
    "no_dependency_ready_task",
]
missing_tokens = [x for x in tokens if x not in proof]
print("PATCH_PROOF_MISSING=", missing_tokens)
if missing_tokens:
    shutil.copy2(backup, SRC)
    raise SystemExit("V65_76_ABORT=patch_proof_failed")

print("PATCH_PROOF=PASS")

regression = '''
from pathlib import Path
import json, os, time

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue, TaskRecord
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.dependency_aware_dispatcher import DependencyAwareDispatcher

root = Path.home() / ".companyos_runtime" / "task_queue"
root.mkdir(parents=True, exist_ok=True)
now = time.time()

for i in range(1000):
    task_id = f"a{i:04d}"
    d = {
        "task_id": task_id,
        "idempotency_key": f"dummy:{i}",
        "task_type": "research",
        "priority": 1,
        "payload": {"goal_id": f"dummy-goal-{i}", "stage": "research"},
        "state": "COMPLETED",
        "assigned_agent": None,
        "attempts": 1,
        "max_attempts": 3,
        "created_at_unix": now - 1000 + i,
        "updated_at_unix": now,
        "next_attempt_unix": now,
        "result": {"ok": True},
        "last_error": None,
    }
    (root / f"{task_id}.json").write_text(json.dumps(d))

ready = TaskRecord(
    task_id="zzzz-ready",
    idempotency_key="regression:ready",
    task_type="research",
    priority=999,
    payload={"goal_id": "regression-goal", "stage": "research", "profitability": True},
    state="QUEUED",
    assigned_agent=None,
    attempts=0,
    max_attempts=3,
    created_at_unix=now,
    updated_at_unix=now,
    next_attempt_unix=now,
    result=None,
    last_error=None,
)
(root / "zzzz-ready.json").write_text(json.dumps(ready.__dict__))

os.environ["COMPANYOS_QUEUE_SCAN_LIMIT"] = "1000"

q = AutonomousTaskQueue(root)
base = AutonomousTaskDispatcher(q)
base.register(
    task_type="research",
    agent_name="regression-research",
    handler=lambda task: {"ok": True, "external_research_performed": False},
)
dep = DependencyAwareDispatcher(base)
r = dep.dispatch_next()

print("REGRESSION_RESULT=", r)
print("REGRESSION_DISPATCHED=", r.dispatched)
print("REGRESSION_TASK_ID=", r.task_id)
print("REGRESSION_REASON=", r.reason)

if not r.dispatched:
    raise SystemExit("REGRESSION_FAIL=not_dispatched")
if r.task_id != "zzzz-ready":
    raise SystemExit("REGRESSION_FAIL=wrong_task")
if r.reason != "completed":
    raise SystemExit("REGRESSION_FAIL=not_completed")

print("SCAN_STARVATION_REGRESSION=PASS")
'''

with tempfile.TemporaryDirectory(prefix="companyos_v65_76_") as td:
    env = os.environ.copy()
    env["HOME"] = td
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    cp = subprocess.run(
        [sys.executable, "-c", regression],
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
    )

    print("REGRESSION_RETURN_CODE=", cp.returncode)
    print(cp.stdout)
    if cp.stderr:
        print(cp.stderr)

    if cp.returncode != 0:
        shutil.copy2(backup, SRC)
        py_compile.compile(str(SRC), doraise=True)
        print("REGRESSION=FAIL")
        print("SOURCE_RESTORED=TRUE")
        raise SystemExit(cp.returncode)

print("REGRESSION=PASS")

tests = sorted({
    *ROOT.glob("tests/*dispatch*.py"),
    *ROOT.glob("tests/*dependency*.py"),
})

test_args = [str(p.relative_to(ROOT)) for p in tests if p.is_file()]
print("TARGET_TEST_FILES=", test_args)

if test_args:
    cp = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *test_args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=300,
    )
    print("TARGET_TEST_RETURN_CODE=", cp.returncode)
    print(cp.stdout[-16000:])
    if cp.stderr:
        print(cp.stderr[-6000:])

    if cp.returncode != 0:
        shutil.copy2(backup, SRC)
        py_compile.compile(str(SRC), doraise=True)
        print("TARGET_TESTS=FAIL")
        print("SOURCE_RESTORED=TRUE")
        raise SystemExit(cp.returncode)

print("TARGET_TESTS=PASS")
print("SOURCE_RESTORED=FALSE")
print("V65_76_SCAN_STARVATION_FIX=PASS")
print("V65_76_COMPLETE")
PY
