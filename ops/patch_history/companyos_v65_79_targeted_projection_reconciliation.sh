#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.79 TARGETED PROJECTION RECONCILIATION ====="

python - <<'PY'
from pathlib import Path
import json
import os
import re
import shutil
import sqlite3
import tarfile
import time
from collections import Counter, defaultdict

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
QUEUE_DIR = RUNTIME / "task_queue"
DB = RUNTIME / "execution_kernel.sqlite3"
REPORT_DIR = RUNTIME / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

STAMP = int(time.time())
SNAP_DIR = RUNTIME / "checkpoints" / f"v65_79_projection_reconcile_before_{STAMP}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

print("REPO=", ROOT)
print("RUNTIME=", RUNTIME)
print("SNAPSHOT_DIR=", SNAP_DIR)

# Current source must contain the fixed dispatcher result flow before retrying
# tasks whose only durable failure was the historical NameError(result).
dispatcher = ROOT / "companyos/runtime/autonomous_task_dispatcher.py"
dtext = dispatcher.read_text(errors="ignore")
required_source = [
    "ok, result, error = guard.execute",
    "task = self.queue.complete(task, result)",
]
missing_source = [x for x in required_source if x not in dtext]
print("CURRENT_RESULT_FLOW_MISSING=", missing_source)
if missing_source:
    raise SystemExit("V65_79_ABORT=current_dispatcher_result_flow_not_verified")
print("CURRENT_DISPATCHER_RESULT_FLOW=VERIFIED")

if not DB.exists():
    raise SystemExit("V65_79_ABORT=execution_kernel_db_missing")

def load_json_tasks():
    tasks = {}
    unreadable = []
    for p in sorted(QUEUE_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(errors="ignore"))
            tid = str(d.get("task_id") or p.stem)
            d["_path"] = str(p)
            tasks[tid] = d
        except Exception as exc:
            unreadable.append((str(p), type(exc).__name__, str(exc)))
    return tasks, unreadable

def read_db():
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        rows = [dict(r) for r in con.execute(
            "SELECT task_id,idempotency_key,task_type,priority,state,assigned_agent,"
            "attempts,max_attempts,created_at_unix,updated_at_unix,next_attempt_unix,"
            "goal_id,stage,depends_on_stage,payload_json,result_json,last_error FROM tasks"
        ).fetchall()]
    finally:
        con.close()
    return integrity, rows

json_tasks, unreadable = load_json_tasks()
integrity_before, db_rows = read_db()

print("JSON_TASKS_BEFORE=", len(json_tasks))
print("UNREADABLE_JSON_BEFORE=", len(unreadable))
print("DB_TASKS_BEFORE=", len(db_rows))
print("DB_INTEGRITY_BEFORE=", integrity_before)

if unreadable:
    raise SystemExit("V65_79_ABORT=unreadable_json")
if integrity_before != "ok":
    raise SystemExit("V65_79_ABORT=db_integrity_failed")

db_by_id = {str(r["task_id"]): r for r in db_rows}
db_by_key = {
    str(r.get("idempotency_key")): r
    for r in db_rows
    if str(r.get("idempotency_key") or "")
}

# ----- Identify JSON duplicate idempotency keys -----
json_by_key = defaultdict(list)
for tid, d in json_tasks.items():
    key = str(d.get("idempotency_key") or "")
    if key:
        json_by_key[key].append(d)

dup_groups = {k:v for k,v in json_by_key.items() if len(v) > 1}
print("JSON_DUPLICATE_IDEMPOTENCY_KEYS_BEFORE=", len(dup_groups))

# Only repair semantically exact duplicates where:
# 1) one canonical task is already COMPLETED,
# 2) SQLite's unique-key owner is exactly that completed task,
# 3) all duplicate records describe the same goal/stage/type,
# 4) the noncanonical record is nonterminal.
duplicate_repairs = []

