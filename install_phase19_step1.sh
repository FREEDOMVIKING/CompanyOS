#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase19_step1_$(date +%Y%m%d_%H%M%S)"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 19 Step 1 - Controlled Execution Gateway"
echo "============================================================"

for f in "$AGENTS/execution_gateway.py" "$CTL/gatewayctl" \
 "$MEM/execution_gateway_config.json" "$MEM/execution_gateway_queue.json" \
 "$MEM/execution_gateway_state.json" "$MEM/execution_gateway_health.json" \
 "$MEM/execution_gateway_audit.json" "$MEM/autonomous_operations_config.json"; do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/execution_gateway_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_execution": true,
  "automatic_external_read": true,
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false,
  "credential_export": false,
  "private_key_export": false,
  "kill_switch_file": "ceo_memory/HALT_AUTONOMY",
  "max_requests_per_cycle": 20,
  "max_duplicate_window_seconds": 3600,
  "allowed_internal_actions": [
    "integrity-check",
    "backup-create",
    "priority-rank",
    "decision-prepare",
    "execution-plan-prepare",
    "improvement-analyze",
    "performance-collect",
    "forecast-run",
    "brief-generate",
    "goal-generate",
    "learning-run",
    "health-run",
    "mission-build",
    "readiness-check",
    "outcome-measure",
    "strategy-feedback"
  ]
}
JSON

cat > "$AGENTS/execution_gateway.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CONFIG = MEM / "execution_gateway_config.json"
QUEUE = MEM / "execution_gateway_queue.json"
STATE = MEM / "execution_gateway_state.json"
HEALTH = MEM / "execution_gateway_health.json"
AUDIT = MEM / "execution_gateway_audit.json"
HALT = MEM / "HALT_AUTONOMY"

ACTION_MAP = {
    "integrity-check": ["python", "companyos/integrityctl", "check"],
    "backup-create": ["python", "companyos/integrityctl", "backup"],
    "priority-rank": ["python", "companyos/priorityctl", "rank"],
    "decision-prepare": ["python", "companyos/decisionctl", "prepare"],
    "execution-plan-prepare": ["python", "companyos/executionplanctl", "prepare"],
    "improvement-analyze": ["python", "companyos/improvementctl", "analyze"],
    "performance-collect": ["python", "companyos/performancectl", "collect"],
    "forecast-run": ["python", "companyos/forecastctl", "forecast"],
    "brief-generate": ["python", "companyos/briefctl", "generate"],
    "goal-generate": ["python", "companyos/goalctl", "generate"],
    "learning-run": ["python", "companyos/learningctl", "learn"],
    "health-run": ["python", "companyos/healthctl", "run"],
    "mission-build": ["python", "companyos/missionctl", "build"],
    "readiness-check": ["python", "companyos/readinessctl", "check"],
    "outcome-measure": ["python", "companyos/outcomectl", "measure"],
    "strategy-feedback": ["python", "companyos/strategyfeedbackctl", "adapt"]
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def audit(action: str, result: dict[str, Any]) -> None:
    records = load(AUDIT, [])
    if not isinstance(records, list):
        records = []
    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result
    })
    save(AUDIT, records[-2000:])


def fingerprint(request: dict[str, Any]) -> str:
    material = json.dumps({
        "action": request.get("action"),
        "scope": request.get("scope"),
        "payload": request.get("payload", {})
    }, sort_keys=True)
    return hashlib.sha256(material.encode()).hexdigest()


def enqueue(action: str, scope: str = "internal", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = load(CONFIG, {})
    store = load(QUEUE, {"schema_version": 1, "requests": []})
    requests = store.setdefault("requests", [])

    request = {
        "id": f"req-{int(time.time()*1000)}",
        "action": action,
        "scope": scope,
        "payload": payload or {},
        "status": "pending",
        "created_at": now()
    }
    request["fingerprint"] = fingerprint(request)

    window = int(cfg.get("max_duplicate_window_seconds", 3600))
    cutoff = time.time() - window

    for existing in requests:
        if existing.get("fingerprint") != request["fingerprint"]:
            continue
        try:
            ts = datetime.fromisoformat(existing.get("created_at")).timestamp()
        except Exception:
            ts = 0
        if ts >= cutoff and existing.get("status") in {"pending", "completed"}:
            result = {
                "success": True,
                "status": "duplicate_suppressed",
                "existing_request_id": existing.get("id")
            }
            audit("enqueue", result)
            return result

    requests.append(request)
    save(QUEUE, store)

    result = {
        "success": True,
        "status": "gateway_request_enqueued",
        "request": request
    }
    audit("enqueue", result)
    return result


def classify(request: dict[str, Any]) -> dict[str, Any]:
    cfg = load(CONFIG, {})
    scope = request.get("scope")
    action = request.get("action")

    if HALT.exists():
        return {
            "allowed": False,
            "reason": "autonomy_halted"
        }

    if scope == "internal":
        allowed = action in set(cfg.get("allowed_internal_actions", []))
        return {
            "allowed": allowed,
            "requires_owner_approval": False,
            "reason": "internal_allowlisted" if allowed else "internal_not_allowlisted"
        }

    if scope == "external_read":
        return {
            "allowed": bool(cfg.get("automatic_external_read", True)),
            "requires_owner_approval": False,
            "reason": "external_read_policy"
        }

    if scope in {
        "external_write",
        "customer_contact",
        "publication",
        "spending",
        "destructive",
        "credential_export",
        "private_key_export"
    }:
        return {
            "allowed": False,
            "requires_owner_approval": True,
            "reason": "owner_approval_required"
        }

    return {
        "allowed": False,
        "requires_owner_approval": True,
        "reason": "unknown_scope"
    }


def execute_internal(action: str) -> dict[str, Any]:
    command = ACTION_MAP.get(action)

    if not command:
        return {
            "success": False,
            "status": "unknown_internal_action",
            "action": action
        }

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
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-2000:]
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc)
        }


