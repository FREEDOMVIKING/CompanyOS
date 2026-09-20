#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.77 POST-STARVATION-FIX LIVE DRAIN ====="

python - <<'PY'
from pathlib import Path
import ast, json, re, sqlite3, tarfile, time
from collections import Counter, defaultdict

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
QUEUE_DIR = RUNTIME / "task_queue"
DB = RUNTIME / "execution_kernel.sqlite3"
REPORT_DIR = RUNTIME / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

STOP_FILE = RUNTIME / "STOP_COMPANYOS"
STAMP = int(time.time())
SNAP_DIR = RUNTIME / "checkpoints" / f"v65_77_runtime_before_{STAMP}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

MAX_DISPATCHES = 160

print("REPO=", ROOT)
print("RUNTIME=", RUNTIME)
print("MAX_DISPATCHES=", MAX_DISPATCHES)
print("SNAPSHOT_DIR=", SNAP_DIR)

# ----- Confirm the V65.76 starvation fix is active -----
dep_path = ROOT / "companyos/runtime/dependency_aware_dispatcher.py"
dep_text = dep_path.read_text(errors="ignore")
markers = [
    "V65.76 scan-window starvation fix",
    "starvation fallback",
    "self.queue._iter_task_files()",
]
missing = [m for m in markers if m not in dep_text]
print("V65_76_MARKERS_MISSING=", missing)
if missing:
    raise SystemExit("V65_77_ABORT=v65_76_fix_not_active")
print("V65_76_FIX_ACTIVE=PASS")

profit_terms = re.compile(
    r"(primary economic directive|maximi[sz]e.{0,80}profit|profitability|expected[_ ]profit|net profit|risk[- ]adjusted|enterprise value|expected roi|return on investment)",
    re.I | re.S,
)

registry_path = ROOT / "companyos/runtime/default_specialist_registry.py"
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
    raise SystemExit("V65_77_ABORT=external_specialist_import_detected")

compact = registry_text.replace(" ", "")
if '"external_research_performed":False' not in compact:
    raise SystemExit("V65_77_ABORT=research_internal_only_marker_missing")
if '"external_deployment_performed":False' not in compact:
    raise SystemExit("V65_77_ABORT=build_internal_only_marker_missing")

print("INTERNAL_ONLY_EXECUTION_GATE=PASS")

def read_tasks():
    tasks = []
    unreadable = []
    for p in sorted(QUEUE_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(errors="ignore"))
            d["_path"] = str(p)
            tasks.append(d)
        except Exception as exc:
            unreadable.append((str(p), type(exc).__name__, str(exc)))
    return tasks, unreadable

def snapshot_counts():
    tasks, unreadable = read_tasks()
    counts = Counter(str(t.get("state") or "UNKNOWN") for t in tasks)
    queued_profit = 0
    queued_missing = []
    for t in tasks:
        if str(t.get("state")) != "QUEUED":
            continue
        payload = t.get("payload")
        txt = json.dumps(payload, sort_keys=True, default=str) if isinstance(payload, dict) else ""
        if profit_terms.search(txt):
            queued_profit += 1
        elif len(queued_missing) < 20:
            queued_missing.append(t.get("task_id"))
    return tasks, dict(sorted(counts.items())), unreadable, queued_profit, queued_missing

before_tasks, before_counts, unreadable, profit_ok, profit_missing = snapshot_counts()
before_total = len(before_tasks)

print("QUEUE_TOTAL_BEFORE=", before_total)
print("QUEUE_COUNTS_BEFORE=", before_counts)
print("UNREADABLE_BEFORE=", len(unreadable))
print("QUEUED_PROFIT_ALIGNED_BEFORE=", profit_ok)
print("QUEUED_PROFIT_MISSING_BEFORE=", profit_missing)

if unreadable:
    raise SystemExit("V65_77_ABORT=unreadable_queue_files")
if profit_ok != before_counts.get("QUEUED", 0):
    raise SystemExit("V65_77_ABORT=queue_profit_alignment_not_full")

if not DB.exists():
    raise SystemExit("V65_77_ABORT=execution_kernel_db_missing")

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
    raise SystemExit("V65_77_ABORT=db_integrity_failed")

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
    tf.add(QUEUE_DIR, arcname="task_queue")
    cursor = RUNTIME / "dispatcher_scan_cursor.txt"
    if cursor.exists():
        tf.add(cursor, arcname="dispatcher_scan_cursor.txt")

with tarfile.open(archive, "r:gz") as tf:
    print("SNAPSHOT_ARCHIVE_MEMBERS=", len(tf.getmembers()))

