#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.68 CONTROLLED RUNTIME SMOKE VALIDATION ====="

python - <<'PY'
from pathlib import Path
import ast, json, os, sqlite3, subprocess, sys, tempfile
from collections import Counter

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
QUEUE = RUNTIME / "task_queue"
DB = RUNTIME / "execution_kernel.sqlite3"
DISPATCHER = ROOT / "companyos/runtime/autonomous_task_dispatcher.py"
REGISTRY = ROOT / "companyos/runtime/default_specialist_registry.py"

print("REPO=", ROOT)
print("RUNTIME=", RUNTIME)

dispatcher_text = DISPATCHER.read_text(errors="ignore")
required_dispatch_markers = [
    "V35_1_FENCED_HANDLER_CALL",
    "V27_9_4A_LIVE_HANDLER_TIMEOUT",
    "run_bounded(lambda: handler(task))",
    "_v35_guard.execute",
]
missing = [m for m in required_dispatch_markers if m not in dispatcher_text]
print("DISPATCH_MARKERS_MISSING=", missing)
if missing:
    raise SystemExit("V65_68_ABORT=known_good_dispatcher_contract_missing")
print("DISPATCH_CONTRACT=PASS")

registry_text = REGISTRY.read_text(errors="ignore")
tree = ast.parse(registry_text)
imports = set()
for n in ast.walk(tree):
    if isinstance(n, ast.Import):
        imports.update(a.name.split(".")[0] for a in n.names)
    elif isinstance(n, ast.ImportFrom) and n.module:
        imports.add(n.module.split(".")[0])

blocked_imports = {
    "requests", "httpx", "urllib", "socket", "subprocess",
    "web3", "solana", "solders", "paramiko", "ftplib", "smtplib"
}
present_blocked = sorted(blocked_imports.intersection(imports))
print("SPECIALIST_IMPORTS=", sorted(imports))
print("BLOCKED_EXTERNAL_IMPORTS=", present_blocked)
if present_blocked:
    raise SystemExit("V65_68_ABORT=default_specialist_external_import_detected")

compact_registry = registry_text.replace(" ", "")
if '"external_research_performed":False' not in compact_registry:
    raise SystemExit("V65_68_ABORT=research_internal_only_marker_missing")
if '"external_deployment_performed":False' not in compact_registry:
    raise SystemExit("V65_68_ABORT=build_internal_only_marker_missing")
print("DEFAULT_SPECIALISTS_INTERNAL_ONLY=PASS")

def production_counts():
    counts = Counter()
    total = 0
    if QUEUE.exists():
        for p in QUEUE.glob("*.json"):
            try:
                rec = json.loads(p.read_text(errors="ignore"))
            except Exception:
                counts["UNREADABLE"] += 1
                continue
            total += 1
            counts[str(rec.get("state") or "UNKNOWN")] += 1
    return total, dict(sorted(counts.items()))

prod_total_before, prod_counts_before = production_counts()
print("PRODUCTION_QUEUE_TOTAL_BEFORE=", prod_total_before)
print("PRODUCTION_QUEUE_COUNTS_BEFORE=", prod_counts_before)

if DB.exists():
    con = sqlite3.connect(str(DB))
    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        task_rows = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    finally:
        con.close()
    print("PRODUCTION_DB_INTEGRITY=", integrity)
    print("PRODUCTION_DB_TASK_ROWS=", task_rows)
    if integrity != "ok":
        raise SystemExit("V65_68_ABORT=production_db_integrity_failed")
else:
    print("PRODUCTION_DB=NOT_PRESENT")

