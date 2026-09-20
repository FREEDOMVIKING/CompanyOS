#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.80 RECONCILED QUEUE FINAL DRAIN ====="

python - <<'PY'
from pathlib import Path
import ast
import json
import re
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

STOP_FILE = RUNTIME / "STOP_COMPANYOS"
STAMP = int(time.time())
SNAP_DIR = RUNTIME / "checkpoints" / f"v65_80_runtime_before_{STAMP}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

MAX_DISPATCHES = 80

print("REPO=", ROOT)
print("RUNTIME=", RUNTIME)
print("MAX_DISPATCHES=", MAX_DISPATCHES)
print("SNAPSHOT_DIR=", SNAP_DIR)

# ---------- Verify V65.76 starvation fix ----------
dep_path = ROOT / "companyos/runtime/dependency_aware_dispatcher.py"
dep_text = dep_path.read_text(errors="ignore")
fix_markers = [
    "V65.76 scan-window starvation fix",
    "starvation fallback",
    "self.queue._iter_task_files()",
]
missing = [x for x in fix_markers if x not in dep_text]
print("V65_76_MARKERS_MISSING=", missing)
if missing:
    raise SystemExit("V65_80_ABORT=v65_76_fix_not_active")
print("V65_76_FIX_ACTIVE=PASS")

# ---------- Verify corrected dispatcher result flow ----------
dispatcher_path = ROOT / "companyos/runtime/autonomous_task_dispatcher.py"
dtext = dispatcher_path.read_text(errors="ignore")
tree = ast.parse(dtext)

has_result_assignment = False
has_execute_call = False
has_complete_with_result = False

for node in ast.walk(tree):
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = set()
        for target in targets:
            for sub in ast.walk(target):
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
    raise SystemExit("V65_80_ABORT=current_dispatcher_result_flow_not_verified")
print("CURRENT_DISPATCHER_RESULT_FLOW=VERIFIED")

# ---------- Profit alignment gate ----------
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
        break

if not explicit_directive:
    raise SystemExit("V65_80_ABORT=hardcoded_profit_directive_not_found")
print("HARD_CODED_PROFIT_DIRECTIVE=CONFIRMED")

# ---------- Internal-only default handlers ----------
registry_path = ROOT / "companyos/runtime/default_specialist_registry.py"
registry_text = registry_path.read_text(errors="ignore")
rtree = ast.parse(registry_text)
imports = set()
for n in ast.walk(rtree):
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
    raise SystemExit("V65_80_ABORT=external_specialist_import_detected")

compact = registry_text.replace(" ", "")
if '"external_research_performed":False' not in compact:
    raise SystemExit("V65_80_ABORT=research_internal_only_marker_missing")
if '"external_deployment_performed":False' not in compact:
    raise SystemExit("V65_80_ABORT=build_internal_only_marker_missing")
print("INTERNAL_ONLY_EXECUTION_GATE=PASS")

def load_json_tasks():
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

def read_db_rows():
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        rows = [dict(r) for r in con.execute(
            "SELECT task_id,idempotency_key,task_type,state,goal_id,stage,depends_on_stage,"
            "attempts,max_attempts,last_error FROM tasks"
        ).fetchall()]
    finally:
        con.close()
    return integrity, rows

# ---------- Projection alignment gate ----------
json_before, unreadable_before = load_json_tasks()
integrity_before, db_before = read_db_rows()

json_states_before = Counter(str(d.get("state") or "UNKNOWN") for d in json_before.values())
db_states_before = Counter(str(d.get("state") or "UNKNOWN") for d in db_before)

print("JSON_TASKS_BEFORE=", len(json_before))
print("DB_TASKS_BEFORE=", len(db_before))
print("QUEUE_MINUS_DB_DELTA_BEFORE=", len(json_before) - len(db_before))
print("JSON_STATE_COUNTS_BEFORE=", dict(sorted(json_states_before.items())))
print("DB_STATE_COUNTS_BEFORE=", dict(sorted(db_states_before.items())))
print("DB_INTEGRITY_BEFORE=", integrity_before)
print("UNREADABLE_JSON_BEFORE=", len(unreadable_before))

if unreadable_before:
    raise SystemExit("V65_80_ABORT=unreadable_json_before")
if integrity_before != "ok":
    raise SystemExit("V65_80_ABORT=db_integrity_failed")
