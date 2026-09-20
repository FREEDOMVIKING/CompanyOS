#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.82a FRESH-PROCESS ORCHESTRATION RECONCILE ====="

python - <<'PY'
from pathlib import Path
import json, py_compile, shutil, sqlite3, tarfile, tempfile, time
from collections import Counter
from dataclasses import asdict

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
QUEUE_DIR = RUNTIME / "task_queue"
DB = RUNTIME / "execution_kernel.sqlite3"
ORCH_DIR = RUNTIME / "ceo_orchestrations"
REPORT_DIR = RUNTIME / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

STAMP = int(time.time())
SNAP_DIR = RUNTIME / "checkpoints" / f"v65_82a_orchestration_reconcile_before_{STAMP}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

LIFECYCLE_SRC = ROOT / "companyos/runtime/goal_lifecycle_manager.py"
LIFECYCLE_BAK = SNAP_DIR / "goal_lifecycle_manager.py.before"

print("REPO=", ROOT)
print("RUNTIME=", RUNTIME)
print("SNAPSHOT_DIR=", SNAP_DIR)

def load_queue_json():
    tasks, unreadable = {}, []
    for p in sorted(QUEUE_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(errors="ignore"))
            tasks[str(d.get("task_id") or p.stem)] = d
        except Exception as exc:
            unreadable.append((str(p), type(exc).__name__, str(exc)))
    return tasks, unreadable

def load_db():
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

def load_orchestration_json():
    records, unreadable = {}, []
    for p in sorted(ORCH_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(errors="ignore"))
            oid = str(d.get("orchestration_id") or p.stem)
            d["_path"] = str(p)
            records[oid] = d
        except Exception as exc:
            unreadable.append((str(p), type(exc).__name__, str(exc)))
    return records, unreadable

def is_reconciled_duplicate(d):
    result = d.get("result")
    return (
        str(d.get("state")) == "CANCELLED"
        and isinstance(result, dict)
        and result.get("reason") == "semantic_duplicate_already_completed"
        and bool(result.get("canonical_task_id"))
    )

# ---------- Baseline ----------
queue_before, unreadable_queue = load_queue_json()
integrity_before, db_before = load_db()
orch_before, unreadable_orch = load_orchestration_json()

qcounts = Counter(str(x.get("state") or "UNKNOWN") for x in queue_before.values())
dcounts = Counter(str(x.get("state") or "UNKNOWN") for x in db_before)
running = [x for x in orch_before.values() if str(x.get("state")) == "RUNNING"]

print("QUEUE_COUNTS_BEFORE=", dict(sorted(qcounts.items())))
print("DB_COUNTS_BEFORE=", dict(sorted(dcounts.items())))
print("QUEUE_MINUS_DB_DELTA_BEFORE=", len(queue_before) - len(db_before))
print("DB_INTEGRITY_BEFORE=", integrity_before)
print("UNREADABLE_QUEUE_FILES=", len(unreadable_queue))
print("UNREADABLE_ORCHESTRATION_FILES=", len(unreadable_orch))
print("RUNNING_ORCHESTRATIONS_BEFORE=", len(running))

if unreadable_queue:
    raise SystemExit("V65_82A_ABORT=unreadable_queue")
if unreadable_orch:
    raise SystemExit("V65_82A_ABORT=unreadable_orchestration")
if integrity_before != "ok":
    raise SystemExit("V65_82A_ABORT=db_integrity_failed")
if len(queue_before) != len(db_before):
    raise SystemExit("V65_82A_ABORT=projection_cardinality_mismatch")
if qcounts.get("QUEUED", 0) or qcounts.get("CLAIMED", 0) or qcounts.get("RUNNING", 0):
    raise SystemExit("V65_82A_ABORT=task_queue_not_fully_terminal")

# ---------- Classify all stale RUNNING orchestrations in one in-memory pass ----------
by_goal = {}
for d in queue_before.values():
    payload = d.get("payload")
    if not isinstance(payload, dict):
        continue
    gid = payload.get("goal_id")
    if gid is not None:
        by_goal.setdefault(str(gid), []).append(d)

