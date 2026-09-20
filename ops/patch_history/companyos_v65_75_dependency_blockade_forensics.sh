#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.75 DEPENDENCY BLOCKADE FORENSICS ====="
echo "SOURCE_WRITES=0"
echo "QUEUE_WRITES=0"
echo "DB_WRITES=0"

python - <<'PY'
from pathlib import Path
import json
import sqlite3
from collections import Counter, defaultdict

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
QUEUE_DIR = RUNTIME / "task_queue"
DB = RUNTIME / "execution_kernel.sqlite3"

# ----- Read every JSON task record -----
tasks = []
unreadable = []

for p in sorted(QUEUE_DIR.glob("*.json")):
    try:
        d = json.loads(p.read_text(errors="ignore"))
        d["_path"] = str(p)
        tasks.append(d)
    except Exception as exc:
        unreadable.append((str(p), type(exc).__name__, str(exc)))

print("QUEUE_JSON_RECORDS=", len(tasks))
print("UNREADABLE_JSON_RECORDS=", len(unreadable))

if unreadable:
    for x in unreadable[:10]:
        print("UNREADABLE_SAMPLE=", x)

state_counts = Counter(str(t.get("state") or "UNKNOWN") for t in tasks)
type_counts = Counter(str(t.get("task_type") or "UNKNOWN") for t in tasks)
print("STATE_COUNTS=", dict(sorted(state_counts.items())))
print("TYPE_COUNTS=", dict(sorted(type_counts.items())))

queued = [t for t in tasks if str(t.get("state")) == "QUEUED"]
print("QUEUED_TOTAL=", len(queued))
print("QUEUED_TYPES=", dict(sorted(Counter(str(t.get("task_type") or "UNKNOWN") for t in queued).items())))

# ----- Build JSON indexes -----
by_goal_stage = defaultdict(list)

for t in tasks:
    payload = t.get("payload")
    if not isinstance(payload, dict):
        continue
    gid = payload.get("goal_id")
    stage = payload.get("stage")
    if gid is not None and stage is not None:
        by_goal_stage[(str(gid), str(stage))].append(t)

# ----- Read SQLite durable projection -----
db_rows = []
if DB.exists():
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        db_rows = [dict(r) for r in con.execute(
            "SELECT task_id, idempotency_key, task_type, state, goal_id, stage, depends_on_stage, attempts, max_attempts, last_error "
            "FROM tasks"
        ).fetchall()]
    finally:
        con.close()
else:
    integrity = "missing"

print("DB_INTEGRITY=", integrity)
print("DB_TASK_ROWS=", len(db_rows))

db_by_goal_stage = defaultdict(list)
db_by_id = {}

for r in db_rows:
    db_by_id[str(r.get("task_id"))] = r
    gid = r.get("goal_id")
    stage = r.get("stage")
    if gid is not None and stage is not None:
        db_by_goal_stage[(str(gid), str(stage))].append(r)

# ----- Classify each queued task -----
classes = Counter()
stage_pairs = Counter()
samples = defaultdict(list)

