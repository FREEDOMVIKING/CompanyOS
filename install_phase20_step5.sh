#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase20_step5_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 20 Step 5 - Autonomous Action Dispatcher"
echo "============================================================"

for f in \
  "$AGENTS/action_dispatcher.py" \
  "$CTL/dispatchctl" \
  "$MEM/action_dispatcher_config.json" \
  "$MEM/action_dispatcher_queue.json" \
  "$MEM/action_dispatcher_state.json" \
  "$MEM/action_dispatcher_report.json" \
  "$MEM/action_dispatcher_health.json" \
  "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/action_dispatcher_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_dispatch": true,
  "maximum_actions_per_cycle": 10,
  "allowed_categories": [
    "internal_read_only",
    "internal_reversible",
    "external_read_only"
  ],
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false,
  "credential_export": false,
  "private_key_export": false
}
JSON

cat > "$AGENTS/action_dispatcher.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "action_dispatcher_config.json"
ELIGIBILITY = MEM / "execution_eligibility_report.json"
ACTION_QUEUE = MEM / "action_queue_report.json"
QUEUE = MEM / "action_dispatcher_queue.json"
STATE = MEM / "action_dispatcher_state.json"
REPORT = MEM / "action_dispatcher_report.json"
HEALTH = MEM / "action_dispatcher_health.json"

ACTION_MAP = {
    "refresh-priorities": {
        "category": "internal_reversible",
        "command": ["python", "companyos/priorityctl", "rank"]
    },
    "refresh-decisions": {
        "category": "internal_reversible",
        "command": ["python", "companyos/decisionctl", "prepare"]
    },
    "refresh-forecast": {
        "category": "internal_read_only",
        "command": ["python", "companyos/forecastctl", "forecast"]
    },
    "refresh-brief": {
        "category": "internal_read_only",
        "command": ["python", "companyos/briefctl", "generate"]
    },
    "refresh-goals": {
        "category": "internal_reversible",
        "command": ["python", "companyos/goalctl", "generate"]
    },
    "run-learning": {
        "category": "internal_reversible",
        "command": ["python", "companyos/learningctl", "learn"]
    },
    "run-health": {
        "category": "internal_read_only",
        "command": ["python", "companyos/healthctl", "run"]
    },
    "run-readiness": {
        "category": "internal_read_only",
        "command": ["python", "companyos/readiness2ctl", "run"]
    },
    "run-outcomes": {
        "category": "internal_read_only",
        "command": ["python", "companyos/outcomectl", "measure"]
    },
    "github-read": {
        "category": "external_read_only",
        "command": ["python", "companyos/githubreadctl", "repos", "20"]
    }
}

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)

def run(command: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=300
        )
        return {
            "success": proc.returncode == 0,
            "return_code": proc.returncode,
            "stdout": proc.stdout[-3000:],
            "stderr": proc.stderr[-1500:]
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc)
        }

def build_queue() -> list[dict[str, Any]]:
    eligibility = load(ELIGIBILITY, {})
    eligible = eligibility.get("eligibility", {})
    source = load(ACTION_QUEUE, {})
    selected = source.get("selected", [])

    queue: list[dict[str, Any]] = []

    for item in selected:
        name = item.get("action")
        spec = ACTION_MAP.get(name)
        if not spec:
            continue

        category = spec["category"]
        queue.append({
            "action": name,
            "category": category,
            "priority": int(item.get("priority", 0)),
            "reason": item.get("reason"),
            "eligible": bool(eligible.get(category, False))
        })

    # Keep one live read path available whenever external reads are eligible.
    if eligible.get("external_read_only", False):
        queue.append({
            "action": "github-read",
            "category": "external_read_only",
            "priority": 40,
            "reason": "Refresh live GitHub repository data.",
            "eligible": True
        })

    # De-duplicate by action name and keep highest priority occurrence.
    deduped: dict[str, dict[str, Any]] = {}
    for item in queue:
        current = deduped.get(item["action"])
        if current is None or item["priority"] > current["priority"]:
            deduped[item["action"]] = item

    return sorted(
        deduped.values(),
        key=lambda x: x["priority"],
        reverse=True
    )