details = []
unsafe = []

for rec in running:
    gid = str(rec.get("active_goal_id") or "")
    tasks = list(by_goal.get(gid, []))
    ignored = [d for d in tasks if is_reconciled_duplicate(d)]
    effective = [d for d in tasks if not is_reconciled_duplicate(d)]
    states = Counter(str(d.get("state") or "UNKNOWN") for d in effective)

    if effective and states.get("COMPLETED", 0) == len(effective):
        classification = "all_effective_tasks_completed"
    elif not effective:
        classification = "no_effective_tasks"
    elif states.get("FAILED", 0):
        classification = "has_failed_task"
    elif states.get("QUEUED", 0):
        classification = "has_queued_task"
    elif states.get("CLAIMED", 0) or states.get("RUNNING", 0):
        classification = "has_active_task"
    else:
        classification = "mixed_or_other"

    item = {
        "orchestration_id": rec.get("orchestration_id"),
        "active_goal_id": gid,
        "classification": classification,
        "effective_task_count": len(effective),
        "ignored_reconciled_duplicates": len(ignored),
        "effective_state_counts": dict(states),
        "total_cycles": rec.get("total_cycles"),
    }
    details.append(item)
    if classification != "all_effective_tasks_completed":
        unsafe.append(item)

class_counts = Counter(x["classification"] for x in details)
print("RUNNING_CLASSIFICATION_COUNTS=", dict(sorted(class_counts.items())))
print("UNSAFE_RUNNING_ORCHESTRATIONS=", len(unsafe))

for x in unsafe[:30]:
    print("UNSAFE_RUNNING_DETAIL=", json.dumps(x, sort_keys=True))

if unsafe:
    raise SystemExit("V65_82A_ABORT=running_orchestrations_not_all_terminalizable")

# ---------- Snapshot before mutation ----------
shutil.copy2(LIFECYCLE_SRC, LIFECYCLE_BAK)

db_copy = SNAP_DIR / "execution_kernel.sqlite3"
src = sqlite3.connect(str(DB))
dst = sqlite3.connect(str(db_copy))
try:
    src.backup(dst)
finally:
    dst.close()
    src.close()

for dirname in ("task_queue", "ceo_orchestrations", "goal_lifecycle", "goal_outcomes"):
    p = RUNTIME / dirname
    if p.exists():
        archive = SNAP_DIR / f"{dirname}_before.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            tf.add(p, arcname=dirname)

print("SOURCE_BACKUP=", LIFECYCLE_BAK)
print("RUNTIME_DB_BACKUP=", db_copy)
print("ROLLBACK_SNAPSHOT=PASS")

# ---------- Ensure lifecycle patch exists BEFORE importing lifecycle/orchestrator ----------
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
        raise SystemExit("V65_82A_ABORT=lifecycle_patch_anchor_not_found")
    source = source.replace(old, new, 1)
    LIFECYCLE_SRC.write_text(source, encoding="utf-8")
    print("LIFECYCLE_PATCH_STATUS=inserted")
else:
    print("LIFECYCLE_PATCH_STATUS=already_present")

py_compile.compile(str(LIFECYCLE_SRC), doraise=True)
print("LIFECYCLE_COMPILE=PASS")

# IMPORTANT: all imports below happen after the patch in this fresh interpreter.
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue, TaskRecord
from companyos.runtime.goal_lifecycle_manager import GoalLifecycleManager, GoalRecord
from companyos.runtime.goal_outcome_evaluator import GoalOutcomeEvaluation
from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator

