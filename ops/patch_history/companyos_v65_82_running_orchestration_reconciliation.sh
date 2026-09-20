#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.82 RUNNING ORCHESTRATION RECONCILIATION ====="

python - <<'PY'
from pathlib import Path
import json, py_compile, shutil, sqlite3, tarfile, tempfile, time
from collections import Counter

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
QUEUE_DIR = RUNTIME / "task_queue"
DB = RUNTIME / "execution_kernel.sqlite3"
REPORT_DIR = RUNTIME / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

STAMP = int(time.time())
SNAP_DIR = RUNTIME / "checkpoints" / f"v65_82_orchestration_reconcile_before_{STAMP}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

LIFECYCLE_SRC = ROOT / "companyos/runtime/goal_lifecycle_manager.py"
LIFECYCLE_BAK = SNAP_DIR / "goal_lifecycle_manager.py.before"

print("REPO=", ROOT)
print("RUNTIME=", RUNTIME)
print("SNAPSHOT_DIR=", SNAP_DIR)

def load_queue():
    tasks, unreadable = {}, []
    for p in sorted(QUEUE_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(errors="ignore"))
            tasks[str(d.get("task_id") or p.stem)] = d
        except Exception as exc:
            unreadable.append((str(p), type(exc).__name__, str(exc)))
    return tasks, unreadable

def read_db():
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        rows = [dict(r) for r in con.execute(
            "SELECT task_id,idempotency_key,task_type,state,goal_id,stage,last_error FROM tasks"
        ).fetchall()]
    finally:
        con.close()
    return integrity, rows

queue_before, unreadable = load_queue()
integrity_before, db_before = read_db()

qcounts = Counter(str(x.get("state") or "UNKNOWN") for x in queue_before.values())
dcounts = Counter(str(x.get("state") or "UNKNOWN") for x in db_before)

print("QUEUE_COUNTS_BEFORE=", dict(sorted(qcounts.items())))
print("DB_COUNTS_BEFORE=", dict(sorted(dcounts.items())))
print("QUEUE_MINUS_DB_DELTA_BEFORE=", len(queue_before) - len(db_before))
print("DB_INTEGRITY_BEFORE=", integrity_before)
print("UNREADABLE_QUEUE_FILES_BEFORE=", len(unreadable))

if unreadable:
    raise SystemExit("V65_82_ABORT=unreadable_queue")
if integrity_before != "ok":
    raise SystemExit("V65_82_ABORT=db_integrity_failed")
if len(queue_before) != len(db_before):
    raise SystemExit("V65_82_ABORT=projection_cardinality_mismatch")
if qcounts.get("QUEUED", 0) != 0:
    raise SystemExit("V65_82_ABORT=queue_not_empty")
if qcounts.get("CLAIMED", 0) != 0 or qcounts.get("RUNNING", 0) != 0:
    raise SystemExit("V65_82_ABORT=active_task_execution_present")

from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator

ceo = AutonomousCEOOrchestrator()
running = []
for p in sorted(ceo.root.glob("*.json")):
    try:
        rec = ceo.load(p.stem)
    except Exception:
        continue
    if rec.state == "RUNNING":
        running.append(rec)

print("RUNNING_ORCHESTRATIONS_BEFORE=", len(running))

def ignored_duplicate(d):
    result = d.get("result")
    return (
        str(d.get("state")) == "CANCELLED"
        and isinstance(result, dict)
        and result.get("reason") == "semantic_duplicate_already_completed"
        and bool(result.get("canonical_task_id"))
    )

classifications = Counter()
details = []

for rec in running:
    active_gid = rec.active_goal_id
    tasks = []
    for d in queue_before.values():
        payload = d.get("payload")
        if isinstance(payload, dict) and str(payload.get("goal_id")) == str(active_gid):
            tasks.append(d)

    effective = [d for d in tasks if not ignored_duplicate(d)]
    states = Counter(str(d.get("state") or "UNKNOWN") for d in effective)
    ignored = [d for d in tasks if ignored_duplicate(d)]

    if effective and states.get("COMPLETED", 0) == len(effective):
        cls = "all_effective_tasks_completed"
    elif not effective:
        cls = "no_effective_tasks"
    elif states.get("FAILED", 0):
        cls = "has_failed_task"
    elif states.get("QUEUED", 0):
        cls = "has_queued_task"
    elif states.get("CLAIMED", 0) or states.get("RUNNING", 0):
        cls = "has_active_task"
    else:
        cls = "mixed_or_other"

    classifications[cls] += 1
    details.append({
        "orchestration_id": rec.orchestration_id,
        "active_goal_id": active_gid,
        "classification": cls,
        "effective_task_count": len(effective),
        "ignored_reconciled_duplicates": len(ignored),
        "effective_state_counts": dict(states),
        "total_cycles": rec.total_cycles,
    })

