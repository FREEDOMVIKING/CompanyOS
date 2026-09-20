#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.79b JSON-ONLY DUPLICATE RECONCILIATION ====="

python - <<'PY'
from pathlib import Path
import ast
import json
import sqlite3
import tarfile
import time
from collections import defaultdict, Counter

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
QUEUE_DIR = RUNTIME / "task_queue"
DB = RUNTIME / "execution_kernel.sqlite3"
REPORT_DIR = RUNTIME / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

STAMP = int(time.time())
SNAP_DIR = RUNTIME / "checkpoints" / f"v65_79b_projection_reconcile_before_{STAMP}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

print("REPO=", ROOT)
print("RUNTIME=", RUNTIME)
print("SNAPSHOT_DIR=", SNAP_DIR)

# ---------- Verify corrected dispatcher result flow structurally ----------
dispatcher = ROOT / "companyos/runtime/autonomous_task_dispatcher.py"
dtext = dispatcher.read_text(errors="ignore")
tree = ast.parse(dtext)

has_result_assignment = False
has_execute_call = False
has_complete_with_result = False

for node in ast.walk(tree):
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = set()
        for t in targets:
            for sub in ast.walk(t):
                if isinstance(sub, ast.Name):
                    names.add(sub.id)
        if "result" in names:
            has_result_assignment = True

    if isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Attribute) and fn.attr == "execute":
            has_execute_call = True
        if isinstance(fn, ast.Attribute) and fn.attr == "complete":
            if any(isinstance(a, ast.Name) and a.id == "result" for a in node.args):
                has_complete_with_result = True

flow = {
    "result_assignment": has_result_assignment,
    "execute_call": has_execute_call,
    "complete_with_result": has_complete_with_result,
}
print("CURRENT_RESULT_FLOW_AST=", flow)
if not all(flow.values()):
    raise SystemExit("V65_79B_ABORT=current_dispatcher_result_flow_not_verified")

print("CURRENT_DISPATCHER_RESULT_FLOW=VERIFIED")

# ---------- Load current projections ----------
def load_json():
    tasks = {}
    unreadable = []
    for p in sorted(QUEUE_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(errors="ignore"))
            tid = str(d.get("task_id") or p.stem)
            tasks[tid] = d
        except Exception as exc:
            unreadable.append((str(p), type(exc).__name__, str(exc)))
    return tasks, unreadable

def load_db():
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        rows = [dict(r) for r in con.execute(
            "SELECT task_id,idempotency_key,task_type,priority,state,assigned_agent,"
            "attempts,max_attempts,created_at_unix,updated_at_unix,next_attempt_unix,"
            "goal_id,stage,depends_on_stage,payload_json,result_json,last_error "
            "FROM tasks"
        ).fetchall()]
    finally:
        con.close()
    return integrity, rows

json_tasks, unreadable = load_json()
integrity_before, db_rows = load_db()

print("JSON_TASKS_BEFORE=", len(json_tasks))
print("JSON_UNREADABLE_BEFORE=", len(unreadable))
print("DB_TASKS_BEFORE=", len(db_rows))
print("DB_INTEGRITY_BEFORE=", integrity_before)
print("JSON_STATE_COUNTS_BEFORE=", dict(sorted(Counter(str(x.get("state") or "UNKNOWN") for x in json_tasks.values()).items())))
print("DB_STATE_COUNTS_BEFORE=", dict(sorted(Counter(str(x.get("state") or "UNKNOWN") for x in db_rows).items())))

if unreadable:
    raise SystemExit("V65_79B_ABORT=unreadable_json")
if integrity_before != "ok":
    raise SystemExit("V65_79B_ABORT=db_integrity_failed")

db_by_id = {str(r["task_id"]): r for r in db_rows}
db_by_key = {
    str(r.get("idempotency_key")): r
    for r in db_rows
    if str(r.get("idempotency_key") or "")
}

json_by_key = defaultdict(list)
for tid, d in json_tasks.items():
    key = str(d.get("idempotency_key") or "")
    if key:
        json_by_key[key].append((tid, d))

dup_groups = {k:v for k,v in json_by_key.items() if len(v) > 1}
print("JSON_DUPLICATE_KEYS_BEFORE=", len(dup_groups))