# ---------- Fresh-import isolated regression ----------
with tempfile.TemporaryDirectory(prefix="companyos_v65_82a_") as td:
    troot = Path(td)
    tq = AutonomousTaskQueue(troot / "task_queue")
    now = time.time()
    gid = "v65-82a-test-goal"

    tq.save(TaskRecord(
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

    tq.save(TaskRecord(
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

    lm = GoalLifecycleManager(tq, troot / "goal_lifecycle")
    test_rec = lm.refresh(goal_id=gid, goal="profit test")

    print("FRESH_IMPORT_ISOLATED_STATE=", test_rec.state)
    print("FRESH_IMPORT_EFFECTIVE_TASK_IDS=", test_rec.task_ids)

    if test_rec.state != "COMPLETED":
        raise SystemExit("V65_82A_FAIL=fresh_import_semantic_duplicate_regression")
    if test_rec.task_ids != ["canonical-completed"]:
        raise SystemExit("V65_82A_FAIL=duplicate_tombstone_not_filtered")

print("FRESH_IMPORT_SEMANTIC_DUPLICATE_REGRESSION=PASS")

# ---------- Efficient terminal reconciliation ----------
# We already proved every RUNNING orchestration has only effectively COMPLETED
# task work. Build the same lifecycle/evaluation/final-summary semantics the
# normal orchestrator would produce, without re-scanning 14k task files once
# per historical orchestration.

ceo = AutonomousCEOOrchestrator()
lifecycle = ceo.lifecycle
evaluator = ceo.evaluator

reconciled = []
now = time.time()

for idx, rec_json in enumerate(running, start=1):
    oid = str(rec_json["orchestration_id"])
    gid = str(rec_json["active_goal_id"])
    rec = ceo.load(oid)

    tasks_all = list(by_goal.get(gid, []))
    effective = [d for d in tasks_all if not is_reconciled_duplicate(d)]

    # Recover the goal text the same way the orchestrator would.
    goal_text = rec.root_goal if gid == rec.root_goal_id else gid
    if gid != rec.root_goal_id:
        for d in effective:
            payload = d.get("payload")
            if isinstance(payload, dict):
                goal_text = str(
                    payload.get("goal")
                    or payload.get("topic")
                    or payload.get("name")
                    or gid
                )
                break

    ordered = sorted(
        effective,
        key=lambda d: (
            int(d.get("priority") or 0),
            float(d.get("created_at_unix") or 0),
        ),
    )

    outputs = []
    evidence = []
    for d in ordered:
        outputs.append({
            "task_id": d.get("task_id"),
            "task_type": d.get("task_type"),
            "agent": d.get("assigned_agent"),
            "result": d.get("result"),
        })
        evidence.append({
            "task_type": d.get("task_type"),
            "agent": d.get("assigned_agent"),
            "result": d.get("result"),
        })

    # Persist lifecycle record as COMPLETED.
    try:
        gr = lifecycle.load(gid)
        created_at = gr.created_at_unix
        completed_at = gr.completed_at_unix or now
    except Exception:
        created_at = min(
            [float(d.get("created_at_unix") or now) for d in effective] or [now]
        )
        completed_at = now

    goal_record = GoalRecord(
        goal_id=gid,
        goal=goal_text,
        state="COMPLETED",
        created_at_unix=created_at,
        updated_at_unix=now,
        completed_at_unix=completed_at,
        failed_at_unix=None,
        task_ids=[str(d.get("task_id")) for d in effective],
        completed_tasks=len(effective),
        failed_tasks=0,
        queued_tasks=0,
        running_tasks=0,
        blocked=False,
        final_result={
            "goal_id": gid,
            "goal": goal_text,
            "outputs": outputs,
        },
        last_error=None,
    )
    lifecycle.save(goal_record)

    evaluation = GoalOutcomeEvaluation(
        goal_id=gid,
        evaluated_at_unix=now,
        goal_state="COMPLETED",
        success=True,
        confidence=1.0 if evidence else 0.75,
        outcome_summary=f"Goal completed with {len(effective)} completed tasks.",
        next_action="review_and_decide_follow_up",
        follow_up_goal=None,
        blocked_reason=None,
        evidence=evidence,
    )
    evaluator.save(evaluation)

    if gid not in rec.completed_goal_ids:
        rec.completed_goal_ids.append(gid)

    rec.state = "COMPLETED"
    rec.updated_at_unix = now
    rec.total_cycles = int(rec.total_cycles) + 1
    rec.last_decision = "root_or_followup_goal_completed"
    rec.final_summary = {
        "success": True,
        "root_goal": rec.root_goal,
        "active_goal_id": gid,
        "completed_goal_ids": rec.completed_goal_ids,
        "follow_up_goal_ids": rec.follow_up_goal_ids,
        "evaluation": asdict(evaluation),
        "reconciled_by": "v65.82a",
    }
    ceo.save(rec)
    reconciled.append(oid)

    if idx <= 10 or idx % 100 == 0 or idx == len(running):
        print("RECONCILE_PROGRESS=", {
            "index": idx,
            "total": len(running),
            "orchestration_id": oid,
            "active_goal_id": gid,
            "effective_completed_tasks": len(effective),
        })

print("RECONCILED_ORCHESTRATIONS=", len(reconciled))

# ---------- Final verification ----------
queue_after, unreadable_after = load_queue_json()
integrity_after, db_after = load_db()
orch_after, unreadable_orch_after = load_orchestration_json()

qcounts_after = Counter(str(x.get("state") or "UNKNOWN") for x in queue_after.values())
dcounts_after = Counter(str(x.get("state") or "UNKNOWN") for x in db_after)
running_after = [x for x in orch_after.values() if str(x.get("state")) == "RUNNING"]

print("RUNNING_ORCHESTRATIONS_AFTER=", len(running_after))
print("QUEUE_COUNTS_AFTER=", dict(sorted(qcounts_after.items())))
print("DB_COUNTS_AFTER=", dict(sorted(dcounts_after.items())))
print("QUEUE_MINUS_DB_DELTA_AFTER=", len(queue_after) - len(db_after))
print("DB_INTEGRITY_AFTER=", integrity_after)
print("UNREADABLE_QUEUE_FILES_AFTER=", len(unreadable_after))
print("UNREADABLE_ORCHESTRATION_FILES_AFTER=", len(unreadable_orch_after))

if running_after:
    raise SystemExit("V65_82A_FAIL=running_orchestrations_remain")
if unreadable_after or unreadable_orch_after:
    raise SystemExit("V65_82A_FAIL=unreadable_runtime_record_after")
if integrity_after != "ok":
    raise SystemExit("V65_82A_FAIL=db_integrity_after")
if len(queue_after) != len(db_after):
    raise SystemExit("V65_82A_FAIL=projection_cardinality_after")
if qcounts_after.get("QUEUED", 0):
    raise SystemExit("V65_82A_FAIL=queue_regenerated_unexpectedly")
if qcounts_after.get("CLAIMED", 0) or qcounts_after.get("RUNNING", 0):
    raise SystemExit("V65_82A_FAIL=active_task_state_after")

report = {
    "version": "V65.82a",
    "timestamp": STAMP,
    "running_before": len(running),
    "classification_counts": dict(class_counts),
    "reconciled_orchestrations": len(reconciled),
    "running_after": len(running_after),
    "queue_counts_after": dict(qcounts_after),
    "db_counts_after": dict(dcounts_after),
    "queue_minus_db_delta_after": len(queue_after) - len(db_after),
    "rollback_snapshot_dir": str(SNAP_DIR),
}
rp = REPORT_DIR / f"v65_82a_fresh_process_orchestration_reconcile_{STAMP}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

print("REPORT=", rp)
print("ROLLBACK_AVAILABLE=", SNAP_DIR)
print("V65_82A_FRESH_IMPORT_REGRESSION=PASS")
print("V65_82A_RUNNING_ORCHESTRATIONS_RECONCILED=PASS")
print("V65_82A_QUEUE_REMAINED_DRAINED=PASS")
print("V65_82A_PROJECTION_ALIGNMENT=PASS")
print("V65_82A_COMPLETE")
PY
