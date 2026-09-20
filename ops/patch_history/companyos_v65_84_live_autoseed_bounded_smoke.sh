#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export COMPANYOS_PROFIT_AUTOSEED_ENABLED=1
export COMPANYOS_PROFIT_AUTOSEED_COOLDOWN_SECONDS=300

echo "===== COMPANYOS V65.84 LIVE AUTO-SEED BOUNDED SMOKE ====="

python - <<'PY'
from pathlib import Path
import json
import re
import shutil
import sqlite3
import tarfile
import time
from collections import Counter

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
QUEUE_DIR = RUNTIME / "task_queue"
DB = RUNTIME / "execution_kernel.sqlite3"
INTAKE_DIR = RUNTIME / "goal_intake"
ORCH_DIR = RUNTIME / "ceo_orchestrations"
REPORT_DIR = RUNTIME / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

STAMP = int(time.time())
SNAP_DIR = RUNTIME / "checkpoints" / f"v65_84_live_autoseed_before_{STAMP}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

profit_terms = re.compile(
    r"(primary economic directive|profit|profitability|expected[_ ]profit|risk[- ]adjusted|economic value|expected roi)",
    re.I | re.S,
)

def load_json_dir(path):
    out = {}
    unreadable = []
    if not path.exists():
        return out, unreadable
    for p in sorted(path.glob("*.json")):
        try:
            d = json.loads(p.read_text(errors="ignore"))
            out[p.stem] = d
        except Exception as exc:
            unreadable.append((str(p), type(exc).__name__, str(exc)))
    return out, unreadable

def load_queue():
    raw, bad = load_json_dir(QUEUE_DIR)
    by_id = {}
    for _, d in raw.items():
        by_id[str(d.get("task_id") or _)] = d
    return by_id, bad

def db_state():
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

queue_before, bad_q = load_queue()
intake_before, bad_i = load_json_dir(INTAKE_DIR)
orch_before, bad_o = load_json_dir(ORCH_DIR)
integrity_before, db_before = db_state()

qstates_before = Counter(str(x.get("state") or "UNKNOWN") for x in queue_before.values())
running_orch_before = [
    d for d in orch_before.values() if str(d.get("state")) == "RUNNING"
]
pending_intake_before = [
    d for d in intake_before.values()
    if str(d.get("state")) in ("PENDING", "CLAIMED")
]

print("QUEUE_COUNTS_BEFORE=", dict(sorted(qstates_before.items())))
print("RUNNING_ORCHESTRATIONS_BEFORE=", len(running_orch_before))
print("PENDING_OR_CLAIMED_INTAKES_BEFORE=", len(pending_intake_before))
print("DB_INTEGRITY_BEFORE=", integrity_before)
print("QUEUE_MINUS_DB_DELTA_BEFORE=", len(queue_before) - len(db_before))
print("UNREADABLE_BEFORE=", len(bad_q) + len(bad_i) + len(bad_o))

if bad_q or bad_i or bad_o:
    raise SystemExit("V65_84_ABORT=unreadable_runtime_json")
if integrity_before != "ok":
    raise SystemExit("V65_84_ABORT=db_integrity_before")
if len(queue_before) != len(db_before):
    raise SystemExit("V65_84_ABORT=projection_cardinality_before")
if qstates_before.get("QUEUED", 0) or qstates_before.get("CLAIMED", 0) or qstates_before.get("RUNNING", 0):
    raise SystemExit("V65_84_ABORT=active_task_work_before")
if running_orch_before:
    raise SystemExit("V65_84_ABORT=running_orchestration_before")
if pending_intake_before:
    raise SystemExit("V65_84_ABORT=pending_intake_before")

# Snapshot real runtime state before bounded live smoke.
db_copy = SNAP_DIR / "execution_kernel.sqlite3"
src = sqlite3.connect(str(DB))
dst = sqlite3.connect(str(db_copy))
try:
    src.backup(dst)
finally:
    dst.close()
    src.close()

for dirname in ("task_queue", "goal_intake", "ceo_orchestrations", "goal_lifecycle", "goal_outcomes"):
    p = RUNTIME / dirname
    if p.exists():
        a = SNAP_DIR / f"{dirname}_before.tar.gz"
        with tarfile.open(a, "w:gz") as tf:
            tf.add(p, arcname=dirname)