if len(json_before) != len(db_before):
    raise SystemExit("V65_80_ABORT=projection_cardinality_not_aligned")

db_by_id_before = {str(r["task_id"]): r for r in db_before}
state_mismatches = []
for tid, jt in json_before.items():
    dr = db_by_id_before.get(tid)
    if not dr or str(jt.get("state")) != str(dr.get("state")):
        state_mismatches.append(tid)

print("STATE_MISMATCHES_BEFORE=", len(state_mismatches))
if state_mismatches:
    raise SystemExit("V65_80_ABORT=projection_state_mismatch_before")

queued_before = [d for d in json_before.values() if str(d.get("state")) == "QUEUED"]
profit_missing = []
for d in queued_before:
    payload = d.get("payload")
    txt = json.dumps(payload, sort_keys=True, default=str) if isinstance(payload, dict) else ""
    if not profit_terms.search(txt):
        profit_missing.append(d.get("task_id"))

print("QUEUED_BEFORE=", len(queued_before))
print("QUEUED_PROFIT_MISSING_BEFORE=", profit_missing[:20])
if profit_missing:
    raise SystemExit("V65_80_ABORT=queue_profit_alignment_not_full")

# ---------- Rollback snapshot ----------
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
    raise SystemExit("V65_80_ABORT=stop_file_present")

# ---------- Live bounded drain ----------
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

q = AutonomousTaskQueue()
loop = AutonomousGoalExecutionLoop(q)

handlers = sorted(loop.dispatcher.dispatcher.handlers.keys())
print("REGISTERED_LIVE_HANDLERS=", handlers)
if handlers != ["build", "planning", "research"]:
    raise SystemExit("V65_80_ABORT=unexpected_live_handler_set")

completed_ids = []
completed_types = Counter()
idle_at = None
stopped_at = None
start = time.time()

for idx in range(1, MAX_DISPATCHES + 1):
    if STOP_FILE.exists():
        stopped_at = idx
        print("STOP_FILE_DETECTED_AT=", idx)
        break

    one = loop.run_bounded_batch(max_dispatches=1)
    if len(one) != 1:
        raise SystemExit(f"V65_80_FAIL=result_count_at_{idx}:{len(one)}")

    r = one[0]

    if not r.dispatched:
        if r.reason != "no_dependency_ready_task":
            raise SystemExit(f"V65_80_FAIL=unexpected_idle_reason:{r.reason}")
        idle_at = idx
        print("IDLE_AT=", idx)
        break

    if not r.task_id:
        raise SystemExit(f"V65_80_FAIL=missing_task_id_at_{idx}")

    task = q.load(r.task_id)

    payload_text = json.dumps(task.payload, sort_keys=True, default=str)
    if not profit_terms.search(payload_text):
        raise SystemExit(f"V65_80_FAIL=task_profit_objective_missing:{r.task_id}")

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
        raise SystemExit(f"V65_80_FAIL=unexpected_external_action_flag:{r.task_id}")

    if r.reason != "completed":
        raise SystemExit(f"V65_80_FAIL=noncompleted_dispatch:{r.task_id}:{r.reason}")

    completed_ids.append(r.task_id)
    completed_types[task.task_type] += 1

    print(
        "PROGRESS=",
        {
            "dispatch_index": idx,
            "task_id": r.task_id,
            "task_type": task.task_type,
            "completed_this_run": len(completed_ids),
            "type_counts": dict(sorted(completed_types.items())),
            "elapsed_seconds": round(time.time() - start, 2),
        },
    )

print("COMPLETED_THIS_RUN=", len(completed_ids))
print("COMPLETED_TYPE_COUNTS=", dict(sorted(completed_types.items())))
print("IDLE_AT=", idle_at)
print("STOPPED_AT=", stopped_at)

# ---------- Post-run projection/integrity ----------
json_after, unreadable_after = load_json_tasks()
integrity_after, db_after = read_db_rows()

json_states_after = Counter(str(d.get("state") or "UNKNOWN") for d in json_after.values())
db_states_after = Counter(str(d.get("state") or "UNKNOWN") for d in db_after)

