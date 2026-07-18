#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
RUNTIME="$ROOT/runtime"
BACKUP="$ROOT/backups/phase20_step1_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$CTL" "$MEM" "$RUNTIME" "$BACKUP"

echo "============================================================"
echo " Phase 20 Step 1 - Runtime State Isolation & Git Hygiene"
echo "============================================================"

for f in \
  ".gitignore" \
  "$CTL/runtimehygienectl" \
  "$MEM/runtime_hygiene_config.json" \
  "$MEM/runtime_hygiene_state.json" \
  "$MEM/runtime_hygiene_health.json" \
  "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/runtime_hygiene_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_runtime_state_isolation": true,
  "automatic_gitignore_management": true,
  "automatic_runtime_cleanup": true,
  "automatic_source_file_deletion": false,
  "automatic_git_reset": false,
  "automatic_git_clean": false,
  "automatic_commit": false,
  "automatic_push": false
}
JSON

touch .gitignore

python - <<'PY'
from pathlib import Path

root = Path.home() / "companyos"
path = root / ".gitignore"

required = [
    "",
    "# CompanyOS runtime-generated state",
    "runtime/",
    "logs/",
    "run/",
    "backups/state_snapshots/",
    "ceo_memory/*_state.json",
    "ceo_memory/*_health.json",
    "ceo_memory/*_report.json",
    "ceo_memory/*_audit.json",
    "ceo_memory/*_cache.json",
    "ceo_memory/*_brief.json",
    "ceo_memory/*_queue.json",
    "ceo_memory/*_history.json",
    "ceo_memory/HALT_AUTONOMY",
    "",
    "# Python runtime",
    "__pycache__/",
    "*.pyc",
]

existing = path.read_text(encoding="utf-8").splitlines()
for line in required:
    if line not in existing:
        existing.append(line)

path.write_text("\n".join(existing).rstrip() + "\n", encoding="utf-8")
print("gitignore_updated")
PY

cat > "$CTL/runtimehygienectl" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"
RUNTIME = ROOT / "runtime"

CFG = MEM / "runtime_hygiene_config.json"
STATE = MEM / "runtime_hygiene_state.json"
HEALTH = MEM / "runtime_hygiene_health.json"

RUNTIME_SUFFIXES = (
    "_state.json",
    "_health.json",
    "_report.json",
    "_audit.json",
    "_cache.json",
    "_brief.json",
    "_queue.json",
    "_history.json",
)

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
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )
    return {
        "success": proc.returncode == 0,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }

def is_runtime_file(path: Path) -> bool:
    name = path.name
    return any(name.endswith(suffix) for suffix in RUNTIME_SUFFIXES) or name == "HALT_AUTONOMY"

def isolate() -> dict[str, Any]:
    cfg = load(CFG, {})
    RUNTIME.mkdir(parents=True, exist_ok=True)

    copied = []
    skipped = []

    for path in MEM.iterdir():
        if not path.is_file() or not is_runtime_file(path):
            continue

        dest = RUNTIME / path.name
        try:
            shutil.copy2(path, dest)
            copied.append(path.name)
        except Exception as exc:
            skipped.append({"file": path.name, "error": str(exc)})

    status = git("status", "--porcelain")
    lines = status.get("stdout", "").splitlines() if status.get("success") else []

    runtime_only = []
    source_changes = []

    for line in lines:
        file_part = line[3:] if len(line) > 3 else ""
        normalized = file_part.replace("\\", "/")
        if (
            normalized.startswith("ceo_memory/")
            and is_runtime_file(Path(normalized))
        ) or normalized.startswith(("logs/", "run/", "runtime/", "backups/state_snapshots/")):
            runtime_only.append(line)
        else:
            source_changes.append(line)

    state = {
        "generated_at": now(),
        "runtime_files_copied": copied,
        "runtime_copy_errors": skipped,
        "git_change_count": len(lines),
        "runtime_only_change_count": len(runtime_only),
        "source_change_count": len(source_changes),
        "runtime_only_changes": runtime_only,
        "source_changes": source_changes,
        "working_tree_effectively_clean": len(source_changes) == 0,
    }
    save(STATE, state)
    save(
        HEALTH,
        {
            "healthy": True,
            "last_checked_at": now(),
            "working_tree_effectively_clean": len(source_changes) == 0,
            "source_change_count": len(source_changes),
            "runtime_only_change_count": len(runtime_only),
        },
    )
    return {"success": True, "status": "runtime_hygiene_complete", "state": state}

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "runtime_hygiene_status",
        "config": load(CFG, {}),
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "isolate":
        result = isolate()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["isolate", "status"],
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$CTL/runtimehygienectl"

echo "[1/6] Compiling..."
python -m py_compile "$CTL/runtimehygienectl"

echo "[2/6] Isolating runtime state..."
python "$CTL/runtimehygienectl" isolate

echo "[3/6] Adding runtime hygiene job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "runtime-hygiene",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/runtimehygienectl", "isolate"]
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

echo "[5/6] Checking effective Git cleanliness..."
python "$CTL/runtimehygienectl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / ".gitignore",
    root / "companyos" / "runtimehygienectl",
    root / "ceo_memory" / "runtime_hygiene_config.json",
    root / "ceo_memory" / "runtime_hygiene_state.json",
    root / "ceo_memory" / "runtime_hygiene_health.json",
    root / "ceo_memory" / "autonomous_operations_config.json",
]

for path in required:
    if not path.exists() or path.stat().st_size <= 0:
        errors.append(f"Missing/empty: {path}")

try:
    py_compile.compile(str(required[1]), doraise=True)
except Exception as exc:
    errors.append(f"Compile error: {exc}")

try:
    cfg = json.loads(required[2].read_text())
    for key in [
        "automatic_source_file_deletion",
        "automatic_git_reset",
        "automatic_git_clean",
        "automatic_commit",
        "automatic_push",
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    sched = json.loads(required[5].read_text())
    job = next(
        (x for x in sched.get("jobs", []) if x.get("id") == "runtime-hygiene"),
        None,
    )
    if not job or job.get("enabled") is not True:
        errors.append("Runtime hygiene scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 1 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 1 INSTALLED"
echo " RUNTIME STATE ISOLATION & GIT HYGIENE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/runtimehygienectl isolate"
echo "  python companyos/runtimehygienectl status"
