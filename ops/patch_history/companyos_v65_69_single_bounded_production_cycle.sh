#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.69 SINGLE BOUNDED PRODUCTION CYCLE ====="

python - <<'PY'
from pathlib import Path
import ast
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
from collections import Counter

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
QUEUE_DIR = RUNTIME / "task_queue"
DB = RUNTIME / "execution_kernel.sqlite3"
REPORT_DIR = RUNTIME / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

STAMP = int(time.time())
SNAP_DIR = RUNTIME / "checkpoints" / f"v65_69_runtime_before_{STAMP}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

print("REPO=", ROOT)
print("RUNTIME=", RUNTIME)
print("SNAPSHOT_DIR=", SNAP_DIR)

# ---- Gate 1: known-good local dispatcher contract still present ----
dispatcher_path = ROOT / "companyos/runtime/autonomous_task_dispatcher.py"
registry_path = ROOT / "companyos/runtime/default_specialist_registry.py"

dispatcher_text = dispatcher_path.read_text(errors="ignore")
required = [
    "V35_1_FENCED_HANDLER_CALL",
    "V27_9_4A_LIVE_HANDLER_TIMEOUT",
    "run_bounded(lambda: handler(task))",
    "_v35_guard.execute",
]
missing = [x for x in required if x not in dispatcher_text]
print("DISPATCH_CONTRACT_MISSING=", missing)
if missing:
    raise SystemExit("V65_69_ABORT=dispatcher_contract_missing")

# ---- Gate 2: default specialists remain internal-only ----
registry_text = registry_path.read_text(errors="ignore")
tree = ast.parse(registry_text)
imports = set()
for n in ast.walk(tree):
    if isinstance(n, ast.Import):
        imports.update(a.name.split(".")[0] for a in n.names)
    elif isinstance(n, ast.ImportFrom) and n.module:
        imports.add(n.module.split(".")[0])

blocked = {
    "requests", "httpx", "urllib", "socket", "subprocess",
    "web3", "solana", "solders", "paramiko", "ftplib", "smtplib"
}
present_blocked = sorted(blocked.intersection(imports))
print("DEFAULT_SPECIALIST_BLOCKED_IMPORTS=", present_blocked)
if present_blocked:
    raise SystemExit("V65_69_ABORT=external_specialist_import_detected")

compact = registry_text.replace(" ", "")
if '"external_research_performed":False' not in compact:
    raise SystemExit("V65_69_ABORT=research_internal_only_marker_missing")
if '"external_deployment_performed":False' not in compact:
    raise SystemExit("V65_69_ABORT=build_internal_only_marker_missing")

print("INTERNAL_ONLY_EXECUTION_GATE=PASS")

def queue_counts():
    counts = Counter()
    total = 0
    unreadable = []
    for p in QUEUE_DIR.glob("*.json"):
        try:
            d = json.loads(p.read_text(errors="ignore"))
            counts[str(d.get("state") or "UNKNOWN")] += 1
            total += 1
        except Exception:
            unreadable.append(str(p))
    return total, dict(sorted(counts.items())), unreadable

before_total, before_counts, unreadable = queue_counts()
print("QUEUE_TOTAL_BEFORE=", before_total)
print("QUEUE_COUNTS_BEFORE=", before_counts)
print("UNREADABLE_QUEUE_FILES_BEFORE=", len(unreadable))

if unreadable:
    raise SystemExit("V65_69_ABORT=unreadable_queue_files")

# ---- Gate 3: durable DB integrity ----
if not DB.exists():
    raise SystemExit("V65_69_ABORT=execution_kernel_db_missing")

con = sqlite3.connect(str(DB))
try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    db_rows_before = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
finally:
    con.close()

print("DB_INTEGRITY_BEFORE=", integrity)
print("DB_TASK_ROWS_BEFORE=", db_rows_before)
if integrity != "ok":
    raise SystemExit("V65_69_ABORT=db_integrity_failed")

# ---- Rollback snapshot of live queue + durable DB ----
# Copy DB with SQLite backup API for a consistent snapshot.
db_copy = SNAP_DIR / "execution_kernel.sqlite3"
src = sqlite3.connect(str(DB))
dst = sqlite3.connect(str(db_copy))
try:
    src.backup(dst)
finally:
    dst.close()
    src.close()

# Archive task_queue and small dispatcher cursor only.
archive = SNAP_DIR / "task_queue_before.tar.gz"
with tarfile.open(archive, "w:gz") as tf:
    if QUEUE_DIR.exists():
        tf.add(QUEUE_DIR, arcname="task_queue")
    cursor = RUNTIME / "dispatcher_scan_cursor.txt"
    if cursor.exists():
        tf.add(cursor, arcname="dispatcher_scan_cursor.txt")

print("RUNTIME_SNAPSHOT_DB=", db_copy)
print("RUNTIME_SNAPSHOT_QUEUE=", archive)