smoke = r"""
from pathlib import Path
import json, sqlite3, uuid
from collections import Counter

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

q = AutonomousTaskQueue()
loop = AutonomousGoalExecutionLoop(q)

goal_id = "v65-68-smoke-" + uuid.uuid4().hex[:12]

research = q.enqueue(
    task_type="research",
    payload={
        "goal_id": goal_id,
        "stage": "research",
        "topic": "CompanyOS controlled runtime validation",
        "evidence": ["local smoke-test evidence only"],
    },
    priority=999,
    idempotency_key=goal_id + ":research",
    max_attempts=2,
)

planning = q.enqueue(
    task_type="planning",
    payload={
        "goal_id": goal_id,
        "stage": "planning",
        "depends_on_stage": "research",
        "goal": "Validate dependency-aware planning execution",
        "constraints": ["no external actions"],
    },
    priority=998,
    idempotency_key=goal_id + ":planning",
    max_attempts=2,
)

build = q.enqueue(
    task_type="build",
    payload={
        "goal_id": goal_id,
        "stage": "build",
        "depends_on_stage": "planning",
        "name": "CompanyOS runtime smoke artifact",
        "deliverable": "local manifest only",
    },
    priority=997,
    idempotency_key=goal_id + ":build",
    max_attempts=2,
)

print("SMOKE_GOAL_ID=", goal_id)
print("ENQUEUED_IDS=", [research.task_id, planning.task_id, build.task_id])
print("REGISTERED_BASE_HANDLERS=", sorted(loop.dispatcher.dispatcher.handlers.keys()))

results = loop.run_until_idle(max_cycles=10, sleep_seconds=0)
for idx, item in enumerate(results, 1):
    print("CYCLE_RESULT_%02d=" % idx, item)

tasks = q.all_tasks()
counts = Counter(t.state for t in tasks)
print("ISOLATED_FINAL_COUNTS=", dict(sorted(counts.items())))

target = [t for t in tasks if isinstance(t.payload, dict) and t.payload.get("goal_id") == goal_id]
target.sort(key=lambda t: {"research":0, "planning":1, "build":2}.get(t.payload.get("stage"), 99))
print("TARGET_TASK_STATES=", [(t.payload.get("stage"), t.state, t.attempts, t.last_error) for t in target])

if len(target) != 3:
    raise SystemExit("SMOKE_FAIL=target_task_count")
if any(t.state != "COMPLETED" for t in target):
    raise SystemExit("SMOKE_FAIL=task_not_completed")

for stage in ("research", "planning", "build"):
    if not q.has_completed_goal_stage(goal_id, stage):
        raise SystemExit("SMOKE_FAIL=completed_stage_missing:" + stage)
print("DEPENDENCY_CHAIN=PASS")

evidence_dir = Path.home() / ".companyos_runtime" / "specialist_evidence"
artifacts = sorted(evidence_dir.glob("*.json"))
print("EVIDENCE_FILES=", [str(p) for p in artifacts])
if len(artifacts) < 3:
    raise SystemExit("SMOKE_FAIL=evidence_artifacts_missing")

external_flags = []
for p in artifacts:
    data = json.loads(p.read_text())
    if "external_research_performed" in data:
        external_flags.append(("external_research_performed", data["external_research_performed"]))
    if "external_deployment_performed" in data:
        external_flags.append(("external_deployment_performed", data["external_deployment_performed"]))
print("EXTERNAL_ACTION_FLAGS=", external_flags)
if any(bool(v) for _, v in external_flags):
    raise SystemExit("SMOKE_FAIL=unexpected_external_action_flag")

db = q.kernel.db_path
con = sqlite3.connect(str(db))
try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    rows = con.execute(
        "SELECT task_id, state, stage, goal_id FROM tasks WHERE goal_id=? ORDER BY stage",
        (goal_id,),
    ).fetchall()
finally:
    con.close()

print("ISOLATED_DB_INTEGRITY=", integrity)
print("ISOLATED_DB_ROWS=", rows)
if integrity != "ok":
    raise SystemExit("SMOKE_FAIL=isolated_db_integrity")
if len(rows) != 3 or any(r[1] != "COMPLETED" for r in rows):
    raise SystemExit("SMOKE_FAIL=durable_projection_mismatch")

print("QUEUE_DISPATCH_LEASE_DEPENDENCY_EVIDENCE=PASS")
print("V65_68_ISOLATED_RUNTIME=PASS")
"""

with tempfile.TemporaryDirectory(prefix="companyos_v65_68_") as td:
    fake_home = Path(td)
    env = os.environ.copy()
    env["HOME"] = str(fake_home)
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["COMPANYOS_QUEUE_SCAN_LIMIT"] = "100"

    cp = subprocess.run(
        [sys.executable, "-c", smoke],
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
    )

    print("ISOLATED_RUNTIME_RETURN_CODE=", cp.returncode)
    print("ISOLATED_RUNTIME_STDOUT_BEGIN")
    print(cp.stdout)
    print("ISOLATED_RUNTIME_STDOUT_END")
    if cp.stderr:
        print("ISOLATED_RUNTIME_STDERR_BEGIN")
        print(cp.stderr)
        print("ISOLATED_RUNTIME_STDERR_END")

    if cp.returncode != 0:
        raise SystemExit("V65_68_ABORT=isolated_runtime_failed")

prod_total_after, prod_counts_after = production_counts()
print("PRODUCTION_QUEUE_TOTAL_AFTER=", prod_total_after)
print("PRODUCTION_QUEUE_COUNTS_AFTER=", prod_counts_after)

if prod_total_after != prod_total_before or prod_counts_after != prod_counts_before:
    raise SystemExit("V65_68_ABORT=production_queue_changed_during_isolated_test")

print("PRODUCTION_QUEUE_UNCHANGED=PASS")
print("V65_68_CONTROLLED_RUNTIME_VALIDATION=PASS")
PY
