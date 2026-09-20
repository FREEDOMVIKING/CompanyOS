#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.71 PROGRESSIVE PRODUCTION BATCH x32 ====="

python - <<'PY'
from pathlib import Path
import ast
import json
import sqlite3
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
SNAP_DIR = RUNTIME / "checkpoints" / f"v65_71_runtime_before_{STAMP}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

print("REPO=", ROOT)
print("RUNTIME=", RUNTIME)
print("SNAPSHOT_DIR=", SNAP_DIR)

# ----- Internal-only safety gate -----
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
    raise SystemExit("V65_71_ABORT=dispatcher_contract_missing")

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
blocked_present = sorted(blocked.intersection(imports))
print("DEFAULT_SPECIALIST_BLOCKED_IMPORTS=", blocked_present)
if blocked_present:
    raise SystemExit("V65_71_ABORT=external_specialist_import_detected")

compact = registry_text.replace(" ", "")
if '"external_research_performed":False' not in compact:
    raise SystemExit("V65_71_ABORT=research_internal_only_marker_missing")
if '"external_deployment_performed":False' not in compact:
    raise SystemExit("V65_71_ABORT=build_internal_only_marker_missing")

print("INTERNAL_ONLY_EXECUTION_GATE=PASS")

def queue_snapshot():
    counts = Counter()
    types = Counter()
    total = 0
    unreadable = []
    for p in QUEUE_DIR.glob("*.json"):
        try:
            d = json.loads(p.read_text(errors="ignore"))
        except Exception:
            unreadable.append(str(p))
            continue
        total += 1
        counts[str(d.get("state") or "UNKNOWN")] += 1
        types[str(d.get("task_type") or "UNKNOWN")] += 1
    return total, dict(sorted(counts.items())), dict(sorted(types.items())), unreadable

before_total, before_counts, before_types, unreadable = queue_snapshot()
print("QUEUE_TOTAL_BEFORE=", before_total)
print("QUEUE_COUNTS_BEFORE=", before_counts)
print("QUEUE_TYPES_BEFORE=", before_types)
print("UNREADABLE_QUEUE_FILES_BEFORE=", len(unreadable))
if unreadable:
    raise SystemExit("V65_71_ABORT=unreadable_queue_files")

if not DB.exists():
    raise SystemExit("V65_71_ABORT=execution_kernel_db_missing")

con = sqlite3.connect(str(DB))
try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    db_rows_before = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
finally:
    con.close()

delta_before = before_total - db_rows_before
print("DB_INTEGRITY_BEFORE=", integrity)
print("DB_TASK_ROWS_BEFORE=", db_rows_before)
print("QUEUE_MINUS_DB_DELTA_BEFORE=", delta_before)

if integrity != "ok":
    raise SystemExit("V65_71_ABORT=db_integrity_failed")

# ----- Rollback snapshot -----
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
    if QUEUE_DIR.exists():
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

# ----- Run 32 one-at-a-time bounded production dispatches -----
# One-at-a-time is deliberate: it lets us stop immediately on the first failure.
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

q = AutonomousTaskQueue()
loop = AutonomousGoalExecutionLoop(q)

handlers = sorted(loop.dispatcher.dispatcher.handlers.keys())
print("REGISTERED_LIVE_HANDLERS=", handlers)
if handlers != ["build", "planning", "research"]:
    raise SystemExit("V65_71_ABORT=unexpected_live_handler_set")

records = []
completed_ids = []
completed_types = Counter()
failed_ids = []
idle_seen = False

