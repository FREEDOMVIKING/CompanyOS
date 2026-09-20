#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

echo "===== COMPANYOS V27.8B FAST DEPENDENCY AUDIT ====="
echo "This is read-only. No queue records are changed."

python - <<'PY'
import json, time
from pathlib import Path
from collections import Counter, defaultdict

root = Path.home()/".companyos_runtime"/"task_queue"
files = list(root.glob("*.json"))

states = Counter()
types = Counter()
reasons = Counter()
completed_stages = set()
queued = []

# ONE filesystem pass only.
for p in files:
    try:
        x = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        reasons["unreadable"] += 1
        continue

    state = str(x.get("state","UNKNOWN")).upper()
    states[state] += 1
    payload = x.get("payload") if isinstance(x.get("payload"), dict) else {}

    if state == "COMPLETED":
        gid = payload.get("goal_id")
        stage = payload.get("stage")
        if gid and stage:
            completed_stages.add((str(gid), str(stage)))

    if state == "QUEUED":
        queued.append(x)
        types[str(x.get("task_type","UNKNOWN"))] += 1

registered = {"research","planning","build"}
now = time.time()
examples = {}

for x in queued:
    payload = x.get("payload") if isinstance(x.get("payload"), dict) else {}
    task_type = str(x.get("task_type","UNKNOWN"))
    attempts = int(x.get("attempts",0) or 0)
    max_attempts = int(x.get("max_attempts",1) or 1)
    next_attempt = float(x.get("next_attempt_unix",0) or 0)

    if attempts >= max_attempts:
        reason = "max_attempts"
    elif next_attempt > now:
        reason = "retry_delay"
    elif task_type not in registered:
        reason = "missing_handler"
    else:
        dep = payload.get("depends_on_stage")
        gid = payload.get("goal_id")
        if not dep:
            reason = "execution_ready"
        elif not gid:
            reason = "legacy_missing_goal_id"
        elif (str(gid), str(dep)) in completed_stages:
            reason = "execution_ready"
        else:
            reason = "dependency_blocked"

    reasons[reason] += 1
    examples.setdefault(reason, {
        "task_id": x.get("task_id"),
        "task_type": task_type,
        "attempts": attempts,
        "max_attempts": max_attempts,
        "goal_id": payload.get("goal_id"),
        "stage": payload.get("stage"),
        "depends_on_stage": payload.get("depends_on_stage"),
    })

print("TOTAL_FILES:", len(files))
print("STATES:", dict(states))
print("QUEUED_TYPES:", dict(types))
print("COMPLETED_STAGE_KEYS:", len(completed_stages))
print("BLOCKERS:", dict(reasons))
print("EXAMPLES:")
for k,v in examples.items():
    print(" ", k, "=>", v)
print("V27_8B_FAST_AUDIT=PASS")
PY

echo "===== SUPERVISOR ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
echo "===== CONTINUOUS RUNTIME ====="
pgrep -af 'companyos.runtime.continuous_goal_runtime' || true
echo "===== V27.8B COMPLETE ====="
