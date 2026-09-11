#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase19_step8_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 19 Step 8 - GitHub Change Intelligence & Risk Scoring"
echo "============================================================"

for f in \
 "$AGENTS/github_change_intelligence.py" \
 "$CTL/githubchangectl" \
 "$MEM/github_change_config.json" \
 "$MEM/github_change_state.json" \
 "$MEM/github_change_report.json" \
 "$MEM/github_change_health.json" \
 "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/github_change_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_change_analysis": true,
  "automatic_risk_scoring": true,
  "automatic_internal_recommendations": true,
  "high_risk_file_patterns": [
    "companyos/githubctl",
    "companyos/gatewayctl",
    "companyos/permissionctl",
    "companyos/operationsctl",
    "agents/autonomous_orchestrator.py",
    "agents/exception_recovery_engine.py"
  ],
  "automatic_repository_mutation": false,
  "automatic_issue_creation": false,
  "automatic_pull_request_creation": false,
  "automatic_merge": false,
  "automatic_publication": false,
  "automatic_spending": false
}
JSON

cat > "$AGENTS/github_change_intelligence.py" <<'PY'
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

CFG = MEM / "github_change_config.json"
STATE = MEM / "github_change_state.json"
REPORT = MEM / "github_change_report.json"
HEALTH = MEM / "github_change_health.json"

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

def git(*args: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60
        )
        return {
            "success": proc.returncode == 0,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip()
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def analyze() -> dict[str, Any]:
    cfg = load(CFG, {})
    if not cfg.get("enabled", True):
        return {"success": False, "status": "github_change_intelligence_disabled"}

    status = git("status", "--porcelain")
    diffstat = git("diff", "--stat")
    changed = git("diff", "--name-only")
    staged = git("diff", "--cached", "--name-only")

    unstaged_files = [
        x for x in changed.get("stdout", "").splitlines() if x.strip()
    ]
    staged_files = [
        x for x in staged.get("stdout", "").splitlines() if x.strip()
    ]
    all_files = sorted(set(unstaged_files + staged_files))

    high_patterns = cfg.get("high_risk_file_patterns", [])
    high_risk_files = [
        f for f in all_files
        if any(pattern in f for pattern in high_patterns)
    ]

    risk = 0
    reasons = []

    if all_files:
        risk += min(30, len(all_files) * 3)
        reasons.append(f"{len(all_files)} changed file(s) detected")

    if high_risk_files:
        risk += min(50, len(high_risk_files) * 15)
        reasons.append("High-risk control files changed")

    if staged_files and unstaged_files:
        risk += 10
        reasons.append("Both staged and unstaged changes exist")

    risk = min(100, risk)

    if risk >= 70:
        band = "high"
    elif risk >= 35:
        band = "medium"
    else:
        band = "low"

    recommendations = []
    if not all_files:
        recommendations.append("No local code changes detected.")
    else:
        recommendations.append("Run tests before push.")
        if high_risk_files:
            recommendations.append("Review high-risk control files before deployment.")
        if band == "high":
            recommendations.append("Require explicit owner review before production deployment.")

    report = {
        "generated_at": now(),
        "risk_score": risk,
        "risk_band": band,
        "reasons": reasons,
        "changed_files": all_files,
        "high_risk_files": high_risk_files,
        "diff_stat": diffstat.get("stdout"),
        "working_tree_status": status.get("stdout"),
        "recommendations": recommendations,
        "automatic_repository_mutation": False,
        "automatic_issue_creation": False,
        "automatic_pull_request_creation": False,
        "automatic_merge": False
    }

    save(REPORT, report)
    save(STATE, {
        "generated_at": now(),
        "risk_score": risk,
        "risk_band": band,
        "changed_file_count": len(all_files),
        "high_risk_file_count": len(high_risk_files)
    })
    save(HEALTH, {
        "healthy": True,
        "last_analyzed_at": now(),
        "risk_score": risk,
        "risk_band": band
    })

    return {
        "success": True,
        "status": "github_change_intelligence_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "github_change_intelligence_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "analyze":
        result = analyze()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["analyze", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/github_change_intelligence.py"

cat > "$CTL/githubchangectl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "github_change_intelligence.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/githubchangectl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/github_change_intelligence.py" "$CTL/githubchangectl"

echo "[2/5] Running change intelligence..."
python "$CTL/githubchangectl" analyze

echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "github-change-intelligence",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/githubchangectl", "analyze"]
}

existing = next((x for x in jobs if x.get("id") == job["id"]), None)
if existing:
    existing.clear()
    existing.update(job)
else:
    jobs.append(job)

p.write_text(json.dumps(d, indent=2))
print(json.dumps({"success": True, "job_id": job["id"]}, indent=2))
PY

echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
python "$CTL/githubchangectl" status

echo "[5/5] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

r = Path.home()/"companyos"
errors = []

req = [
    r/"agents"/"github_change_intelligence.py",
    r/"companyos"/"githubchangectl",
    r/"ceo_memory"/"github_change_config.json",
    r/"ceo_memory"/"github_change_state.json",
    r/"ceo_memory"/"github_change_report.json",
    r/"ceo_memory"/"github_change_health.json",
    r/"ceo_memory"/"autonomous_operations_config.json"
]

for p in req:
    if not p.exists() or p.stat().st_size <= 0:
        errors.append(f"Missing/empty: {p}")

for p in req[:2]:
    try:
        py_compile.compile(str(p), doraise=True)
    except Exception as exc:
        errors.append(str(exc))

try:
    cfg = json.loads(req[2].read_text())
    for key in [
        "automatic_repository_mutation",
        "automatic_issue_creation",
        "automatic_pull_request_creation",
        "automatic_merge",
        "automatic_publication",
        "automatic_spending"
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    report = json.loads(req[4].read_text())
    for key in ["risk_score", "risk_band", "changed_files", "recommendations"]:
        if key not in report:
            errors.append(f"Missing report field: {key}")

    sched = json.loads(req[6].read_text())
    job = next(
        (x for x in sched.get("jobs", [])
         if x.get("id") == "github-change-intelligence"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("GitHub change intelligence scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 19 Step 8 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 19 STEP 8 INSTALLED"
echo " GITHUB CHANGE INTELLIGENCE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/githubchangectl analyze"
echo "  python companyos/githubchangectl status"
echo
echo "Autonomous schedule:"
echo "  Change-risk analysis runs every 30 minutes"