# ---------- Classify JSON-only duplicate shadows ----------
# Safe case:
# - SQLite unique-key owner exists
# - owner JSON exists and owner is COMPLETED in both projections
# - duplicate JSON task has no SQLite row (the previous upsert failed)
# - duplicate is nonterminal
# - goal/stage/type exactly match the completed canonical owner
shadow_repairs = []
ambiguous_duplicates = []

for key, group in dup_groups.items():
    owner = db_by_key.get(key)
    if not owner:
        ambiguous_duplicates.append({"key": key, "reason": "no_db_key_owner"})
        continue

    owner_tid = str(owner["task_id"])
    owner_json = json_tasks.get(owner_tid)
    if not owner_json:
        ambiguous_duplicates.append({
            "key": key,
            "reason": "db_owner_missing_json",
            "owner_task_id": owner_tid,
        })
        continue

    op = owner_json.get("payload") if isinstance(owner_json.get("payload"), dict) else {}
    canonical_sig = (
        str(owner_json.get("task_type")),
        str(op.get("goal_id")),
        str(op.get("stage")),
    )

    if str(owner.get("state")) != "COMPLETED" or str(owner_json.get("state")) != "COMPLETED":
        ambiguous_duplicates.append({
            "key": key,
            "reason": "canonical_owner_not_completed",
            "owner_task_id": owner_tid,
            "db_state": owner.get("state"),
            "json_state": owner_json.get("state"),
        })
        continue

    for tid, d in group:
        if tid == owner_tid:
            continue

        dp = d.get("payload") if isinstance(d.get("payload"), dict) else {}
        duplicate_sig = (
            str(d.get("task_type")),
            str(dp.get("goal_id")),
            str(dp.get("stage")),
        )

        safe = (
            tid not in db_by_id
            and str(d.get("state")) in {"QUEUED", "CLAIMED", "RUNNING"}
            and duplicate_sig == canonical_sig
        )

        item = {
            "key": key,
            "canonical_task_id": owner_tid,
            "duplicate_task_id": tid,
            "duplicate_state": d.get("state"),
            "task_type": d.get("task_type"),
            "goal_id": dp.get("goal_id"),
            "stage": dp.get("stage"),
            "duplicate_has_db_row": tid in db_by_id,
            "same_semantics": duplicate_sig == canonical_sig,
        }

        if safe:
            shadow_repairs.append(item)
        else:
            item["reason"] = "json_only_shadow_safety_check_failed"
            ambiguous_duplicates.append(item)

print("SAFE_JSON_ONLY_DUPLICATE_SHADOWS=", len(shadow_repairs))
print("AMBIGUOUS_DUPLICATES=", len(ambiguous_duplicates))

for x in shadow_repairs:
    print("SAFE_SHADOW=", json.dumps(x, sort_keys=True))
for x in ambiguous_duplicates:
    print("AMBIGUOUS_DUPLICATE=", json.dumps(x, sort_keys=True))

if ambiguous_duplicates:
    raise SystemExit("V65_79B_ABORT=ambiguous_duplicate_requires_review")

# ---------- Classify known historical NameError(result) mismatches ----------
historical_retry = []
other_mismatches = []

for tid, jt in json_tasks.items():
    dr = db_by_id.get(tid)
    if not dr:
        continue

    js = str(jt.get("state"))
    ds = str(dr.get("state"))
    if js == ds:
        continue

    db_error = str(dr.get("last_error") or "")
    same_key = str(jt.get("idempotency_key") or "") == str(dr.get("idempotency_key") or "")
    same_type = str(jt.get("task_type")) == str(dr.get("task_type"))

    known = (
        js == "QUEUED"
        and ds == "FAILED"
        and same_key
        and same_type
        and "NameError" in db_error
        and "result" in db_error
        and "not defined" in db_error
    )

    if known:
        historical_retry.append({
            "task_id": tid,
            "idempotency_key": jt.get("idempotency_key"),
            "task_type": jt.get("task_type"),
            "db_last_error": db_error,
        })
    else:
        other_mismatches.append({
            "task_id": tid,
            "json_state": js,
            "db_state": ds,
            "json_key": jt.get("idempotency_key"),
            "db_key": dr.get("idempotency_key"),
            "db_last_error": dr.get("last_error"),
        })

print("KNOWN_HISTORICAL_RESULT_BUG_RETRIES=", len(historical_retry))
print("OTHER_STATE_MISMATCHES=", len(other_mismatches))