for key, group in dup_groups.items():
    owner = db_by_key.get(key)
    if not owner:
        print("AMBIGUOUS_DUPLICATE=no_db_key_owner", key)
        continue

    owner_tid = str(owner["task_id"])
    owner_json = json_tasks.get(owner_tid)

    if not owner_json or str(owner.get("state")) != "COMPLETED" or str(owner_json.get("state")) != "COMPLETED":
        print("AMBIGUOUS_DUPLICATE=owner_not_completed", key, owner_tid)
        continue

    op = owner_json.get("payload") if isinstance(owner_json.get("payload"), dict) else {}
    canonical_sig = (
        str(owner_json.get("task_type")),
        str(op.get("goal_id")),
        str(op.get("stage")),
    )

    for d in group:
        tid = str(d.get("task_id"))
        if tid == owner_tid:
            continue

        dp = d.get("payload") if isinstance(d.get("payload"), dict) else {}
        sig = (
            str(d.get("task_type")),
            str(dp.get("goal_id")),
            str(dp.get("stage")),
        )
        state = str(d.get("state"))

        if sig != canonical_sig:
            print("AMBIGUOUS_DUPLICATE=semantic_mismatch", key, tid)
            continue
        if state not in {"QUEUED", "CLAIMED", "RUNNING"}:
            print("AMBIGUOUS_DUPLICATE=unexpected_duplicate_state", key, tid, state)
            continue
        if tid not in db_by_id:
            print("AMBIGUOUS_DUPLICATE=duplicate_task_missing_db_row", key, tid)
            continue

        duplicate_repairs.append({
            "key": key,
            "canonical_task_id": owner_tid,
            "duplicate_task_id": tid,
            "duplicate_state": state,
            "goal_id": dp.get("goal_id"),
            "stage": dp.get("stage"),
            "task_type": d.get("task_type"),
        })

print("SAFE_SEMANTIC_DUPLICATE_REPAIRS=", len(duplicate_repairs))
for x in duplicate_repairs:
    print("DUPLICATE_REPAIR_CANDIDATE=", json.dumps(x, sort_keys=True))

if dup_groups and len(duplicate_repairs) != sum(len(v)-1 for v in dup_groups.values()):
    raise SystemExit("V65_79_ABORT=not_all_duplicate_keys_are_unambiguous")

# ----- Identify historical NameError(result) projection mismatches -----
historical_retry = []
other_state_mismatches = []

for tid, jt in json_tasks.items():
    dr = db_by_id.get(tid)
    if not dr:
        continue

    js = str(jt.get("state"))
    ds = str(dr.get("state"))
    if js == ds:
        continue

    db_error = str(dr.get("last_error") or "")
    json_key = str(jt.get("idempotency_key") or "")
    db_key = str(dr.get("idempotency_key") or "")

    is_known_result_bug = (
        js == "QUEUED"
        and ds == "FAILED"
        and "NameError" in db_error
        and "result" in db_error
        and "not defined" in db_error
        and str(jt.get("task_type")) == str(dr.get("task_type"))
        and json_key == db_key
    )

    if is_known_result_bug:
        historical_retry.append({
            "task_id": tid,
            "idempotency_key": json_key,
            "task_type": jt.get("task_type"),
            "json_attempts": jt.get("attempts"),
            "json_max_attempts": jt.get("max_attempts"),
            "db_attempts": dr.get("attempts"),
            "db_max_attempts": dr.get("max_attempts"),
            "db_last_error": db_error,
        })
    else:
        other_state_mismatches.append({
            "task_id": tid,
            "json_state": js,
            "db_state": ds,
            "json_key": json_key,
            "db_key": db_key,
            "db_last_error": db_error,
        })

print("KNOWN_HISTORICAL_RESULT_BUG_RETRIES=", len(historical_retry))
print("OTHER_STATE_MISMATCHES=", len(other_state_mismatches))

for x in historical_retry[:30]:
    print("HISTORICAL_RETRY_CANDIDATE=", json.dumps(x, sort_keys=True))