print("RUNNING_CLASSIFICATION_COUNTS=", dict(sorted(classifications.items())))
for item in details:
    print("RUNNING_ORCHESTRATION_DETAIL=", json.dumps(item, sort_keys=True))

unsafe = [x for x in details if x["classification"] != "all_effective_tasks_completed"]
print("UNSAFE_RUNNING_ORCHESTRATIONS=", len(unsafe))
for item in unsafe[:20]:
    print("UNSAFE_RUNNING_DETAIL=", json.dumps(item, sort_keys=True))

if unsafe:
    raise SystemExit("V65_82_ABORT=running_orchestrations_not_all_terminalizable")

# Full rollback snapshot.
shutil.copy2(LIFECYCLE_SRC, LIFECYCLE_BAK)

db_copy = SNAP_DIR / "execution_kernel.sqlite3"
src = sqlite3.connect(str(DB))
dst = sqlite3.connect(str(db_copy))
try:
    src.backup(dst)
finally:
    dst.close()
    src.close()

queue_archive = SNAP_DIR / "task_queue_before.tar.gz"
with tarfile.open(queue_archive, "w:gz") as tf:
    tf.add(QUEUE_DIR, arcname="task_queue")

for dirname in ("ceo_orchestrations", "goal_lifecycle", "goal_outcomes"):
    p = RUNTIME / dirname
    if p.exists():
        a = SNAP_DIR / f"{dirname}_before.tar.gz"
        with tarfile.open(a, "w:gz") as tf:
            tf.add(p, arcname=dirname)

print("SOURCE_BACKUP=", LIFECYCLE_BAK)
print("RUNTIME_DB_BACKUP=", db_copy)
print("QUEUE_BACKUP=", queue_archive)
print("ROLLBACK_SNAPSHOT=PASS")

# Patch lifecycle manager so only the exact reconciliation tombstone is ignored.
source = LIFECYCLE_SRC.read_text(encoding="utf-8")
marker = "# V65.82 semantic duplicate cancellation lifecycle filter"

if marker not in source:
    old_lines = [
        "        tasks = []",
        "        for task in self.queue.all_tasks():",
        "            payload = task.payload or {}",
        '            if payload.get("goal_id") == goal_id:',
        "                tasks.append(task)",
        "",
        "        record.task_ids = [t.task_id for t in tasks]",
    ]
    new_lines = [
        "        all_tasks = []",
        "        for task in self.queue.all_tasks():",
        "            payload = task.payload or {}",
        '            if payload.get("goal_id") == goal_id:',
        "                all_tasks.append(task)",
        "",
        "        # V65.82 semantic duplicate cancellation lifecycle filter",
        "        # A reconciliation tombstone is audit history, not unfinished goal work.",
        "        # General CANCELLED tasks are NOT ignored.",
        "        tasks = []",
        "        for task in all_tasks:",
        "            ignored_duplicate = (",
        '                task.state == "CANCELLED"',
        "                and isinstance(task.result, dict)",
        '                and task.result.get("reason") == "semantic_duplicate_already_completed"',
        '                and bool(task.result.get("canonical_task_id"))',
        "            )",
        "            if not ignored_duplicate:",
        "                tasks.append(task)",
        "",
        "        record.task_ids = [t.task_id for t in tasks]",
    ]
    old = "\n".join(old_lines) + "\n"
    new = "\n".join(new_lines) + "\n"
    if old not in source:
        raise SystemExit("V65_82_ABORT=lifecycle_patch_anchor_not_found")
    source = source.replace(old, new, 1)
    LIFECYCLE_SRC.write_text(source, encoding="utf-8")
    print("LIFECYCLE_PATCH_STATUS=inserted")
else:
    print("LIFECYCLE_PATCH_STATUS=already_present")

py_compile.compile(str(LIFECYCLE_SRC), doraise=True)
print("LIFECYCLE_COMPILE=PASS")

# Isolated regression proof.
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue, TaskRecord
from companyos.runtime.goal_lifecycle_manager import GoalLifecycleManager