for x in historical_retry[:30]:
    print("HISTORICAL_RETRY=", json.dumps(x, sort_keys=True))
for x in other_mismatches[:20]:
    print("OTHER_MISMATCH=", json.dumps(x, sort_keys=True))

if other_mismatches:
    raise SystemExit("V65_79B_ABORT=unexpected_state_mismatch_requires_review")

if not shadow_repairs and not historical_retry:
    print("V65_79B_NOTHING_TO_REPAIR=TRUE")
    raise SystemExit(0)

# ---------- Full rollback snapshot before any mutation ----------
db_copy = SNAP_DIR / "execution_kernel.sqlite3"
src = sqlite3.connect(str(DB))
dst = sqlite3.connect(str(db_copy))
try:
    src.backup(dst)
finally:
    dst.close()
    src.close()

archive = SNAP_DIR / "task_queue_before.tar.gz"
with tarfile.open(archive, "w:gz") as tf:
    tf.add(QUEUE_DIR, arcname="task_queue")
    cursor = RUNTIME / "dispatcher_scan_cursor.txt"
    if cursor.exists():
        tf.add(cursor, arcname="dispatcher_scan_cursor.txt")

with tarfile.open(archive, "r:gz") as tf:
    members = len(tf.getmembers())

print("RUNTIME_SNAPSHOT_DB=", db_copy)
print("RUNTIME_SNAPSHOT_QUEUE=", archive)
print("SNAPSHOT_ARCHIVE_MEMBERS=", members)
print("ROLLBACK_SNAPSHOT=PASS")

# ---------- Use the queue's own save/upsert path ----------
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue, TaskRecord

q = AutonomousTaskQueue()
now = time.time()

# 1) Preserve each JSON-only duplicate as an auditable CANCELLED record,
#    but give it a fresh tombstone idempotency key so the completed canonical
#    task keeps ownership of the original key. q.save then inserts the missing
#    durable row and removes the queue-vs-DB cardinality drift.
for item in shadow_repairs:
    dup_tid = item["duplicate_task_id"]
    canonical_tid = item["canonical_task_id"]
    old = json_tasks[dup_tid]

    tombstone = f"reconciled-duplicate:{dup_tid}:{STAMP}"
    if tombstone in db_by_key or tombstone in json_by_key:
        raise SystemExit("V65_79B_ABORT=tombstone_key_collision")

    task = TaskRecord(
        task_id=str(old["task_id"]),
        idempotency_key=tombstone,
        task_type=str(old["task_type"]),
        priority=int(old["priority"]),
        payload=dict(old["payload"]),
        state="CANCELLED",
        assigned_agent=None,
        attempts=int(old["attempts"]),
        max_attempts=int(old["max_attempts"]),
        created_at_unix=float(old["created_at_unix"]),
        updated_at_unix=now,
        next_attempt_unix=float(old["next_attempt_unix"]),
        result={
            "cancelled": True,
            "reason": "semantic_duplicate_already_completed",
            "canonical_task_id": canonical_tid,
            "original_idempotency_key": item["key"],
        },
        last_error=f"semantic_duplicate_already_completed:{canonical_tid}",
    )

    q.save(task)
    print(
        "JSON_ONLY_DUPLICATE_RECONCILED=",
        dup_tid,
        "CANONICAL=",
        canonical_tid,
        "TOMBSTONE_KEY=",
        tombstone,
    )

# 2) Reset only the 16 known historical NameError(result) records through the
#    normal queue save/upsert path.
for item in historical_retry:
    tid = item["task_id"]
    old = json_tasks[tid]

    task = TaskRecord(
        task_id=str(old["task_id"]),
        idempotency_key=str(old.get("idempotency_key") or ""),
        task_type=str(old["task_type"]),
        priority=int(old["priority"]),
        payload=dict(old["payload"]),
        state="QUEUED",
        assigned_agent=None,
        attempts=0,
        max_attempts=int(old["max_attempts"]),
        created_at_unix=float(old["created_at_unix"]),
        updated_at_unix=now,
        next_attempt_unix=now,
        result=None,
        last_error=None,
    )

    q.save(task)
    print("HISTORICAL_RESULT_FAILURE_REQUEUED=", tid)

# ---------- Verify exact JSON/SQLite alignment ----------
json_after, unreadable_after = load_json()
integrity_after, db_after = load_db()