print("JSON_TASKS_AFTER=", len(json_after))
print("DB_TASKS_AFTER=", len(db_after))
print("QUEUE_MINUS_DB_DELTA_AFTER=", len(json_after) - len(db_after))
print("JSON_STATE_COUNTS_AFTER=", dict(sorted(json_states_after.items())))
print("DB_STATE_COUNTS_AFTER=", dict(sorted(db_states_after.items())))
print("DB_INTEGRITY_AFTER=", integrity_after)
print("UNREADABLE_JSON_AFTER=", len(unreadable_after))

if unreadable_after:
    raise SystemExit("V65_80_FAIL=unreadable_json_after")
if integrity_after != "ok":
    raise SystemExit("V65_80_FAIL=db_integrity_after")
if len(json_after) != len(db_after):
    raise SystemExit("V65_80_FAIL=projection_cardinality_changed")

db_by_id_after = {str(r["task_id"]): r for r in db_after}
state_mismatches_after = []
for tid, jt in json_after.items():
    dr = db_by_id_after.get(tid)
    if not dr or str(jt.get("state")) != str(dr.get("state")):
        state_mismatches_after.append({
            "task_id": tid,
            "json_state": jt.get("state"),
            "db_state": dr.get("state") if dr else None,
        })

print("STATE_MISMATCHES_AFTER=", len(state_mismatches_after))
if state_mismatches_after:
    for x in state_mismatches_after[:20]:
        print("STATE_MISMATCH_AFTER=", x)
    raise SystemExit("V65_80_FAIL=projection_state_mismatch_after")

# ---------- Remaining queue classification ----------
by_goal_stage_json = defaultdict(list)
for d in json_after.values():
    payload = d.get("payload")
    if isinstance(payload, dict):
        gid = payload.get("goal_id")
        stage = payload.get("stage")
        if gid is not None and stage is not None:
            by_goal_stage_json[(str(gid), str(stage))].append(d)

by_goal_stage_db = defaultdict(list)
for r in db_after:
    gid = r.get("goal_id")
    stage = r.get("stage")
    if gid is not None and stage is not None:
        by_goal_stage_db[(str(gid), str(stage))].append(r)

classes = Counter()
samples = defaultdict(list)
queued_profit_missing_after = []

for d in json_after.values():
    if str(d.get("state")) != "QUEUED":
        continue

    payload = d.get("payload")
    txt = json.dumps(payload, sort_keys=True, default=str) if isinstance(payload, dict) else ""
    if not profit_terms.search(txt):
        queued_profit_missing_after.append(d.get("task_id"))

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
            "task_id": d.get("task_id"),
            "task_type": d.get("task_type"),
            "payload": d.get("payload"),
        })

print("REMAINING_QUEUED=", json_states_after.get("QUEUED", 0))
print("REMAINING_CLASSIFICATION_COUNTS=", dict(sorted(classes.items())))
print("QUEUED_PROFIT_MISSING_AFTER=", queued_profit_missing_after)

for cls in sorted(samples):
    print(f"===== {cls} SAMPLES =====")
    for s in samples[cls]:
        print(json.dumps(s, sort_keys=True, default=str))

failed_errors = Counter()
for r in db_after:
    if str(r.get("state")) == "FAILED" and r.get("last_error"):
        failed_errors[str(r.get("last_error"))] += 1

print("TOP_FAILED_ERRORS_AFTER=")
for err, n in failed_errors.most_common(10):
    print("ERROR_COUNT=", n, "ERROR=", err[:500])

if queued_profit_missing_after:
    raise SystemExit("V65_80_FAIL=remaining_queue_profit_alignment_not_full")

report = {
    "version": "V65.80",
    "timestamp": STAMP,
    "completed_this_run": len(completed_ids),
    "completed_type_counts": dict(completed_types),
    "idle_at": idle_at,
    "stopped_at": stopped_at,
    "json_state_counts_after": dict(json_states_after),
    "db_state_counts_after": dict(db_states_after),
    "remaining_classification_counts": dict(classes),
    "rollback_snapshot_dir": str(SNAP_DIR),
}
rp = REPORT_DIR / f"v65_80_reconciled_queue_final_drain_{STAMP}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

print("REPORT=", rp)
print("ROLLBACK_AVAILABLE=", SNAP_DIR)
print("V65_80_PROJECTION_ALIGNMENT=PASS")
print("V65_80_PROFIT_ALIGNMENT_AFTER=FULL")
print("V65_80_FINAL_DRAIN=PASS")
print("V65_80_COMPLETE")
PY