for idx in range(1, 33):
    one = loop.run_bounded_batch(max_dispatches=1)
    if len(one) != 1:
        raise SystemExit(f"V65_71_FAIL=result_count_at_{idx}:{len(one)}")

    r = one[0]
    print(f"RESULT_{idx:02d}=", r)

    rec = {
        "index": idx,
        "dispatched": r.dispatched,
        "task_id": r.task_id,
        "agent_name": r.agent_name,
        "state": r.state,
        "reason": r.reason,
        "completed_tasks": r.completed_tasks,
        "failed_tasks": r.failed_tasks,
        "queued_tasks": r.queued_tasks,
        "running_tasks": r.running_tasks,
    }

    if not r.dispatched:
        if r.reason != "no_dependency_ready_task":
            raise SystemExit(f"V65_71_FAIL=unexpected_idle_reason:{r.reason}")
        idle_seen = True
        records.append(rec)
        print("EARLY_IDLE_AT=", idx)
        break

    if not r.task_id:
        raise SystemExit(f"V65_71_FAIL=missing_task_id_at_{idx}")

    task = q.load(r.task_id)
    rec["task_type"] = task.task_type
    rec["attempts"] = task.attempts
    rec["last_error"] = task.last_error

    print(f"TASK_{idx:02d}_TYPE=", task.task_type)
    print(f"TASK_{idx:02d}_STATE=", task.state)
    print(f"TASK_{idx:02d}_ATTEMPTS=", task.attempts)
    print(f"TASK_{idx:02d}_LAST_ERROR=", task.last_error)

    if task.task_type not in {"research", "planning", "build"}:
        raise SystemExit(f"V65_71_FAIL=unexpected_task_type:{task.task_type}")

    result_payload = task.result if isinstance(task.result, dict) else {}
    ext_flags = {
        k: v for k, v in result_payload.items()
        if k in {
            "external_research_performed",
            "external_deployment_performed",
            "external_action_performed",
            "transaction_performed",
        }
    }
    rec["external_flags"] = ext_flags
    print(f"TASK_{idx:02d}_EXTERNAL_FLAGS=", ext_flags)

    if any(bool(v) for v in ext_flags.values()):
        raise SystemExit(f"V65_71_FAIL=unexpected_external_action_flag:{r.task_id}")

    if r.reason == "completed":
        completed_ids.append(r.task_id)
        completed_types[task.task_type] += 1
    elif r.reason == "handler_failed":
        failed_ids.append(r.task_id)
        records.append(rec)
        print("STOP_ON_FIRST_HANDLER_FAILURE=TRUE")
        raise SystemExit(f"V65_71_FAIL=handler_failed:{r.task_id}")
    else:
        records.append(rec)
        raise SystemExit(f"V65_71_FAIL=unexpected_dispatch_reason:{r.reason}")

    records.append(rec)

print("COMPLETED_IDS=", completed_ids)
print("COMPLETED_TYPE_COUNTS=", dict(sorted(completed_types.items())))
print("FAILED_IDS=", failed_ids)
print("IDLE_SEEN=", idle_seen)

# ----- Post-run invariants -----
after_total, after_counts, after_types, unreadable_after = queue_snapshot()
print("QUEUE_TOTAL_AFTER=", after_total)
print("QUEUE_COUNTS_AFTER=", after_counts)
print("QUEUE_TYPES_AFTER=", after_types)
print("UNREADABLE_QUEUE_FILES_AFTER=", len(unreadable_after))

con = sqlite3.connect(str(DB))
try:
    integrity_after = con.execute("PRAGMA integrity_check").fetchone()[0]
    db_rows_after = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
finally:
    con.close()

delta_after = after_total - db_rows_after
print("DB_INTEGRITY_AFTER=", integrity_after)
print("DB_TASK_ROWS_AFTER=", db_rows_after)
print("QUEUE_MINUS_DB_DELTA_AFTER=", delta_after)

if unreadable_after:
    raise SystemExit("V65_71_FAIL=queue_file_corruption")
if integrity_after != "ok":
    raise SystemExit("V65_71_FAIL=db_integrity_after")
if after_total != before_total:
    raise SystemExit("V65_71_FAIL=queue_cardinality_changed")
if db_rows_after != db_rows_before:
    raise SystemExit("V65_71_FAIL=db_cardinality_changed")
if delta_after != delta_before:
    raise SystemExit("V65_71_FAIL=queue_db_delta_changed")

done = len(completed_ids)
expected_completed = before_counts.get("COMPLETED", 0) + done
expected_queued = before_counts.get("QUEUED", 0) - done
actual_completed = after_counts.get("COMPLETED", 0)
actual_queued = after_counts.get("QUEUED", 0)

print("EXPECTED_COMPLETED_AFTER=", expected_completed)
print("ACTUAL_COMPLETED_AFTER=", actual_completed)
print("EXPECTED_QUEUED_AFTER=", expected_queued)
print("ACTUAL_QUEUED_AFTER=", actual_queued)

if actual_completed != expected_completed:
    raise SystemExit("V65_71_FAIL=completed_count_mismatch")
if actual_queued != expected_queued:
    raise SystemExit("V65_71_FAIL=queued_count_mismatch")

report = {
    "version": "V65.71",
    "timestamp": STAMP,
    "before_total": before_total,
    "before_counts": before_counts,
    "after_total": after_total,
    "after_counts": after_counts,
    "db_rows_before": db_rows_before,
    "db_rows_after": db_rows_after,
    "queue_minus_db_delta_before": delta_before,
    "queue_minus_db_delta_after": delta_after,
    "completed_ids": completed_ids,
    "completed_type_counts": dict(completed_types),
    "failed_ids": failed_ids,
    "idle_seen": idle_seen,
    "records": records,
    "rollback_snapshot_dir": str(SNAP_DIR),
}
rp = REPORT_DIR / f"v65_71_progressive_production_batch32_{STAMP}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

print("REPORT=", rp)
print("ROLLBACK_AVAILABLE=", SNAP_DIR)
print("V65_71_BATCH_COMPLETED=", done)
print("V65_71_PRODUCTION_BATCH=PASS")
print("V65_71_COMPLETE")
PY
