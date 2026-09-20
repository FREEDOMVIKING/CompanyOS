#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.81 PROFIT GOAL REGENERATION SMOKE ====="

python - <<'PY'
from pathlib import Path
import json
import re
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
SNAP_DIR = RUNTIME / "checkpoints" / f"v65_81_profit_regen_before_{STAMP}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

print("REPO=", ROOT)
print("RUNTIME=", RUNTIME)
print("SNAPSHOT_DIR=", SNAP_DIR)

profit_terms = re.compile(
    r"(primary economic directive|maximi[sz]e.{0,80}profit|profitability|expected[_ ]profit|net profit|risk[- ]adjusted|enterprise value|expected roi|return on investment)",
    re.I | re.S,
)

def load_queue():
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

def db_rows():
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

queue_before, unreadable = load_queue()
integrity_before, durable_before = db_rows()

json_states_before = Counter(str(x.get("state") or "UNKNOWN") for x in queue_before.values())
db_states_before = Counter(str(x.get("state") or "UNKNOWN") for x in durable_before)

print("QUEUE_STATE_COUNTS_BEFORE=", dict(sorted(json_states_before.items())))
print("DB_STATE_COUNTS_BEFORE=", dict(sorted(db_states_before.items())))
print("QUEUE_MINUS_DB_DELTA_BEFORE=", len(queue_before) - len(durable_before))
print("DB_INTEGRITY_BEFORE=", integrity_before)
print("UNREADABLE_QUEUE_FILES_BEFORE=", len(unreadable))

if unreadable:
    raise SystemExit("V65_81_ABORT=unreadable_queue_files")
if integrity_before != "ok":
    raise SystemExit("V65_81_ABORT=db_integrity_failed")
if len(queue_before) != len(durable_before):
    raise SystemExit("V65_81_ABORT=projection_cardinality_mismatch")
if json_states_before.get("QUEUED", 0) != 0:
    raise SystemExit("V65_81_ABORT=queue_not_empty_starting_state")

# ----- Inspect existing intake/orchestrations before creating fresh work -----
from companyos.runtime.autonomous_goal_intake import AutonomousGoalIntake
from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator

intake = AutonomousGoalIntake()
ceo = AutonomousCEOOrchestrator()

intake_records = intake.all_records()
pending = [r for r in intake_records if r.state in ("PENDING", "CLAIMED")]
running_orchestrations = []

for p in sorted(ceo.root.glob("*.json")):
    try:
        rec = ceo.load(p.stem)
    except Exception:
        continue
    if rec.state == "RUNNING":
        running_orchestrations.append(rec)

print("PENDING_OR_CLAIMED_INTAKES_BEFORE=", len(pending))
print("RUNNING_ORCHESTRATIONS_BEFORE=", len(running_orchestrations))

if pending:
    for r in pending[:10]:
        print("EXISTING_INTAKE=", {
            "intake_id": r.intake_id,
            "state": r.state,
            "priority": r.priority,
            "goal_preview": r.goal[:300],
        })
    raise SystemExit("V65_81_ABORT=existing_pending_intake_requires_processing_first")

if running_orchestrations:
    for r in running_orchestrations[:10]:
        print("EXISTING_RUNNING_ORCHESTRATION=", {
            "orchestration_id": r.orchestration_id,
            "state": r.state,
            "root_goal_preview": r.root_goal[:300],
            "total_cycles": r.total_cycles,
        })
    raise SystemExit("V65_81_ABORT=existing_running_orchestration_requires_processing_first")

# ----- Rollback snapshot before creating fresh work -----
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

goal_intake_root = RUNTIME / "goal_intake"
if goal_intake_root.exists():
    intake_archive = SNAP_DIR / "goal_intake_before.tar.gz"
    with tarfile.open(intake_archive, "w:gz") as tf:
        tf.add(goal_intake_root, arcname="goal_intake")
else:
    intake_archive = None

orch_root = RUNTIME / "ceo_orchestrations"
if orch_root.exists():
    orch_archive = SNAP_DIR / "ceo_orchestrations_before.tar.gz"
    with tarfile.open(orch_archive, "w:gz") as tf:
        tf.add(orch_root, arcname="ceo_orchestrations")
else:
    orch_archive = None