def dispatch() -> dict[str, Any]:
    cfg = load(CFG, {})
    eligibility = load(ELIGIBILITY, {})
    system_ready = eligibility.get("system_ready") is True
    allowed_categories = set(cfg.get("allowed_categories", []))

    queue = build_queue()
    save(QUEUE, {
        "generated_at": now(),
        "system_ready": system_ready,
        "queue": queue
    })

    if not system_ready:
        report = {
            "generated_at": now(),
            "status": "dispatch_blocked_system_not_ready",
            "system_ready": False,
            "queued_count": len(queue),
            "executed_count": 0,
            "results": []
        }
        save(REPORT, report)
        save(STATE, {
            "last_dispatch_at": now(),
            "system_ready": False,
            "executed_count": 0,
            "blocked_count": len(queue)
        })
        save(HEALTH, {
            "healthy": True,
            "last_checked_at": now(),
            "system_ready": False,
            "dispatch_blocked": True
        })
        return {
            "success": True,
            "status": "dispatch_blocked_system_not_ready",
            "report": report
        }

    maximum = int(cfg.get("maximum_actions_per_cycle", 10))
    results = []
    blocked = []

    for item in queue[:maximum]:
        name = item["action"]
        category = item["category"]
        spec = ACTION_MAP.get(name)

        if not item.get("eligible") or category not in allowed_categories:
            blocked.append({
                **item,
                "status": "blocked_by_eligibility"
            })
            continue

        if not spec:
            blocked.append({
                **item,
                "status": "action_not_mapped"
            })
            continue

        result = run(spec["command"])
        results.append({
            "action": name,
            "category": category,
            "priority": item["priority"],
            "reason": item.get("reason"),
            "result": result,
            "success": result.get("success", False)
        })

    failures = [x for x in results if not x.get("success")]

    report = {
        "generated_at": now(),
        "status": "dispatch_complete",
        "system_ready": True,
        "queued_count": len(queue),
        "executed_count": len(results),
        "blocked_count": len(blocked),
        "failure_count": len(failures),
        "results": results,
        "blocked": blocked,
        "automatic_external_write": False,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False,
        "credential_export": False,
        "private_key_export": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_dispatch_at": now(),
        "system_ready": True,
        "executed_count": len(results),
        "blocked_count": len(blocked),
        "failure_count": len(failures)
    })
    save(HEALTH, {
        "healthy": len(failures) == 0,
        "last_checked_at": now(),
        "system_ready": True,
        "failure_count": len(failures)
    })

    return {
        "success": len(failures) == 0,
        "status": "dispatch_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "action_dispatcher_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {}),
        "queue": load(QUEUE, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "run":
        result = dispatch()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["run", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/action_dispatcher.py"

cat > "$CTL/dispatchctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "action_dispatcher.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/dispatchctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/action_dispatcher.py" "$CTL/dispatchctl"

echo "[2/6] Running action dispatcher..."
python "$CTL/dispatchctl" run || true

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "autonomous-action-dispatcher",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/dispatchctl", "run"]
}

existing = next((x for x in jobs if x.get("id") == job["id"]), None)

if existing:
    existing.clear()
    existing.update(job)
else:
    jobs.append(job)

p.write_text(json.dumps(d, indent=2), encoding="utf-8")
print(json.dumps({"success": True, "job_id": job["id"]}, indent=2))
PY

echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart

echo "[5/6] Checking dispatcher status..."
python "$CTL/dispatchctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "action_dispatcher.py",
    root / "companyos" / "dispatchctl",
    root / "ceo_memory" / "action_dispatcher_config.json",
    root / "ceo_memory" / "action_dispatcher_queue.json",
    root / "ceo_memory" / "action_dispatcher_state.json",
    root / "ceo_memory" / "action_dispatcher_report.json",
    root / "ceo_memory" / "action_dispatcher_health.json",
    root / "ceo_memory" / "autonomous_operations_config.json"
]

for path in required:
    if not path.exists() or path.stat().st_size <= 0:
        errors.append(f"Missing/empty: {path}")

for path in required[:2]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(str(exc))

try:
    cfg = json.loads(required[2].read_text())

    for key in [
        "automatic_external_write",
        "automatic_customer_contact",
        "automatic_publication",
        "automatic_spending",
        "automatic_destructive_actions",
        "credential_export",
        "private_key_export"
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    sched = json.loads(required[7].read_text())
    job = next(
        (x for x in sched.get("jobs", []) if x.get("id") == "autonomous-action-dispatcher"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Autonomous action dispatcher scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 5 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 5 INSTALLED"
echo " AUTONOMOUS ACTION DISPATCHER ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/dispatchctl run"
echo "  python companyos/dispatchctl status"