with tempfile.TemporaryDirectory(prefix="companyos_v65_82_") as td:
    troot = Path(td)
    q = AutonomousTaskQueue(troot / "task_queue")
    now = time.time()
    gid = "v65-82-test-goal"

    q.save(TaskRecord(
        task_id="canonical-completed",
        idempotency_key=f"{gid}:research",
        task_type="research",
        priority=100,
        payload={"goal_id": gid, "stage": "research", "topic": "profit test"},
        state="COMPLETED",
        assigned_agent="research_agent",
        attempts=1,
        max_attempts=3,
        created_at_unix=now,
        updated_at_unix=now,
        next_attempt_unix=now,
        result={"ok": True},
        last_error=None,
    ))

    q.save(TaskRecord(
        task_id="duplicate-shadow",
        idempotency_key="reconciled-duplicate:duplicate-shadow:test",
        task_type="research",
        priority=100,
        payload={"goal_id": gid, "stage": "research", "topic": "profit test"},
        state="CANCELLED",
        assigned_agent=None,
        attempts=0,
        max_attempts=3,
        created_at_unix=now,
        updated_at_unix=now,
        next_attempt_unix=now,
        result={
            "cancelled": True,
            "reason": "semantic_duplicate_already_completed",
            "canonical_task_id": "canonical-completed",
            "original_idempotency_key": f"{gid}:research",
        },
        last_error="semantic_duplicate_already_completed:canonical-completed",
    ))

    lm = GoalLifecycleManager(q, troot / "goal_lifecycle")
    test_rec = lm.refresh(goal_id=gid, goal="profit test")
    print("ISOLATED_LIFECYCLE_STATE=", test_rec.state)
    print("ISOLATED_COMPLETED_TASKS=", test_rec.completed_tasks)
    print("ISOLATED_EFFECTIVE_TASK_IDS=", test_rec.task_ids)
    if test_rec.state != "COMPLETED":
        raise SystemExit("V65_82_FAIL=semantic_duplicate_regression")

print("SEMANTIC_DUPLICATE_LIFECYCLE_REGRESSION=PASS")

# Reconcile only orchestrations already proven to have all effective tasks completed.
fresh_ceo = AutonomousCEOOrchestrator()
reconciled = []

for item in details:
    oid = item["orchestration_id"]
    before = fresh_ceo.load(oid)
    result = fresh_ceo.cycle(oid)
    after = fresh_ceo.load(oid)

    print("RECONCILE_RESULT=", {
        "orchestration_id": oid,
        "before_state": before.state,
        "cycle_decision": result.decision,
        "goal_state": result.goal_state,
        "after_state": after.state,
        "task_dispatched": result.task_dispatched,
        "follow_up_created": result.follow_up_created,
    })

    if result.task_dispatched:
        raise SystemExit(f"V65_82_FAIL=unexpected_task_dispatch:{oid}")
    if result.follow_up_created:
        raise SystemExit(f"V65_82_FAIL=unexpected_followup_created:{oid}")
    if after.state != "COMPLETED":
        raise SystemExit(f"V65_82_FAIL=orchestration_not_completed:{oid}:{after.state}")

    reconciled.append(oid)

print("RECONCILED_ORCHESTRATIONS=", len(reconciled))

queue_after, unreadable_after = load_queue()
integrity_after, db_after = read_db()
qcounts_after = Counter(str(x.get("state") or "UNKNOWN") for x in queue_after.values())
dcounts_after = Counter(str(x.get("state") or "UNKNOWN") for x in db_after)

running_after = []
for p in sorted(fresh_ceo.root.glob("*.json")):
    try:
        r = fresh_ceo.load(p.stem)
    except Exception:
        continue
    if r.state == "RUNNING":
        running_after.append(r.orchestration_id)

print("RUNNING_ORCHESTRATIONS_AFTER=", len(running_after))
print("QUEUE_COUNTS_AFTER=", dict(sorted(qcounts_after.items())))
print("DB_COUNTS_AFTER=", dict(sorted(dcounts_after.items())))
print("QUEUE_MINUS_DB_DELTA_AFTER=", len(queue_after) - len(db_after))
print("DB_INTEGRITY_AFTER=", integrity_after)
print("UNREADABLE_QUEUE_FILES_AFTER=", len(unreadable_after))

if running_after:
    raise SystemExit("V65_82_FAIL=running_orchestrations_remain")
if unreadable_after:
    raise SystemExit("V65_82_FAIL=unreadable_queue_after")
if integrity_after != "ok":
    raise SystemExit("V65_82_FAIL=db_integrity_after")
if len(queue_after) != len(db_after):
    raise SystemExit("V65_82_FAIL=projection_cardinality_after")
if qcounts_after.get("QUEUED", 0):
    raise SystemExit("V65_82_FAIL=queue_regenerated_unexpectedly")

report = {
    "version": "V65.82",
    "timestamp": STAMP,
    "running_before": len(running),
    "classification_counts": dict(classifications),
    "reconciled_orchestrations": reconciled,
    "running_after": len(running_after),
    "queue_counts_after": dict(qcounts_after),
    "db_counts_after": dict(dcounts_after),
    "rollback_snapshot_dir": str(SNAP_DIR),
}
rp = REPORT_DIR / f"v65_82_running_orchestration_reconciliation_{STAMP}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

print("REPORT=", rp)
print("ROLLBACK_AVAILABLE=", SNAP_DIR)
print("V65_82_LIFECYCLE_PATCH=PASS")
print("V65_82_SEMANTIC_DUPLICATE_FILTER=PASS")
print("V65_82_RUNNING_ORCHESTRATIONS_RECONCILED=PASS")
print("V65_82_QUEUE_REMAINED_DRAINED=PASS")
print("V65_82_COMPLETE")
PY