print("ROLLBACK_SNAPSHOT_DB=", db_copy)
print("ROLLBACK_SNAPSHOT_QUEUE=", archive)
print("ROLLBACK_SNAPSHOT_INTAKE=", intake_archive)
print("ROLLBACK_SNAPSHOT_ORCHESTRATIONS=", orch_archive)
print("ROLLBACK_SNAPSHOT=PASS")

# ----- Seed exactly one fresh profit-first CEO goal -----
from companyos.strategy.profit_first_venture_engine import discovery_directive

goal = discovery_directive()

if not profit_terms.search(goal):
    raise SystemExit("V65_81_ABORT=profit_directive_not_detected_in_seed_goal")

seed_id = f"v65-81-profit-regeneration-{STAMP}"
record = intake.submit(
    goal=goal,
    priority=1,
    metadata={
        "source": "v65.81_profit_goal_regeneration_smoke",
        "profit_first": True,
        "internal_only": True,
        "created_at_unix": time.time(),
    },
    intake_id=seed_id,
    max_attempts=3,
)

print("SEEDED_INTAKE_ID=", record.intake_id)
print("SEEDED_INTAKE_STATE=", record.state)
print("SEEDED_GOAL_PROFIT_ALIGNED=", bool(profit_terms.search(record.goal)))

# ----- Process through the real scheduler path -----
from companyos.runtime.autonomous_goal_scheduler import AutonomousGoalScheduler

scheduler = AutonomousGoalScheduler(intake=intake, ceo=ceo)
scheduled = scheduler.process_next()

print("SCHEDULER_RESULT=", scheduled)

if not scheduled.processed:
    raise SystemExit("V65_81_FAIL=scheduler_did_not_process_seed")
if not scheduled.orchestration_id:
    raise SystemExit("V65_81_FAIL=scheduler_did_not_create_orchestration")

orch_id = scheduled.orchestration_id
orch = ceo.load(orch_id)

print("CREATED_ORCHESTRATION_ID=", orch_id)
print("CREATED_ORCHESTRATION_STATE=", orch.state)
print("CREATED_ROOT_GOAL_PROFIT_ALIGNED=", bool(profit_terms.search(orch.root_goal)))

if not profit_terms.search(orch.root_goal):
    raise SystemExit("V65_81_FAIL=orchestration_root_goal_not_profit_aligned")

# ----- Run bounded real internal runtime cycles -----
from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime, ContinuousGoalRuntimeState

runtime = ContinuousGoalRuntime(interval_seconds=1, max_failures=3)
state = ContinuousGoalRuntimeState(
    running=True,
    ready=True,
    cycles=0,
    goals_processed=0,
    idle_cycles=0,
    consecutive_failures=0,
    last_reason="v65_81_smoke_started",
    last_orchestration_id=orch_id,
    updated_at_unix=time.time(),
    execution_dispatched=0,
    execution_failures=0,
    scheduler_failures=0,
    ceo_failures=0,
)

for i in range(1, 13):
    state = runtime.cycle(state)
    orch = ceo.load(orch_id)
    q_now, _ = load_queue()
    counts = Counter(str(x.get("state") or "UNKNOWN") for x in q_now.values())

    print("RUNTIME_CYCLE=", {
        "cycle": i,
        "runtime_ready": state.ready,
        "runtime_reason": state.last_reason,
        "execution_dispatched_total": state.execution_dispatched,
        "execution_failures": state.execution_failures,
        "scheduler_failures": state.scheduler_failures,
        "ceo_failures": state.ceo_failures,
        "orchestration_state": orch.state,
        "queue_states": dict(sorted(counts.items())),
    })

    if state.execution_failures or state.scheduler_failures:
        raise SystemExit("V65_81_FAIL=runtime_execution_or_scheduler_failure")

    if orch.state in ("COMPLETED", "FAILED", "HALTED") and counts.get("QUEUED", 0) == 0:
        break

# ----- Verify every task created by the new orchestration -----
queue_after, unreadable_after = load_queue()
integrity_after, durable_after = db_rows()

new_goal_tasks = []
for d in queue_after.values():
    payload = d.get("payload")
    if not isinstance(payload, dict):
        continue
    gid = str(payload.get("goal_id") or "")
    if gid.startswith(orch_id + ":goal:"):
        new_goal_tasks.append(d)

print("NEW_GOAL_TASK_COUNT=", len(new_goal_tasks))