def process() -> dict[str, Any]:
    cfg = load(CONFIG, {})

    if not cfg.get("enabled", True):
        result = {
            "success": False,
            "status": "execution_gateway_disabled"
        }
        audit("process", result)
        return result

    store = load(QUEUE, {"schema_version": 1, "requests": []})
    requests = store.setdefault("requests", [])
    maximum = int(cfg.get("max_requests_per_cycle", 20))

    pending = [r for r in requests if r.get("status") == "pending"][:maximum]
    results = []

    for request in pending:
        policy = classify(request)
        request["policy"] = policy

        if not policy.get("allowed"):
            request["status"] = (
                "approval_required"
                if policy.get("requires_owner_approval")
                else "blocked"
            )
            request["updated_at"] = now()
            results.append({
                "request_id": request.get("id"),
                "success": False,
                "status": request["status"],
                "policy": policy
            })
            continue

        if request.get("scope") == "internal":
            execution = execute_internal(str(request.get("action")))
        else:
            execution = {
                "success": True,
                "status": "external_read_allowed_no_connector_bound"
            }

        request["status"] = "completed" if execution.get("success") else "failed"
        request["updated_at"] = now()
        request["execution"] = execution

        results.append({
            "request_id": request.get("id"),
            "success": execution.get("success", False),
            "status": request["status"],
            "execution": execution
        })

    save(QUEUE, store)

    completed = sum(1 for r in requests if r.get("status") == "completed")
    pending_count = sum(1 for r in requests if r.get("status") == "pending")
    approval_count = sum(
        1 for r in requests if r.get("status") == "approval_required"
    )

    state = {
        "generated_at": now(),
        "processed_this_cycle": len(pending),
        "completed_total": completed,
        "pending_total": pending_count,
        "approval_required_total": approval_count,
        "halted": HALT.exists()
    }
    save(STATE, state)

    save(HEALTH, {
        "healthy": True,
        "last_processed_at": now(),
        "processed_this_cycle": len(pending),
        "approval_required_total": approval_count,
        "halted": HALT.exists()
    })

    result = {
        "success": True,
        "status": "execution_gateway_cycle_complete",
        "state": state,
        "results": results
    }
    audit("process", result)
    return result


def status() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "execution_gateway_status",
        "config": load(CONFIG, {}),
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "queue": load(QUEUE, {})
    }
    audit("status", result)
    return result


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "enqueue":
        if len(sys.argv) < 3:
            result = {
                "success": False,
                "status": "action_required"
            }
        else:
            scope = sys.argv[3] if len(sys.argv) > 3 else "internal"
            result = enqueue(sys.argv[2], scope)

    elif action == "process":
        result = process()

    elif action == "status":
        result = status()

    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["enqueue", "process", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/execution_gateway.py"

cat > "$CTL/gatewayctl" <<'PY'
#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "execution_gateway.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/gatewayctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/execution_gateway.py" "$CTL/gatewayctl"

echo "[2/6] Initializing gateway queue..."
python "$CTL/gatewayctl" enqueue integrity-check internal
python "$CTL/gatewayctl" process

echo "[3/6] Adding gateway to autonomous scheduler..."
python - <<'PY'
import json
from pathlib import Path

p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text())
jobs=d.setdefault("jobs",[])

job={
 "id":"execution-gateway",
 "enabled":True,
 "interval_seconds":900,
 "command":["python","companyos/gatewayctl","process"]
}

e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:
 e.clear();e.update(job)
else:
 jobs.append(job)

p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY

echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart

echo "[5/6] Checking gateway status..."
python "$CTL/gatewayctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json, py_compile
from pathlib import Path

r=Path.home()/"companyos"
errors=[]

required=[
 r/"agents"/"execution_gateway.py",
 r/"companyos"/"gatewayctl",
 r/"ceo_memory"/"execution_gateway_config.json",
 r/"ceo_memory"/"execution_gateway_queue.json",
 r/"ceo_memory"/"execution_gateway_state.json",
 r/"ceo_memory"/"execution_gateway_health.json",
 r/"ceo_memory"/"autonomous_operations_config.json"
]

for p in required:
    if not p.exists() or p.stat().st_size<=0:
        errors.append(f"Missing/empty: {p}")

for p in required[:2]:
    try:
        py_compile.compile(str(p),doraise=True)
    except Exception as e:
        errors.append(f"Compile error: {e}")

try:
    cfg=json.loads(required[2].read_text())
    for k in [
        "automatic_external_write",
        "automatic_customer_contact",
        "automatic_publication",
        "automatic_spending",
        "automatic_destructive_actions",
        "credential_export",
        "private_key_export"
    ]:
        if cfg.get(k) is not False:
            errors.append(f"{k} must remain disabled")

    sched=json.loads(required[6].read_text())
    job=next(
        (x for x in sched.get("jobs",[]) if x.get("id")=="execution-gateway"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Execution gateway scheduler job missing/disabled")

except Exception as e:
    errors.append(str(e))

print("--------------------------------------------")
print("Phase 19 Step 1 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for e in errors:
    print("ERROR:",e)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 19 STEP 1 INSTALLED"
echo " CONTROLLED EXECUTION GATEWAY ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/gatewayctl enqueue integrity-check internal"
echo "  python companyos/gatewayctl process"
echo "  python companyos/gatewayctl status"
echo
echo "Autonomous schedule:"
echo "  Gateway processes requests every 15 minutes"
