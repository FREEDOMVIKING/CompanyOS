#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase19_step7_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 19 Step 7 - GitHub Intelligence Integration"
echo "============================================================"

for f in \
 "$AGENTS/github_intelligence_engine.py" \
 "$CTL/githubintelctl" \
 "$MEM/github_intelligence_config.json" \
 "$MEM/github_intelligence_state.json" \
 "$MEM/github_intelligence_report.json" \
 "$MEM/github_intelligence_health.json" \
 "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/github_intelligence_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_repository_analysis": true,
  "automatic_health_signals": true,
  "automatic_internal_recommendations": true,
  "repository": "FREEDOMVIKING/CompanyOS",
  "automatic_repository_mutation": false,
  "automatic_issue_creation": false,
  "automatic_pull_request_creation": false,
  "automatic_publication": false,
  "automatic_spending": false
}
JSON

cat > "$AGENTS/github_intelligence_engine.py" <<'PY'
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

CFG = MEM / "github_intelligence_config.json"
STATE = MEM / "github_intelligence_state.json"
REPORT = MEM / "github_intelligence_report.json"
HEALTH = MEM / "github_intelligence_health.json"
CACHE = MEM / "github_read_cache.json"
GIT_STATUS = MEM / "github_connector_audit.json"

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

def run_git(*args: str) -> dict[str, Any]:
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
        result = {"success": False, "status": "github_intelligence_disabled"}
        print(json.dumps(result, indent=2))
        return result

    repos = load(CACHE, {}).get("repositories", [])
    repo = next(
        (r for r in repos if r.get("full_name") == cfg.get("repository")),
        None
    )

    branch = run_git("branch", "--show-current")
    status = run_git("status", "--porcelain")
    latest = run_git("log", "-1", "--pretty=%H|%cI|%s")

    working_tree_clean = bool(status.get("success")) and not status.get("stdout")
    branch_name = branch.get("stdout") if branch.get("success") else None

    commit_hash = None
    commit_time = None
    commit_subject = None
    if latest.get("success") and latest.get("stdout"):
        parts = latest["stdout"].split("|", 2)
        if len(parts) == 3:
            commit_hash, commit_time, commit_subject = parts

    signals = []
    recommendations = []

    if branch_name != "main":
        signals.append("not_on_main_branch")
        recommendations.append("Review the active Git branch before production changes.")

    if not working_tree_clean:
        signals.append("uncommitted_changes")
        recommendations.append("Review and either commit or restore uncommitted changes.")

    if repo is None:
        signals.append("repository_cache_missing")
        recommendations.append("Refresh the GitHub read connector repository cache.")
    else:
        if repo.get("default_branch") != "main":
            signals.append("default_branch_not_main")

    if not signals:
        signals.append("repository_operating_normally")
        recommendations.append("Repository state looks healthy; continue normal autonomous monitoring.")

    report = {
        "generated_at": now(),
        "repository": cfg.get("repository"),
        "live_repository_data": repo,
        "local_git": {
            "branch": branch_name,
            "working_tree_clean": working_tree_clean,
            "latest_commit_hash": commit_hash,
            "latest_commit_time": commit_time,
            "latest_commit_subject": commit_subject
        },
        "signals": signals,
        "recommendations": recommendations,
        "automatic_repository_mutation": False,
        "automatic_issue_creation": False,
        "automatic_pull_request_creation": False
    }

    save(REPORT, report)
    save(STATE, {
        "generated_at": now(),
        "signal_count": len(signals),
        "working_tree_clean": working_tree_clean,
        "branch": branch_name
    })
    save(HEALTH, {
        "healthy": True,
        "last_analyzed_at": now(),
        "signal_count": len(signals),
        "working_tree_clean": working_tree_clean
    })

    return {
        "success": True,
        "status": "github_intelligence_analysis_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "github_intelligence_status",
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

chmod +x "$AGENTS/github_intelligence_engine.py"

cat > "$CTL/githubintelctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "github_intelligence_engine.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/githubintelctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/github_intelligence_engine.py" "$CTL/githubintelctl"

echo "[2/6] Refreshing GitHub repository cache..."
python "$CTL/githubreadctl" repos 20 || true

echo "[3/6] Running GitHub intelligence analysis..."
python "$CTL/githubintelctl" analyze

echo "[4/6] Adding intelligence job to scheduler..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "github-intelligence",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/githubintelctl", "analyze"]
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

echo "[5/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
python "$CTL/githubintelctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

r = Path.home()/"companyos"
errors = []

req = [
    r/"agents"/"github_intelligence_engine.py",
    r/"companyos"/"githubintelctl",
    r/"ceo_memory"/"github_intelligence_config.json",
    r/"ceo_memory"/"github_intelligence_state.json",
    r/"ceo_memory"/"github_intelligence_report.json",
    r/"ceo_memory"/"github_intelligence_health.json",
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
        "automatic_publication",
        "automatic_spending"
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    report = json.loads(req[4].read_text())
    if "local_git" not in report:
        errors.append("GitHub intelligence report missing local_git")

    sched = json.loads(req[6].read_text())
    job = next(
        (x for x in sched.get("jobs", [])
         if x.get("id") == "github-intelligence"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("GitHub intelligence scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 19 Step 7 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 19 STEP 7 INSTALLED"
echo " GITHUB INTELLIGENCE LOOP ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/githubintelctl analyze"
echo "  python companyos/githubintelctl status"
echo
echo "Autonomous schedule:"
echo "  GitHub intelligence refreshes every 30 minutes"