if not new_goal_tasks:
    raise SystemExit("V65_81_FAIL=no_tasks_created_for_new_profit_goal")

misaligned = []
external_true = []

for d in new_goal_tasks:
    payload_txt = json.dumps(d.get("payload"), sort_keys=True, default=str)
    if not profit_terms.search(payload_txt):
        misaligned.append(d.get("task_id"))

    result = d.get("result")
    if isinstance(result, dict):
        for key in (
            "external_research_performed",
            "external_deployment_performed",
            "external_action_performed",
            "transaction_performed",
        ):
            if bool(result.get(key)):
                external_true.append((d.get("task_id"), key))

print("NEW_GOAL_PROFIT_MISALIGNED_TASKS=", misaligned)
print("NEW_GOAL_EXTERNAL_TRUE_FLAGS=", external_true)

if misaligned:
    raise SystemExit("V65_81_FAIL=new_goal_task_profit_alignment_failure")
if external_true:
    raise SystemExit("V65_81_FAIL=unexpected_external_action")

json_states_after = Counter(str(x.get("state") or "UNKNOWN") for x in queue_after.values())
db_states_after = Counter(str(x.get("state") or "UNKNOWN") for x in durable_after)

print("QUEUE_STATE_COUNTS_AFTER=", dict(sorted(json_states_after.items())))
print("DB_STATE_COUNTS_AFTER=", dict(sorted(db_states_after.items())))
print("QUEUE_MINUS_DB_DELTA_AFTER=", len(queue_after) - len(durable_after))
print("DB_INTEGRITY_AFTER=", integrity_after)
print("UNREADABLE_QUEUE_FILES_AFTER=", len(unreadable_after))

orch = ceo.load(orch_id)
final_intake = intake.load(seed_id)

print("FINAL_INTAKE_STATE=", final_intake.state)
print("FINAL_ORCHESTRATION_STATE=", orch.state)
print("RUNTIME_EXECUTION_FAILURES=", state.execution_failures)
print("RUNTIME_SCHEDULER_FAILURES=", state.scheduler_failures)
print("RUNTIME_CEO_FAILURES=", state.ceo_failures)

if unreadable_after:
    raise SystemExit("V65_81_FAIL=unreadable_queue_after")
if integrity_after != "ok":
    raise SystemExit("V65_81_FAIL=db_integrity_after")
if len(queue_after) != len(durable_after):
    raise SystemExit("V65_81_FAIL=projection_cardinality_after")
if final_intake.state != "SUBMITTED":
    raise SystemExit("V65_81_FAIL=intake_not_submitted")
if orch.state not in ("COMPLETED", "RUNNING"):
    raise SystemExit(f"V65_81_FAIL=unexpected_orchestration_state:{orch.state}")
if state.execution_failures or state.scheduler_failures or state.ceo_failures:
    raise SystemExit("V65_81_FAIL=runtime_health_failure")

report = {
    "version": "V65.81",
    "timestamp": STAMP,
    "seed_intake_id": seed_id,
    "orchestration_id": orch_id,
    "final_intake_state": final_intake.state,
    "final_orchestration_state": orch.state,
    "new_goal_task_count": len(new_goal_tasks),
    "queue_state_counts_after": dict(json_states_after),
    "db_state_counts_after": dict(db_states_after),
    "queue_minus_db_delta_after": len(queue_after) - len(durable_after),
    "runtime_state": {
        "cycles": state.cycles,
        "execution_dispatched": state.execution_dispatched,
        "execution_failures": state.execution_failures,
        "scheduler_failures": state.scheduler_failures,
        "ceo_failures": state.ceo_failures,
        "last_reason": state.last_reason,
    },
    "rollback_snapshot_dir": str(SNAP_DIR),
}
rp = REPORT_DIR / f"v65_81_profit_goal_regeneration_smoke_{STAMP}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

print("REPORT=", rp)
print("ROLLBACK_AVAILABLE=", SNAP_DIR)
print("V65_81_FRESH_PROFIT_GOAL_CREATED=PASS")
print("V65_81_SCHEDULER_PATH=PASS")
print("V65_81_NEW_GOAL_PROFIT_ALIGNMENT=PASS")
print("V65_81_INTERNAL_ONLY_EXECUTION=PASS")
print("V65_81_RUNTIME_HEALTH=PASS")
print("V65_81_COMPLETE")
PY