# Validate snapshot archive before any execution.
with tarfile.open(archive, "r:gz") as tf:
    members = tf.getmembers()
print("SNAPSHOT_ARCHIVE_MEMBERS=", len(members))
print("ROLLBACK_SNAPSHOT=PASS")

# ---- Execute exactly ONE bounded cycle on the actual runtime queue ----
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

q = AutonomousTaskQueue()
loop = AutonomousGoalExecutionLoop(q)

handlers = sorted(loop.dispatcher.dispatcher.handlers.keys())
print("REGISTERED_LIVE_HANDLERS=", handlers)

if handlers != ["build", "planning", "research"]:
    raise SystemExit("V65_69_ABORT=unexpected_live_handler_set")

result_list = loop.run_bounded_batch(max_dispatches=1)
print("RAW_BATCH_RESULT=", result_list)

if len(result_list) != 1:
    raise SystemExit("V65_69_ABORT=unexpected_batch_result_count")

r = result_list[0]
print("DISPATCHED=", r.dispatched)
print("TASK_ID=", r.task_id)
print("AGENT_NAME=", r.agent_name)
print("STATE=", r.state)
print("REASON=", r.reason)
print("COUNTS_FROM_LOOP=", {
    "completed": r.completed_tasks,
    "failed": r.failed_tasks,
    "queued": r.queued_tasks,
    "running": r.running_tasks,
})

changed_task = None
if r.task_id:
    try:
        changed_task = q.load(r.task_id)
        print("TASK_TYPE=", changed_task.task_type)
        print("TASK_ATTEMPTS=", changed_task.attempts)
        print("TASK_LAST_ERROR=", changed_task.last_error)
        print("TASK_PAYLOAD=", json.dumps(changed_task.payload, sort_keys=True, default=str))
        print("TASK_RESULT=", json.dumps(changed_task.result, sort_keys=True, default=str))
    except Exception as exc:
        print("TASK_RELOAD_ERROR=", type(exc).__name__, str(exc))
        raise

# ---- Post-cycle integrity ----
after_total, after_counts, unreadable_after = queue_counts()
print("QUEUE_TOTAL_AFTER=", after_total)
print("QUEUE_COUNTS_AFTER=", after_counts)
print("UNREADABLE_QUEUE_FILES_AFTER=", len(unreadable_after))

con = sqlite3.connect(str(DB))
try:
    integrity_after = con.execute("PRAGMA integrity_check").fetchone()[0]
    db_rows_after = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
finally:
    con.close()

print("DB_INTEGRITY_AFTER=", integrity_after)
print("DB_TASK_ROWS_AFTER=", db_rows_after)

if unreadable_after:
    raise SystemExit("V65_69_FAIL=queue_file_corruption")
if integrity_after != "ok":
    raise SystemExit("V65_69_FAIL=db_integrity_after")
if after_total != before_total:
    raise SystemExit("V65_69_FAIL=queue_cardinality_changed")
if db_rows_after != db_rows_before:
    raise SystemExit("V65_69_FAIL=db_cardinality_changed")

# This cycle is allowed to mutate exactly one existing queued task.
if r.dispatched:
    if not r.task_id:
        raise SystemExit("V65_69_FAIL=dispatched_without_task_id")
    if changed_task.task_type not in {"research", "planning", "build"}:
        raise SystemExit("V65_69_FAIL=unexpected_task_type")
    if r.reason not in {"completed", "handler_failed"}:
        raise SystemExit("V65_69_FAIL=unexpected_dispatch_reason")
else:
    if r.reason != "no_dependency_ready_task":
        raise SystemExit("V65_69_FAIL=unexpected_idle_reason")

report = {
    "version": "V65.69",
    "timestamp": STAMP,
    "before_total": before_total,
    "before_counts": before_counts,
    "after_total": after_total,
    "after_counts": after_counts,
    "db_rows_before": db_rows_before,
    "db_rows_after": db_rows_after,
    "dispatched": r.dispatched,
    "task_id": r.task_id,
    "agent_name": r.agent_name,
    "state": r.state,
    "reason": r.reason,
    "rollback_snapshot_dir": str(SNAP_DIR),
}
rp = REPORT_DIR / f"v65_69_single_bounded_production_cycle_{STAMP}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print("REPORT=", rp)

if r.dispatched and r.reason == "completed":
    print("V65_69_SINGLE_PRODUCTION_CYCLE=PASS_COMPLETED")
elif r.dispatched and r.reason == "handler_failed":
    print("V65_69_SINGLE_PRODUCTION_CYCLE=PASS_OBSERVED_HANDLER_FAILURE")
else:
    print("V65_69_SINGLE_PRODUCTION_CYCLE=PASS_IDLE")

print("ROLLBACK_AVAILABLE=", SNAP_DIR)
print("V65_69_COMPLETE")
PY