db_after_by_id = {str(r["task_id"]): r for r in db_after}
db_after_by_key = {
    str(r.get("idempotency_key")): r
    for r in db_after
    if str(r.get("idempotency_key") or "")
}

json_after_by_key = defaultdict(list)
for tid, d in json_after.items():
    key = str(d.get("idempotency_key") or "")
    if key:
        json_after_by_key[key].append((tid, d))

dup_after = {k:v for k,v in json_after_by_key.items() if len(v) > 1}

owner_conflicts_after = []
state_mismatches_after = []
json_missing_db_after = []
db_missing_json_after = []

for tid, jt in json_after.items():
    dr = db_after_by_id.get(tid)
    if not dr:
        json_missing_db_after.append(tid)
        continue

    if str(jt.get("state")) != str(dr.get("state")):
        state_mismatches_after.append({
            "task_id": tid,
            "json_state": jt.get("state"),
            "db_state": dr.get("state"),
        })

    key = str(jt.get("idempotency_key") or "")
    owner = db_after_by_key.get(key)
    if key and owner and str(owner["task_id"]) != tid:
        owner_conflicts_after.append({
            "key": key,
            "json_task_id": tid,
            "db_owner_task_id": owner["task_id"],
        })

for tid in db_after_by_id:
    if tid not in json_after:
        db_missing_json_after.append(tid)

json_states = Counter(str(d.get("state") or "UNKNOWN") for d in json_after.values())
db_states = Counter(str(d.get("state") or "UNKNOWN") for d in db_after)

print("DB_INTEGRITY_AFTER=", integrity_after)
print("JSON_TASKS_AFTER=", len(json_after))
print("DB_TASKS_AFTER=", len(db_after))
print("QUEUE_MINUS_DB_DELTA_AFTER=", len(json_after) - len(db_after))
print("JSON_UNREADABLE_AFTER=", len(unreadable_after))
print("JSON_DUPLICATE_KEYS_AFTER=", len(dup_after))
print("IDEMPOTENCY_OWNER_CONFLICTS_AFTER=", len(owner_conflicts_after))
print("STATE_MISMATCHES_AFTER=", len(state_mismatches_after))
print("JSON_WITHOUT_DB_TASK_ID_AFTER=", len(json_missing_db_after))
print("DB_WITHOUT_JSON_TASK_ID_AFTER=", len(db_missing_json_after))
print("JSON_STATE_COUNTS_AFTER=", dict(sorted(json_states.items())))
print("DB_STATE_COUNTS_AFTER=", dict(sorted(db_states.items())))

if integrity_after != "ok":
    raise SystemExit("V65_79B_FAIL=db_integrity_after")
if unreadable_after:
    raise SystemExit("V65_79B_FAIL=unreadable_json_after")
if dup_after:
    raise SystemExit("V65_79B_FAIL=json_duplicate_keys_remain")
if owner_conflicts_after:
    raise SystemExit("V65_79B_FAIL=idempotency_owner_conflicts_remain")
if state_mismatches_after:
    raise SystemExit("V65_79B_FAIL=state_projection_mismatches_remain")
if json_missing_db_after:
    raise SystemExit("V65_79B_FAIL=json_rows_missing_db")
if db_missing_json_after:
    raise SystemExit("V65_79B_FAIL=db_rows_missing_json")
if len(json_after) != len(db_after):
    raise SystemExit("V65_79B_FAIL=projection_cardinality_mismatch")

report = {
    "version": "V65.79b",
    "timestamp": STAMP,
    "json_only_duplicate_repairs": shadow_repairs,
    "historical_result_bug_retries": historical_retry,
    "json_state_counts_after": dict(json_states),
    "db_state_counts_after": dict(db_states),
    "rollback_snapshot_dir": str(SNAP_DIR),
}
rp = REPORT_DIR / f"v65_79b_json_only_duplicate_reconciliation_{STAMP}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

print("REPORT=", rp)
print("ROLLBACK_AVAILABLE=", SNAP_DIR)
print("V65_79B_JSON_ONLY_DUPLICATE_RECONCILIATION=PASS")
print("V65_79B_HISTORICAL_RESULT_RETRY_RESET=PASS")
print("V65_79B_PROJECTION_ALIGNMENT=PASS")
print("V65_79B_COMPLETE")
PY