print("ROLLBACK_SNAPSHOT=PASS")

if STOP_FILE.exists():
    raise SystemExit("V65_77_ABORT=stop_file_present")

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

q = AutonomousTaskQueue()
loop = AutonomousGoalExecutionLoop(q)

handlers = sorted(loop.dispatcher.dispatcher.handlers.keys())
print("REGISTERED_LIVE_HANDLERS=", handlers)
if handlers != ["build", "planning", "research"]:
    raise SystemExit("V65_77_ABORT=unexpected_live_handler_set")

completed_ids = []
completed_types = Counter()
idle_at = None
start = time.time()

for idx in range(1, MAX_DISPATCHES + 1):
    if STOP_FILE.exists():
        print("STOP_FILE_DETECTED_AT=", idx)
        break

    one = loop.run_bounded_batch(max_dispatches=1)
    if len(one) != 1:
        raise SystemExit(f"V65_77_FAIL=result_count_at_{idx}:{len(one)}")

    r = one[0]

    if not r.dispatched:
        if r.reason != "no_dependency_ready_task":
            raise SystemExit(f"V65_77_FAIL=unexpected_idle_reason:{r.reason}")
        idle_at = idx
        print("IDLE_AT=", idx)
        break

    if not r.task_id:
        raise SystemExit(f"V65_77_FAIL=missing_task_id_at_{idx}")

    task = q.load(r.task_id)
    if task.task_type not in {"research", "planning", "build"}:
        raise SystemExit(f"V65_77_FAIL=unexpected_task_type:{task.task_type}")

    payload_text = json.dumps(task.payload, sort_keys=True, default=str)
    if not profit_terms.search(payload_text):
        raise SystemExit(f"V65_77_FAIL=task_profit_objective_missing:{r.task_id}")

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
    if any(bool(v) for v in ext_flags.values()):
        raise SystemExit(f"V65_77_FAIL=unexpected_external_action_flag:{r.task_id}")

    if r.reason != "completed":
        raise SystemExit(f"V65_77_FAIL=noncompleted_dispatch:{r.task_id}:{r.reason}")

    completed_ids.append(r.task_id)
    completed_types[task.task_type] += 1

    if idx <= 10 or idx % 10 == 0:
        print("PROGRESS=", {
            "dispatch_index": idx,
            "task_id": r.task_id,
            "task_type": task.task_type,
            "completed_this_run": len(completed_ids),
            "type_counts": dict(sorted(completed_types.items())),
            "elapsed_seconds": round(time.time() - start, 2),
        })

print("COMPLETED_THIS_RUN=", len(completed_ids))
print("COMPLETED_TYPE_COUNTS=", dict(sorted(completed_types.items())))
print("IDLE_AT=", idle_at)

# ----- Post-run integrity -----
after_tasks, after_counts, unreadable_after, profit_ok_after, profit_missing_after = snapshot_counts()
after_total = len(after_tasks)

print("QUEUE_TOTAL_AFTER=", after_total)
print("QUEUE_COUNTS_AFTER=", after_counts)
print("UNREADABLE_AFTER=", len(unreadable_after))
print("QUEUED_PROFIT_ALIGNED_AFTER=", profit_ok_after)
print("QUEUED_PROFIT_MISSING_AFTER=", profit_missing_after)

con = sqlite3.connect(str(DB))
con.row_factory = sqlite3.Row
try:
    integrity_after = con.execute("PRAGMA integrity_check").fetchone()[0]
    db_rows_after = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    db_rows = [dict(r) for r in con.execute(
        "SELECT task_id, task_type, state, goal_id, stage, depends_on_stage, attempts, max_attempts, last_error FROM tasks"
    ).fetchall()]
finally:
    con.close()

delta_after = after_total - db_rows_after
print("DB_INTEGRITY_AFTER=", integrity_after)
print("DB_TASK_ROWS_AFTER=", db_rows_after)
print("QUEUE_MINUS_DB_DELTA_AFTER=", delta_after)

if unreadable_after:
    raise SystemExit("V65_77_FAIL=queue_file_corruption")
if integrity_after != "ok":
    raise SystemExit("V65_77_FAIL=db_integrity_after")
if after_total != before_total:
    raise SystemExit("V65_77_FAIL=queue_cardinality_changed")
if db_rows_after != db_rows_before:
    raise SystemExit("V65_77_FAIL=db_cardinality_changed")
if delta_after != delta_before:
    raise SystemExit("V65_77_FAIL=queue_db_delta_changed")

done = len(completed_ids)
expected_completed = before_counts.get("COMPLETED", 0) + done
expected_queued = before_counts.get("QUEUED", 0) - done

