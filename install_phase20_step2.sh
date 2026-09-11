#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase20_step2_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 20 Step 2 - Runtime-Aware Preflight Gate"
echo "============================================================"

for f in \
  "$AGENTS/runtime_aware_preflight.py" \
  "$CTL/preflight2ctl" \
  "$MEM/preflight2_config.json" \
  "$MEM/preflight2_state.json" \
  "$MEM/preflight2_report.json" \
  "$MEM/preflight2_health.json" \
  "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/preflight2_config.json" <<'JSON'
{
  "enabled": true,
  "require_runtime_hygiene_check": true,
  "require_github_connector_health": true,
  "require_no_source_changes_for_ready_state": true,
  "allow_runtime_only_changes": true,
  "maximum_change_risk_score": 34,
  "automatic_git_reset": false,
  "automatic_git_clean": false,
  "automatic_commit": false,
  "automatic_push": false,
  "automatic_deploy": false
}
JSON

cat > "$AGENTS/runtime_aware_preflight.py" <<'PY'
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

CFG = MEM / "preflight2_config.json"
STATE = MEM / "preflight2_state.json"
REPORT = MEM / "preflight2_report.json"
HEALTH = MEM / "preflight2_health.json"

HYGIENE = MEM / "runtime_hygiene_state.json"
GH_HEALTH = MEM / "github_read_health.json"
RISK = MEM / "github_change_report.json"

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

def run_hygiene() -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["python", "companyos/runtimehygienectl", "isolate"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=180
        )
        return {
            "success": proc.returncode == 0,
            "stdout": proc.stdout[-2500:],
            "stderr": proc.stderr[-1200:]
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def evaluate() -> dict[str, Any]:
    cfg = load(CFG, {})
    hygiene_run = None

    if cfg.get("require_runtime_hygiene_check", True):
        hygiene_run = run_hygiene()

    hygiene = load(HYGIENE, {})
    github = load(GH_HEALTH, {})
    risk = load(RISK, {})

    blockers = []
    warnings = []

    source_changes = int(hygiene.get("source_change_count", 0))
    runtime_changes = int(hygiene.get("runtime_only_change_count", 0))
    effectively_clean = bool(hygiene.get("working_tree_effectively_clean", False))
    risk_score = int(risk.get("risk_score", 0))

    if cfg.get("require_no_source_changes_for_ready_state", True) and not effectively_clean:
        blockers.append("source_controlled_changes_present")

    if cfg.get("require_github_connector_health", True) and github.get("healthy") is False:
        blockers.append("github_connector_unhealthy")

    if risk_score > int(cfg.get("maximum_change_risk_score", 34)):
        blockers.append("change_risk_above_threshold")

    if runtime_changes and cfg.get("allow_runtime_only_changes", True):
        warnings.append(f"{runtime_changes} runtime-only change(s) ignored for readiness")

    decision = "ready" if not blockers else "blocked"

    report = {
        "generated_at": now(),
        "decision": decision,
        "blockers": blockers,
        "warnings": warnings,
        "runtime_hygiene_run": hygiene_run,
        "source_change_count": source_changes,
        "runtime_only_change_count": runtime_changes,
        "working_tree_effectively_clean": effectively_clean,
        "github_connector_healthy": github.get("healthy"),
        "change_risk_score": risk_score,
        "automatic_git_reset": False,
        "automatic_git_clean": False,
        "automatic_commit": False,
        "automatic_push": False,
        "automatic_deploy": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_evaluated_at": now(),
        "decision": decision,
        "blocker_count": len(blockers),
        "warning_count": len(warnings)
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "decision": decision,
        "blocker_count": len(blockers)
    })

    return {
        "success": True,
        "status": "runtime_aware_preflight_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "runtime_aware_preflight_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "run":
        result = evaluate()
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

chmod +x "$AGENTS/runtime_aware_preflight.py"

cat > "$CTL/preflight2ctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "runtime_aware_preflight.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/preflight2ctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/runtime_aware_preflight.py" "$CTL/preflight2ctl"

echo "[2/6] Running runtime-aware preflight..."
python "$CTL/preflight2ctl" run

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "runtime-aware-preflight",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/preflight2ctl", "run"]
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

echo "[5/6] Checking status..."
python "$CTL/preflight2ctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "runtime_aware_preflight.py",
    root / "companyos" / "preflight2ctl",
    root / "ceo_memory" / "preflight2_config.json",
    root / "ceo_memory" / "preflight2_state.json",
    root / "ceo_memory" / "preflight2_report.json",
    root / "ceo_memory" / "preflight2_health.json",
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
        "automatic_git_reset",
        "automatic_git_clean",
        "automatic_commit",
        "automatic_push",
        "automatic_deploy"
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    sched = json.loads(required[6].read_text())
    job = next(
        (x for x in sched.get("jobs", []) if x.get("id") == "runtime-aware-preflight"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Runtime-aware preflight scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 2 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 2 INSTALLED"
echo " RUNTIME-AWARE PREFLIGHT GATE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/preflight2ctl run"
echo "  python companyos/preflight2ctl status"
