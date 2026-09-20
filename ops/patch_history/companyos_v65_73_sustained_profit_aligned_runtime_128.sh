#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.73 SUSTAINED PROFIT-ALIGNED RUNTIME x128 ====="

python - <<'PY'
from pathlib import Path
import ast, json, re, sqlite3, tarfile, time
from collections import Counter

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
QUEUE_DIR = RUNTIME / "task_queue"
DB = RUNTIME / "execution_kernel.sqlite3"
REPORT_DIR = RUNTIME / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

STAMP = int(time.time())
SNAP_DIR = RUNTIME / "checkpoints" / f"v65_73_runtime_before_{STAMP}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

print("REPO=", ROOT)
print("RUNTIME=", RUNTIME)
print("SNAPSHOT_DIR=", SNAP_DIR)

# ---- Profit objective gate ----
profit_terms = re.compile(
    r"(primary economic directive|maximi[sz]e.{0,80}profit|profitability|expected[_ ]profit|net profit|risk[- ]adjusted|enterprise value|expected roi|return on investment)",
    re.I | re.S,
)

explicit_directive = False
for p in sorted((ROOT / "companyos").rglob("*.py")):
    ps = str(p).lower()
    if "__pycache__" in ps or ".v65_" in p.name.lower() or "backup" in p.name.lower():
        continue
    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        continue
    low = txt.lower()
    if (
        "primary economic directive" in low
        or ("maximize" in low and "profit" in low)
        or ("maximise" in low and "profit" in low)
    ):
        explicit_directive = True
        print("PROFIT_DIRECTIVE_SOURCE=", p.relative_to(ROOT))

if not explicit_directive:
    raise SystemExit("V65_73_ABORT=hardcoded_profit_directive_not_found")

print("HARD_CODED_PROFIT_DIRECTIVE=CONFIRMED")

# ---- Dispatcher / handler safety gate ----
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
    raise SystemExit("V65_73_ABORT=dispatcher_contract_missing")

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
    raise SystemExit("V65_73_ABORT=external_specialist_import_detected")

compact = registry_text.replace(" ", "")
if '"external_research_performed":False' not in compact:
    raise SystemExit("V65_73_ABORT=research_internal_only_marker_missing")
if '"external_deployment_performed":False' not in compact:
    raise SystemExit("V65_73_ABORT=build_internal_only_marker_missing")

print("INTERNAL_ONLY_EXECUTION_GATE=PASS")

def queue_snapshot():
    counts = Counter()
    total = 0
    unreadable = []
    queued_profit_ok = 0
    queued_profit_missing = []
    for p in QUEUE_DIR.glob("*.json"):
        try:
            d = json.loads(p.read_text(errors="ignore"))
        except Exception:
            unreadable.append(str(p))
            continue

        total += 1
        state = str(d.get("state") or "UNKNOWN")
        counts[state] += 1

        if state == "QUEUED":
            payload = d.get("payload")
            txt = json.dumps(payload, sort_keys=True, default=str) if isinstance(payload, dict) else ""
            if profit_terms.search(txt):
                queued_profit_ok += 1
            elif len(queued_profit_missing) < 20:
                queued_profit_missing.append(d.get("task_id"))

    return total, dict(sorted(counts.items())), unreadable, queued_profit_ok, queued_profit_missing

before_total, before_counts, unreadable, profit_ok, profit_missing = queue_snapshot()
print("QUEUE_TOTAL_BEFORE=", before_total)
print("QUEUE_COUNTS_BEFORE=", before_counts)
print("UNREADABLE_QUEUE_FILES_BEFORE=", len(unreadable))
print("QUEUED_PROFIT_ALIGNED_BEFORE=", profit_ok)
print("QUEUED_PROFIT_MISSING_SAMPLE=", profit_missing)

queued_before = before_counts.get("QUEUED", 0)
if unreadable:
    raise SystemExit("V65_73_ABORT=unreadable_queue_files")
if profit_ok != queued_before:
    raise SystemExit("V65_73_ABORT=queued_profit_alignment_not_full")

print("CURRENT_QUEUE_PROFIT_ALIGNMENT=FULL")

# ---- DB integrity ----
if not DB.exists():
    raise SystemExit("V65_73_ABORT=execution_kernel_db_missing")

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
    raise SystemExit("V65_73_ABORT=db_integrity_failed")

# ---- Rollback snapshot ----
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
    print("SNAPSHOT_ARCHIVE_MEMBERS=", len(tf.getmembers()))

print("ROLLBACK_SNAPSHOT=PASS")

# ---- Sustained bounded production execution ----
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

q = AutonomousTaskQueue()
loop = AutonomousGoalExecutionLoop(q)

handlers = sorted(loop.dispatcher.dispatcher.handlers.keys())
print("REGISTERED_LIVE_HANDLERS=", handlers)
if handlers != ["build", "planning", "research"]:
    raise SystemExit("V65_73_ABORT=unexpected_live_handler_set")

completed_ids = []
completed_types = Counter()
records = []
idle_at = None