for x in other_state_mismatches[:20]:
    print("OTHER_MISMATCH=", json.dumps(x, sort_keys=True))

# The current crash leaves a CLAIMED JSON task with a DB row that was not
# updated because the JSON write happened before the failed SQLite upsert.
# That mismatch is expected if it is exactly one of the duplicate repairs.
allowed_duplicate_ids = {x["duplicate_task_id"] for x in duplicate_repairs}
unexpected_other = [
    x for x in other_state_mismatches
    if x["task_id"] not in allowed_duplicate_ids
]
print("UNEXPECTED_OTHER_STATE_MISMATCHES=", len(unexpected_other))
if unexpected_other:
    raise SystemExit("V65_79_ABORT=unexpected_state_mismatch_requires_manual_review")

if not duplicate_repairs and not historical_retry:
    print("V65_79_NOTHING_TO_REPAIR=TRUE")
    raise SystemExit(0)

# ----- Full rollback snapshot before mutation -----
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
    member_count = len(tf.getmembers())

print("RUNTIME_SNAPSHOT_DB=", db_copy)
print("RUNTIME_SNAPSHOT_QUEUE=", archive)
print("SNAPSHOT_ARCHIVE_MEMBERS=", member_count)
print("ROLLBACK_SNAPSHOT=PASS")

now = time.time()