state_path = RUNTIME / "continuous_goal_runtime_state.json"
if state_path.exists():
    shutil.copy2(state_path, SNAP_DIR / "continuous_goal_runtime_state.json.before")

print("ROLLBACK_SNAPSHOT=", SNAP_DIR)
print("ROLLBACK_SNAPSHOT_STATUS=PASS")

# Capture IDs before so we can identify only work created by this smoke.
before_intake_ids = set(intake_before.keys())
before_orch_ids = set(orch_before.keys())
before_task_ids = set(queue_before.keys())

from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime

runtime = ContinuousGoalRuntime(interval_seconds=1, max_failures=3)
state = runtime.run(max_cycles=6)

print("RUNTIME_FINAL_STATE=", {
    "running": state.running,
    "ready": state.ready,
    "cycles": state.cycles,
    "goals_processed": state.goals_processed,
    "idle_cycles": state.idle_cycles,
    "execution_dispatched": state.execution_dispatched,
    "execution_failures": state.execution_failures,
    "scheduler_failures": state.scheduler_failures,
    "ceo_failures": state.ceo_failures,
    "auto_seeded_profit_goals": getattr(state, "auto_seeded_profit_goals", None),
    "last_reason": state.last_reason,
    "last_orchestration_id": state.last_orchestration_id,
})

queue_after, bad_q2 = load_queue()
intake_after, bad_i2 = load_json_dir(INTAKE_DIR)
orch_after, bad_o2 = load_json_dir(ORCH_DIR)
integrity_after, db_after = db_state()

new_intake_ids = sorted(set(intake_after) - before_intake_ids)
new_orch_ids = sorted(set(orch_after) - before_orch_ids)
new_task_ids = sorted(set(queue_after) - before_task_ids)

auto_intakes = []
for iid in new_intake_ids:
    d = intake_after[iid]
    md = d.get("metadata") or {}
    if md.get("auto_seeded") is True:
        auto_intakes.append(d)

print("NEW_INTAKE_IDS=", new_intake_ids)
print("NEW_ORCHESTRATION_IDS=", new_orch_ids)
print("NEW_TASK_IDS=", new_task_ids)
print("AUTO_SEEDED_INTAKES=", len(auto_intakes))

if len(auto_intakes) != 1:
    raise SystemExit(f"V65_84_FAIL=expected_one_autoseed_got:{len(auto_intakes)}")

seed = auto_intakes[0]
print("AUTO_SEEDED_INTAKE_STATE=", seed.get("state"))
print("AUTO_SEEDED_INTAKE_ORCHESTRATION=", seed.get("orchestration_id"))
print("AUTO_SEEDED_GOAL_PROFIT_ALIGNED=", bool(profit_terms.search(str(seed.get("goal") or ""))))

if seed.get("state") != "SUBMITTED":
    raise SystemExit("V65_84_FAIL=autoseed_not_submitted")
if not seed.get("orchestration_id"):
    raise SystemExit("V65_84_FAIL=autoseed_missing_orchestration")
if not profit_terms.search(str(seed.get("goal") or "")):
    raise SystemExit("V65_84_FAIL=autoseed_goal_not_profit_aligned")

oid = str(seed["orchestration_id"])
orch = None
for d in orch_after.values():
    if str(d.get("orchestration_id")) == oid:
        orch = d
        break

if orch is None:
    raise SystemExit("V65_84_FAIL=created_orchestration_missing")

print("AUTO_SEEDED_ORCHESTRATION_STATE=", orch.get("state"))
if str(orch.get("state")) != "COMPLETED":
    raise SystemExit(f"V65_84_FAIL=orchestration_not_completed:{orch.get('state')}")

created_tasks = [queue_after[tid] for tid in new_task_ids]
if not created_tasks:
    raise SystemExit("V65_84_FAIL=no_tasks_created")

task_states = Counter(str(t.get("state") or "UNKNOWN") for t in created_tasks)
task_types = Counter(str(t.get("task_type") or "UNKNOWN") for t in created_tasks)
misaligned = []
external_true = []

for t in created_tasks:
    payload_text = json.dumps(t.get("payload"), sort_keys=True, default=str)
    if not profit_terms.search(payload_text):
        misaligned.append(t.get("task_id"))

    result = t.get("result")
    if isinstance(result, dict):
        for k in (
            "external_research_performed",
            "external_deployment_performed",
            "external_action_performed",
            "transaction_performed",
        ):
            if bool(result.get(k)):
                external_true.append((t.get("task_id"), k))

