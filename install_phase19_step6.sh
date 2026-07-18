#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase19_step6_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 19 Step 6 - Live GitHub Read Connector"
echo "============================================================"

for f in \
 "$AGENTS/github_read_connector.py" \
 "$CTL/githubreadctl" \
 "$MEM/github_read_config.json" \
 "$MEM/github_read_state.json" \
 "$MEM/github_read_health.json" \
 "$MEM/github_read_cache.json" \
 "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/github_read_config.json" <<'JSON'
{
  "enabled": true,
  "read_only": true,
  "token_environment_variable": "GITHUB_TOKEN",
  "api_base": "https://api.github.com",
  "timeout_seconds": 20,
  "automatic_write": false,
  "automatic_repository_mutation": false,
  "automatic_issue_creation": false,
  "automatic_pull_request_creation": false,
  "credential_export": false
}
JSON

cat > "$AGENTS/github_read_connector.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "github_read_config.json"
STATE = MEM / "github_read_state.json"
HEALTH = MEM / "github_read_health.json"
CACHE = MEM / "github_read_cache.json"

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

def request_json(endpoint: str) -> tuple[int, Any]:
    cfg = load(CFG, {})
    token_name = cfg.get("token_environment_variable", "GITHUB_TOKEN")
    token = os.getenv(token_name)
    if not token:
        raise RuntimeError(f"{token_name} is not set")

    url = cfg.get("api_base", "https://api.github.com").rstrip("/") + endpoint
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "CompanyOS-ReadConnector"
        },
        method="GET"
    )

    with urllib.request.urlopen(
        req,
        timeout=int(cfg.get("timeout_seconds", 20))
    ) as response:
        return response.status, json.loads(response.read().decode("utf-8"))

def probe() -> dict[str, Any]:
    try:
        code, user = request_json("/user")
        result = {
            "success": code == 200,
            "status": "github_read_connector_ready",
            "authenticated_login": user.get("login"),
            "credential_value_recorded": False
        }
        save(STATE, {
            "generated_at": now(),
            "authenticated_login": user.get("login"),
            "last_probe_status": code
        })
        save(HEALTH, {
            "healthy": code == 200,
            "last_checked_at": now(),
            "http_status": code,
            "credential_value_recorded": False
        })
        return result
    except Exception as exc:
        save(HEALTH, {
            "healthy": False,
            "last_checked_at": now(),
            "error": str(exc),
            "credential_value_recorded": False
        })
        return {
            "success": False,
            "status": "github_read_connector_not_ready",
            "error": str(exc)
        }

def repos(limit: int = 20) -> dict[str, Any]:
    code, data = request_json(
        f"/user/repos?per_page={max(1, min(limit, 100))}&sort=updated"
    )
    rows = [{
        "name": x.get("name"),
        "full_name": x.get("full_name"),
        "private": x.get("private"),
        "updated_at": x.get("updated_at"),
        "default_branch": x.get("default_branch")
    } for x in data]

    result = {
        "success": code == 200,
        "status": "github_repositories_read",
        "count": len(rows),
        "repositories": rows
    }
    save(CACHE, {"generated_at": now(), "repositories": rows})
    return result

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "github_read_status",
        "config": load(CFG, {}),
        "state": load(STATE, {}),
        "health": load(HEALTH, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "probe":
            result = probe()
        elif action == "repos":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            result = repos(limit)
        elif action == "status":
            result = status()
        else:
            result = {
                "success": False,
                "status": "unknown_action",
                "allowed": ["probe", "repos [limit]", "status"]
            }
    except Exception as exc:
        result = {
            "success": False,
            "status": "github_read_error",
            "error": str(exc)
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/github_read_connector.py"

cat > "$CTL/githubreadctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "github_read_connector.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/githubreadctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/github_read_connector.py" "$CTL/githubreadctl"

echo "[2/5] Initializing connector state..."
python "$CTL/githubreadctl" status

echo "[3/5] Adding health probe job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

j = {
    "id": "github-read-connector",
    "enabled": True,
    "interval_seconds": 3600,
    "command": ["python", "companyos/githubreadctl", "probe"]
}

e = next((x for x in jobs if x.get("id") == j["id"]), None)
if e:
    e.clear()
    e.update(j)
else:
    jobs.append(j)

p.write_text(json.dumps(d, indent=2))
print(json.dumps({"success": True, "job_id": j["id"]}, indent=2))
PY

echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart

echo "[5/5] Verifying installation..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

r = Path.home()/"companyos"
errors = []

req = [
    r/"agents"/"github_read_connector.py",
    r/"companyos"/"githubreadctl",
    r/"ceo_memory"/"github_read_config.json",
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
        "automatic_write",
        "automatic_repository_mutation",
        "automatic_issue_creation",
        "automatic_pull_request_creation",
        "credential_export"
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    sched = json.loads(req[3].read_text())
    job = next(
        (x for x in sched.get("jobs", [])
         if x.get("id") == "github-read-connector"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("GitHub read connector scheduler job missing/disabled")
except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 19 Step 6 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for error in errors:
    print("ERROR:", error)
if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 19 STEP 6 INSTALLED"
echo " LIVE GITHUB READ CONNECTOR INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "To activate the live connection:"
echo "  export GITHUB_TOKEN='YOUR_TOKEN'"
echo "  python companyos/githubreadctl probe"
echo "  python companyos/githubreadctl repos 20"