for idx in range(1, 129):
    one = loop.run_bounded_batch(max_dispatches=1)
    if len(one) != 1:
        raise SystemExit(f"V65_73_FAIL=result_count_at_{idx}:{len(one)}")

    r = one[0]
    print(f"RESULT_{idx:03d}=", r)

    rec = {
        "index": idx,
        "dispatched": r.dispatched,
        "task_id": r.task_id,
        "agent_name": r.agent_name,
        "state": r.state,
        "reason": r.reason,
    }

    if not r.dispatched:
        if r.reason != "no_dependency_ready_task":
            raise SystemExit(f"V65_73_FAIL=unexpected_idle_reason:{r.reason}")
        idle_at = idx
        records.append(rec)
        print("EARLY_IDLE_AT=", idx)
        break

    if not r.task_id:
        raise SystemExit(f"V65_73_FAIL=missing_task_id_at_{idx}")

    task = q.load(r.task_id)
    rec["task_type"] = task.task_type
    rec["attempts"] = task.attempts
    rec["last_error"] = task.last_error

    if task.task_type not in {"research", "planning", "build"}:
        raise SystemExit(f"V65_73_FAIL=unexpected_task_type:{task.task_type}")

    payload_text = json.dumps(task.payload, sort_keys=True, default=str)
    profit_aligned = bool(profit_terms.search(payload_text))
    print(f"TASK_{idx:03d}_TYPE=", task.task_type)
    print(f"TASK_{idx:03d}_STATE=", task.state)
    print(f"TASK_{idx:03d}_PROFIT_ALIGNED=", profit_aligned)
    print(f"TASK_{idx:03d}_LAST_ERROR=", task.last_error)

    if not profit_aligned:
        raise SystemExit(f"V65_73_FAIL=task_profit_objective_missing:{r.task_id}")

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
    print(f"TASK_{idx:03d}_EXTERNAL_FLAGS=", ext_flags)

    if any(bool(v) for v in ext_flags.values()):
        raise SystemExit(f"V65_73_FAIL=unexpected_external_action_flag:{r.task_id}")

    if r.reason != "completed":
        raise SystemExit(f"V65_73_FAIL=noncompleted_dispatch:{r.task_id}:{r.reason}")

    completed_ids.append(r.task_id)
    completed_types[task.task_type] += 1
    records.append(rec)

    if idx % 16 == 0:
        print(
            "PROGRESS_CHECKPOINT=",
            {
                "completed_this_run": len(completed_ids),
                "type_counts": dict(sorted(completed_types.items())),
            },
        )

print("COMPLETED_THIS_RUN=", len(completed_ids))
print("COMPLETED_TYPE_COUNTS=", dict(sorted(completed_types.items())))
print("IDLE_AT=", idle_at)

# ---- Post-run invariants ----
after_total, after_counts, unreadable_after, profit_ok_after, profit_missing_after = queue_snapshot()

print("QUEUE_TOTAL_AFTER=", after_total)
print("QUEUE_COUNTS_AFTER=", after_counts)
print("UNREADABLE_QUEUE_FILES_AFTER=", len(unreadable_after))
print("QUEUED_PROFIT_ALIGNED_AFTER=", profit_ok_after)
print("QUEUED_PROFIT_MISSING_AFTER=", profit_missing_after)

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
    raise SystemExit("V65_73_FAIL=queue_file_corruption")
if integrity_after != "ok":
    raise SystemExit("V65_73_FAIL=db_integrity_after")
if after_total != before_total:
    raise SystemExit("V65_73_FAIL=queue_cardinality_changed")
if db_rows_after != db_rows_before:
    raise SystemExit("V65_73_FAIL=db_cardinality_changed")
if delta_after != delta_before:
    raise SystemExit("V65_73_FAIL=queue_db_delta_changed")

done = len(completed_ids)
expected_completed = before_counts.get("COMPLETED", 0) + done
expected_queued = before_counts.get("QUEUED", 0) - done

print("EXPECTED_COMPLETED_AFTER=", expected_completed)
print("ACTUAL_COMPLETED_AFTER=", after_counts.get("COMPLETED", 0))
print("EXPECTED_QUEUED_AFTER=", expected_queued)
print("ACTUAL_QUEUED_AFTER=", after_counts.get("QUEUED", 0))

if after_counts.get("COMPLETED", 0) != expected_completed:
    raise SystemExit("V65_73_FAIL=completed_count_mismatch")
if after_counts.get("QUEUED", 0) != expected_queued:
    raise SystemExit("V65_73_FAIL=queued_count_mismatch")
if profit_ok_after != expected_queued:
    raise SystemExit("V65_73_FAIL=remaining_queue_profit_alignment_not_full")

report = {
    "version": "V65.73",
    "timestamp": STAMP,
    "before_counts": before_counts,
    "after_counts": after_counts,
    "completed_this_run": done,
    "completed_type_counts": dict(completed_types),
    "idle_at": idle_at,
    "queue_minus_db_delta_before": delta_before,
    "queue_minus_db_delta_after": delta_after,
    "remaining_queued_profit_aligned": profit_ok_after,
    "rollback_snapshot_dir": str(SNAP_DIR),
    "records": records,
}
rp = REPORT_DIR / f"v65_73_sustained_profit_aligned_runtime_{STAMP}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

print("REPORT=", rp)
print("ROLLBACK_AVAILABLE=", SNAP_DIR)
print("V65_73_PROFIT_ALIGNMENT_AFTER=FULL")
print("V65_73_SUSTAINED_RUNTIME=PASS")
print("V65_73_COMPLETE")
PY