# ----- Repair duplicate semantic tasks -----
# The completed canonical task keeps the original idempotency key.
# The redundant duplicate becomes CANCELLED with a unique tombstone key.
for item in duplicate_repairs:
    dup_tid = item["duplicate_task_id"]
    canonical_tid = item["canonical_task_id"]
    old_key = item["key"]
    tombstone = f"reconciled-duplicate:{dup_tid}:{STAMP}"

    if tombstone in db_by_key or tombstone in json_by_key:
        raise SystemExit("V65_79_ABORT=tombstone_key_collision")

    jt = dict(json_tasks[dup_tid])
    jt.pop("_path", None)
    jt["idempotency_key"] = tombstone
    jt["state"] = "CANCELLED"
    jt["assigned_agent"] = None
    jt["updated_at_unix"] = now
    jt["last_error"] = f"semantic_duplicate_already_completed:{canonical_tid}"
    jt["result"] = {
        "cancelled": True,
        "reason": "semantic_duplicate_already_completed",
        "canonical_task_id": canonical_tid,
        "original_idempotency_key": old_key,
    }

    path = QUEUE_DIR / f"{dup_tid}.json"
    tmp = path.with_suffix(".json.v65_79.tmp")
    tmp.write_text(json.dumps(jt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    con = sqlite3.connect(str(DB), timeout=30)
    try:
        con.execute("BEGIN IMMEDIATE")
        cur = con.execute(
            "UPDATE tasks SET idempotency_key=?, state='CANCELLED', assigned_agent=NULL, "
            "updated_at_unix=?, result_json=?, last_error=? WHERE task_id=?",
            (
                tombstone,
                now,
                json.dumps(jt["result"], sort_keys=True),
                jt["last_error"],
                dup_tid,
            ),
        )
        if cur.rowcount != 1:
            raise RuntimeError(f"duplicate_db_update_rowcount:{dup_tid}:{cur.rowcount}")
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

    tmp.replace(path)
    print("DUPLICATE_CANCELLED=", dup_tid, "CANONICAL=", canonical_tid, "TOMBSTONE=", tombstone)

# Refresh DB ownership map after duplicate repair.
integrity_mid, db_rows_mid = read_db()
if integrity_mid != "ok":
    raise SystemExit("V65_79_FAIL=db_integrity_after_duplicate_repair")

# ----- Retry only historical NameError(result) failures -----
# Current source has already been verified to use the corrected result flow.
for item in historical_retry:
    tid = item["task_id"]
    jt = dict(json_tasks[tid])
    jt.pop("_path", None)

    # Do not resurrect a task that was part of the duplicate cancellation.
    if tid in allowed_duplicate_ids:
        continue

    jt["state"] = "QUEUED"
    jt["assigned_agent"] = None
    jt["attempts"] = 0
    jt["updated_at_unix"] = now
    jt["next_attempt_unix"] = now
    jt["result"] = None
    jt["last_error"] = None

    path = QUEUE_DIR / f"{tid}.json"
    tmp = path.with_suffix(".json.v65_79.tmp")
    tmp.write_text(json.dumps(jt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    con = sqlite3.connect(str(DB), timeout=30)
    try:
        con.execute("BEGIN IMMEDIATE")
        cur = con.execute(
            "UPDATE tasks SET state='QUEUED', assigned_agent=NULL, attempts=0, "
            "updated_at_unix=?, next_attempt_unix=?, result_json=NULL, last_error=NULL "
            "WHERE task_id=? AND state='FAILED'",
            (now, now, tid),
        )
        if cur.rowcount != 1:
            raise RuntimeError(f"historical_retry_db_update_rowcount:{tid}:{cur.rowcount}")
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

    tmp.replace(path)
    print("HISTORICAL_RESULT_FAILURE_REQUEUED=", tid)

# ----- Post-repair verification -----
json_after, unreadable_after = load_json_tasks()
integrity_after, db_after = read_db()
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
        json_after_by_key[key].append(d)

dup_after = {k:v for k,v in json_after_by_key.items() if len(v) > 1}
conflicts_after = []
state_mismatches_after = []

for tid, jt in json_after.items():
    dr = db_after_by_id.get(tid)
    if not dr:
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
        conflicts_after.append({
            "key": key,
            "json_task_id": tid,
            "db_owner_task_id": owner["task_id"],
        })

print("DB_INTEGRITY_AFTER=", integrity_after)
print("JSON_UNREADABLE_AFTER=", len(unreadable_after))
print("JSON_DUPLICATE_IDEMPOTENCY_KEYS_AFTER=", len(dup_after))
print("IDEMPOTENCY_OWNER_CONFLICTS_AFTER=", len(conflicts_after))
print("STATE_MISMATCHES_AFTER=", len(state_mismatches_after))

json_states_after = Counter(str(d.get("state") or "UNKNOWN") for d in json_after.values())
db_states_after = Counter(str(d.get("state") or "UNKNOWN") for d in db_after)

print("JSON_STATE_COUNTS_AFTER=", dict(sorted(json_states_after.items())))
print("DB_STATE_COUNTS_AFTER=", dict(sorted(db_states_after.items())))

if integrity_after != "ok":
    raise SystemExit("V65_79_FAIL=db_integrity_after")
if unreadable_after:
    raise SystemExit("V65_79_FAIL=unreadable_json_after")
if dup_after:
    raise SystemExit("V65_79_FAIL=json_duplicate_keys_remain")
if conflicts_after:
    raise SystemExit("V65_79_FAIL=idempotency_owner_conflicts_remain")
if state_mismatches_after:
    raise SystemExit("V65_79_FAIL=state_projection_mismatches_remain")

report = {
    "version": "V65.79",
    "timestamp": STAMP,
    "duplicate_repairs": duplicate_repairs,
    "historical_result_bug_retries": historical_retry,
    "json_state_counts_after": dict(json_states_after),
    "db_state_counts_after": dict(db_states_after),
    "rollback_snapshot_dir": str(SNAP_DIR),
}
rp = REPORT_DIR / f"v65_79_targeted_projection_reconciliation_{STAMP}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

print("REPORT=", rp)
print("ROLLBACK_AVAILABLE=", SNAP_DIR)
print("V65_79_DUPLICATE_RECONCILIATION=PASS")
print("V65_79_HISTORICAL_RESULT_RETRY_RESET=PASS")
print("V65_79_PROJECTION_ALIGNMENT=PASS")
print("V65_79_COMPLETE")
PY
