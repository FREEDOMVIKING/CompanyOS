#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase98_goal_lifecycle_manager_bundle"

pairs = [
    (BUNDLE / "goal_lifecycle_manager.py", ROOT / "companyos/runtime/goal_lifecycle_manager.py"),
    (BUNDLE / "phase98_goal_lifecycle_test.py", ROOT / "phase98_goal_lifecycle_test.py"),
    (BUNDLE / "phase98_runtime_goal_status.py", ROOT / "phase98_runtime_goal_status.py"),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase98_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "98_GOAL_LIFECYCLE_MANAGER",
    "status": "installed",
    "ceo_goal_lifecycle_tracking": True,
    "task_output_aggregation": True,
    "blocked_goal_detection": True,
    "completed_failed_terminal_states": True,
    "goal_lifecycle_signs_transaction": False,
    "goal_lifecycle_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE98_GOAL_LIFECYCLE_MANAGER_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE98_GOAL_LIFECYCLE_MANAGER: INSTALLED")
print("COMPILE_CHECK: PASS")
print("CEO_GOAL_LIFECYCLE_TRACKING: True")
print("TASK_OUTPUT_AGGREGATION: True")
print("BLOCKED_GOAL_DETECTION: True")
print("COMPLETED_FAILED_TERMINAL_STATES: True")
print("GOAL_LIFECYCLE_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