print("NEW_TASK_STATE_COUNTS=", dict(sorted(task_states.items())))
print("NEW_TASK_TYPE_COUNTS=", dict(sorted(task_types.items())))
print("NEW_TASK_PROFIT_MISALIGNED=", misaligned)
print("NEW_TASK_EXTERNAL_TRUE_FLAGS=", external_true)

if task_states.get("COMPLETED", 0) != len(created_tasks):
    raise SystemExit("V65_84_FAIL=new_tasks_not_all_completed")
if misaligned:
    raise SystemExit("V65_84_FAIL=new_tasks_profit_misaligned")
if external_true:
    raise SystemExit("V65_84_FAIL=unexpected_external_action")

qstates_after = Counter(str(x.get("state") or "UNKNOWN") for x in queue_after.values())
running_orch_after = [
    d for d in orch_after.values() if str(d.get("state")) == "RUNNING"
]
pending_intake_after = [
    d for d in intake_after.values()
    if str(d.get("state")) in ("PENDING", "CLAIMED")
]

print("QUEUE_COUNTS_AFTER=", dict(sorted(qstates_after.items())))
print("RUNNING_ORCHESTRATIONS_AFTER=", len(running_orch_after))
print("PENDING_OR_CLAIMED_INTAKES_AFTER=", len(pending_intake_after))
print("DB_INTEGRITY_AFTER=", integrity_after)
print("QUEUE_MINUS_DB_DELTA_AFTER=", len(queue_after) - len(db_after))

if bad_q2 or bad_i2 or bad_o2:
    raise SystemExit("V65_84_FAIL=unreadable_runtime_json_after")
if integrity_after != "ok":
    raise SystemExit("V65_84_FAIL=db_integrity_after")
if len(queue_after) != len(db_after):
    raise SystemExit("V65_84_FAIL=projection_cardinality_after")
if qstates_after.get("QUEUED", 0) or qstates_after.get("CLAIMED", 0) or qstates_after.get("RUNNING", 0):
    raise SystemExit("V65_84_FAIL=active_task_work_after")
if running_orch_after:
    raise SystemExit("V65_84_FAIL=running_orchestration_after")
if pending_intake_after:
    raise SystemExit("V65_84_FAIL=pending_intake_after")
if state.execution_failures or state.scheduler_failures or state.ceo_failures:
    raise SystemExit("V65_84_FAIL=runtime_health_failure")
if int(getattr(state, "auto_seeded_profit_goals", 0) or 0) != 1:
    raise SystemExit("V65_84_FAIL=autoseed_counter_not_one")

report = {
    "version": "V65.84",
    "timestamp": STAMP,
    "rollback_snapshot_dir": str(SNAP_DIR),
    "new_intake_ids": new_intake_ids,
    "new_orchestration_ids": new_orch_ids,
    "new_task_ids": new_task_ids,
    "new_task_state_counts": dict(task_states),
    "new_task_type_counts": dict(task_types),
    "runtime": {
        "cycles": state.cycles,
        "goals_processed": state.goals_processed,
        "execution_dispatched": state.execution_dispatched,
        "execution_failures": state.execution_failures,
        "scheduler_failures": state.scheduler_failures,
        "ceo_failures": state.ceo_failures,
        "auto_seeded_profit_goals": getattr(state, "auto_seeded_profit_goals", 0),
        "last_reason": state.last_reason,
    },
    "queue_minus_db_delta_after": len(queue_after) - len(db_after),
    "db_integrity_after": integrity_after,
}
rp = REPORT_DIR / f"v65_84_live_autoseed_bounded_smoke_{STAMP}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

print("REPORT=", rp)
print("ROLLBACK_AVAILABLE=", SNAP_DIR)
print("V65_84_REAL_IDLE_AUTOSEED=PASS")
print("V65_84_PROFIT_DIRECTIVE=PASS")
print("V65_84_AUTONOMOUS_EXECUTION=PASS")
print("V65_84_ANTI_FLOOD=PASS")
print("V65_84_RUNTIME_HEALTH=PASS")
print("V65_84_PROJECTION_ALIGNMENT=PASS")
print("V65_84_COMPLETE")
PY
