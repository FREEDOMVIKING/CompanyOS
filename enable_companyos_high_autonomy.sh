#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
MEMORY="$ROOT/ceo_memory"
CTL="$ROOT/companyos"
BACKUP="$ROOT/backups/high_autonomy_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$MEMORY" "$CTL" "$BACKUP"

echo "============================================================"
echo " CompanyOS High-Autonomy Controlled Mode"
echo "============================================================"

for file in \
  "$MEMORY/access_control.json" \
  "$MEMORY/high_autonomy_policy.json" \
  "$MEMORY/high_autonomy_health.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/high_autonomy_policy.json" <<'JSON'
{
  "mode": "high_autonomy_controlled",
  "enabled": true,

  "local_file_read": true,
  "local_file_write": true,
  "local_code_generation": true,
  "local_code_modification": true,
  "local_command_execution": true,
  "local_task_execution": true,
  "local_scheduling": true,
  "local_backup_creation": true,
  "local_recovery": true,

  "internal_analysis": true,
  "internal_decision_preparation": true,
  "internal_plan_generation": true,
  "internal_report_generation": true,
  "internal_memory_updates": true,

  "github_read": true,
  "github_stage": true,
  "github_commit": true,
  "github_push": true,

  "external_api_read": true,
  "external_api_write": true,

  "customer_contact": false,
  "public_posting": false,
  "financial_transactions": false,
  "credential_export": false,
  "private_key_export": false,
  "secret_logging": false,
  "destructive_delete": false,

  "limits": {
    "max_external_writes_per_hour": 10,
    "max_local_commands_per_run": 50,
    "max_files_modified_per_run": 25,
    "max_git_pushes_per_hour": 3,
    "require_backup_before_code_change": true,
    "require_tests_before_git_push": true,
    "require_clean_secret_scan_before_git_push": true
  },

  "kill_switch_file": "ceo_memory/HALT_AUTONOMY",
  "owner_approval_required_for_customer_contact": true,
  "owner_approval_required_for_publication": true,
  "owner_approval_required_for_financial_actions": true
}
JSON

cat > "$CTL/autonomyctl" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path.home() / "companyos"
memory = root / "ceo_memory"
policy_path = memory / "high_autonomy_policy.json"
health_path = memory / "high_autonomy_health.json"
kill_switch = memory / "HALT_AUTONOMY"


def load():
    return json.loads(policy_path.read_text(encoding="utf-8"))


def save_health(data):
    health_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


action = sys.argv[1] if len(sys.argv) > 1 else "status"
policy = load()

if action == "status":
    halted = kill_switch.exists()
    result = {
        "success": True,
        "mode": policy.get("mode"),
        "enabled": policy.get("enabled", False) and not halted,
        "halted": halted,
        "policy": policy,
    }
    save_health(result)
    print(json.dumps(result, indent=2))
    raise SystemExit(0)

if action == "halt":
    kill_switch.write_text("AUTONOMY HALTED\n", encoding="utf-8")
    result = {
        "success": True,
        "status": "autonomy_halted",
    }
    save_health(result)
    print(json.dumps(result, indent=2))
    raise SystemExit(0)

if action == "resume":
    if kill_switch.exists():
        kill_switch.unlink()
    result = {
        "success": True,
        "status": "autonomy_resumed",
    }
    save_health(result)
    print(json.dumps(result, indent=2))
    raise SystemExit(0)

print(json.dumps({
    "success": False,
    "error": "Unknown action",
    "allowed": ["status", "halt", "resume"]
}, indent=2))
raise SystemExit(1)
PY

chmod +x "$CTL/autonomyctl"

cat > "$MEMORY/high_autonomy_health.json" <<'JSON'
{
  "healthy": true,
  "mode": "high_autonomy_controlled",
  "halted": false
}
JSON

echo "[1/3] Compiling..."
python -m py_compile "$CTL/autonomyctl"

echo "[2/3] Verifying policy..."
python - <<'PY'
import json
from pathlib import Path

root = Path.home() / "companyos"
policy = json.loads(
    (root / "ceo_memory" / "high_autonomy_policy.json")
    .read_text(encoding="utf-8")
)

errors = []

required_true = [
    "local_file_read",
    "local_file_write",
    "local_code_generation",
    "local_code_modification",
    "local_command_execution",
    "local_task_execution",
    "local_scheduling",
    "github_push",
    "external_api_read",
    "external_api_write",
]

required_false = [
    "financial_transactions",
    "credential_export",
    "private_key_export",
    "secret_logging",
    "destructive_delete",
]

for field in required_true:
    if policy.get(field) is not True:
        errors.append(f"{field} must be true")

for field in required_false:
    if policy.get(field) is not False:
        errors.append(f"{field} must be false")

limits = policy.get("limits", {})
for field in [
    "max_external_writes_per_hour",
    "max_local_commands_per_run",
    "max_files_modified_per_run",
    "max_git_pushes_per_hour",
]:
    if not isinstance(limits.get(field), int) or limits[field] <= 0:
        errors.append(f"Invalid limit: {field}")

print("--------------------------------------------")
print("High-Autonomy Mode verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo "[3/3] Showing status..."
python "$CTL/autonomyctl" status

echo
echo "============================================================"
echo " HIGH-AUTONOMY CONTROLLED MODE ENABLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Enabled:"
echo "  External API read/write"
echo "  Local command and task execution"
echo "  Local code modification"
echo "  GitHub push"
echo "  Scheduling, backups, and recovery"
echo
echo "Still blocked:"
echo "  Automatic spending"
echo "  Private-key or credential export"
echo "  Destructive deletion"
echo "  Secret logging"
echo "  Automatic customer contact"
echo "  Automatic public posting"
echo
echo "Kill switch:"
echo "  python companyos/autonomyctl halt"
echo "  python companyos/autonomyctl resume"
echo "  python companyos/autonomyctl status"