for t in queued:
    task_id = str(t.get("task_id"))
    task_type = str(t.get("task_type") or "UNKNOWN")
    payload = t.get("payload")
    if not isinstance(payload, dict):
        cls = "queued_payload_not_mapping"
        classes[cls] += 1
        if len(samples[cls]) < 10:
            samples[cls].append({"task_id": task_id, "task_type": task_type})
        continue

    gid = payload.get("goal_id")
    stage = payload.get("stage")
    dep = payload.get("depends_on_stage")

    if not dep:
        cls = "ready_no_dependency"
        classes[cls] += 1
        if len(samples[cls]) < 10:
            samples[cls].append({
                "task_id": task_id, "task_type": task_type,
                "goal_id": gid, "stage": stage
            })
        continue

    stage_pairs[(str(stage), str(dep))] += 1

    if gid is None:
        cls = "blocked_missing_goal_id"
        classes[cls] += 1
        if len(samples[cls]) < 10:
            samples[cls].append({
                "task_id": task_id, "task_type": task_type,
                "stage": stage, "depends_on_stage": dep
            })
        continue

    key = (str(gid), str(dep))
    jdeps = by_goal_stage.get(key, [])
    ddeps = db_by_goal_stage.get(key, [])

    jstates = Counter(str(x.get("state") or "UNKNOWN") for x in jdeps)
    dstates = Counter(str(x.get("state") or "UNKNOWN") for x in ddeps)

    if jstates.get("COMPLETED", 0) > 0:
        cls = "ready_prerequisite_completed_json"
    elif dstates.get("COMPLETED", 0) > 0:
        cls = "projection_gap_completed_in_db_only"
    elif jstates.get("FAILED", 0) > 0 or dstates.get("FAILED", 0) > 0:
        cls = "blocked_by_failed_prerequisite"
    elif jstates.get("QUEUED", 0) > 0 or dstates.get("QUEUED", 0) > 0:
        cls = "waiting_on_queued_prerequisite"
    elif jstates.get("RUNNING", 0) > 0 or dstates.get("RUNNING", 0) > 0:
        cls = "waiting_on_running_prerequisite"
    elif not jdeps and not ddeps:
        cls = "orphan_missing_prerequisite"
    else:
        cls = "blocked_other_prerequisite_state"

    classes[cls] += 1

    if len(samples[cls]) < 12:
        samples[cls].append({
            "task_id": task_id,
            "task_type": task_type,
            "goal_id": gid,
            "stage": stage,
            "depends_on_stage": dep,
            "json_prereq_states": dict(sorted(jstates.items())),
            "db_prereq_states": dict(sorted(dstates.items())),
        })

print("CLASSIFICATION_COUNTS=", dict(sorted(classes.items())))
print("STAGE_DEPENDENCY_PAIRS=", {f"{a}<-{b}": n for (a,b), n in sorted(stage_pairs.items())})

for cls in sorted(samples):
    print(f"\n===== {cls} SAMPLES =====")
    for s in samples[cls]:
        print(json.dumps(s, sort_keys=True))

# ----- Check if the runtime idle condition is globally true -----
globally_ready = (
    classes.get("ready_no_dependency", 0)
    + classes.get("ready_prerequisite_completed_json", 0)
    + classes.get("projection_gap_completed_in_db_only", 0)
)

print("\nGLOBALLY_READY_COUNT=", globally_ready)
print("FAILED_PREREQ_BLOCKED_COUNT=", classes.get("blocked_by_failed_prerequisite", 0))
print("ORPHAN_MISSING_PREREQ_COUNT=", classes.get("orphan_missing_prerequisite", 0))
print("WAITING_ON_QUEUED_PREREQ_COUNT=", classes.get("waiting_on_queued_prerequisite", 0))
print("PROJECTION_GAP_COUNT=", classes.get("projection_gap_completed_in_db_only", 0))

if globally_ready == 0:
    print("IDLE_DIAGNOSIS=TRUE_DEPENDENCY_BLOCKADE")
elif classes.get("projection_gap_completed_in_db_only", 0) > 0:
    print("IDLE_DIAGNOSIS=JSON_DB_PROJECTION_GAP_POSSIBLE")
else:
    print("IDLE_DIAGNOSIS=READY_TASKS_EXIST_BUT_DISPATCHER_DID_NOT_SELECT")

# ----- Durable failed-prerequisite error summary -----
failed_errors = Counter()
for r in db_rows:
    if str(r.get("state")) == "FAILED":
        err = str(r.get("last_error") or "")
        if err:
            failed_errors[err] += 1

print("TOP_FAILED_PREREQUISITE_ERRORS=")
for err, n in failed_errors.most_common(12):
    print("ERROR_COUNT=", n, "ERROR=", err[:500])

print("V65_75_DEPENDENCY_BLOCKADE_FORENSICS=COMPLETE")
PY