print("EXPECTED_COMPLETED_AFTER=", expected_completed)
print("ACTUAL_COMPLETED_AFTER=", after_counts.get("COMPLETED", 0))
print("EXPECTED_QUEUED_AFTER=", expected_queued)
print("ACTUAL_QUEUED_AFTER=", after_counts.get("QUEUED", 0))

if after_counts.get("COMPLETED", 0) != expected_completed:
    raise SystemExit("V65_77_FAIL=completed_count_mismatch")
if after_counts.get("QUEUED", 0) != expected_queued:
    raise SystemExit("V65_77_FAIL=queued_count_mismatch")
if profit_ok_after != expected_queued:
    raise SystemExit("V65_77_FAIL=remaining_queue_profit_alignment_not_full")

# ----- Reclassify anything still queued after the repaired dispatcher runs -----
by_goal_stage_json = defaultdict(list)
for t in after_tasks:
    payload = t.get("payload")
    if isinstance(payload, dict):
        gid = payload.get("goal_id")
        stage = payload.get("stage")
        if gid is not None and stage is not None:
            by_goal_stage_json[(str(gid), str(stage))].append(t)

by_goal_stage_db = defaultdict(list)
for r in db_rows:
    gid = r.get("goal_id")
    stage = r.get("stage")
    if gid is not None and stage is not None:
        by_goal_stage_db[(str(gid), str(stage))].append(r)

classes = Counter()
samples = defaultdict(list)

for t in after_tasks:
    if str(t.get("state")) != "QUEUED":
        continue

    payload = t.get("payload")
    if not isinstance(payload, dict):
        cls = "queued_payload_not_mapping"
    else:
        gid = payload.get("goal_id")
        dep = payload.get("depends_on_stage")

        if not dep:
            cls = "ready_no_dependency"
        elif gid is None:
            cls = "blocked_missing_goal_id"
        else:
            jdeps = by_goal_stage_json.get((str(gid), str(dep)), [])
            ddeps = by_goal_stage_db.get((str(gid), str(dep)), [])
            jstates = Counter(str(x.get("state") or "UNKNOWN") for x in jdeps)
            dstates = Counter(str(x.get("state") or "UNKNOWN") for x in ddeps)

            if jstates.get("COMPLETED", 0) or dstates.get("COMPLETED", 0):
                cls = "ready_prerequisite_completed"
            elif jstates.get("FAILED", 0) or dstates.get("FAILED", 0):
                cls = "blocked_by_failed_prerequisite"
            elif jstates.get("QUEUED", 0) or dstates.get("QUEUED", 0):
                cls = "waiting_on_queued_prerequisite"
            elif jstates.get("RUNNING", 0) or dstates.get("RUNNING", 0):
                cls = "waiting_on_running_prerequisite"
            elif not jdeps and not ddeps:
                cls = "orphan_missing_prerequisite"
            else:
                cls = "blocked_other"

    classes[cls] += 1
    if len(samples[cls]) < 8:
        samples[cls].append({
            "task_id": t.get("task_id"),
            "task_type": t.get("task_type"),
            "payload": t.get("payload"),
        })

print("REMAINING_CLASSIFICATION_COUNTS=", dict(sorted(classes.items())))

for cls in sorted(samples):
    print(f"===== {cls} SAMPLES =====")
    for s in samples[cls]:
        print(json.dumps(s, sort_keys=True, default=str))

failed_errors = Counter()
for r in db_rows:
    if str(r.get("state")) == "FAILED" and r.get("last_error"):
        failed_errors[str(r.get("last_error"))] += 1

print("TOP_FAILED_ERRORS=")
for err, n in failed_errors.most_common(10):
    print("ERROR_COUNT=", n, "ERROR=", err[:500])

report = {
    "version": "V65.77",
    "timestamp": STAMP,
    "before_counts": before_counts,
    "after_counts": after_counts,
    "completed_this_run": done,
    "completed_type_counts": dict(completed_types),
    "idle_at": idle_at,
    "queue_minus_db_delta_before": delta_before,
    "queue_minus_db_delta_after": delta_after,
    "remaining_classification_counts": dict(classes),
    "rollback_snapshot_dir": str(SNAP_DIR),
}
rp = REPORT_DIR / f"v65_77_post_starvation_fix_live_drain_{STAMP}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

print("REPORT=", rp)
print("ROLLBACK_AVAILABLE=", SNAP_DIR)
print("V65_77_PROFIT_ALIGNMENT_AFTER=FULL")
print("V65_77_POST_FIX_LIVE_DRAIN=PASS")
print("V65_77_COMPLETE")
PY
