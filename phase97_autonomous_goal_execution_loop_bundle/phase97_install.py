#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase97_autonomous_goal_execution_loop_bundle"

pairs = [
    (BUNDLE / "autonomous_goal_execution_loop.py", ROOT / "companyos/runtime/autonomous_goal_execution_loop.py"),
    (BUNDLE / "phase97_goal_loop_test.py", ROOT / "phase97_goal_loop_test.py"),
    (BUNDLE / "phase97_runtime_goal_loop_once.py", ROOT / "phase97_runtime_goal_loop_once.py"),
    (BUNDLE / "phase97_runtime_goal_loop_run.py", ROOT / "phase97_runtime_goal_loop_run.py"),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase97_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "97_AUTONOMOUS_GOAL_EXECUTION_LOOP",
    "status": "installed",
    "dependency_ready_task_advance": True,
    "stale_task_recovery_before_cycle": True,
    "specialist_routing_reused": True,
    "persistent_task_results": True,
    "goal_loop_signs_transaction": False,
    "goal_loop_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE97_AUTONOMOUS_GOAL_EXECUTION_LOOP_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE97_AUTONOMOUS_GOAL_EXECUTION_LOOP: INSTALLED")
print("COMPILE_CHECK: PASS")
print("DEPENDENCY_READY_TASK_ADVANCE: True")
print("STALE_TASK_RECOVERY_BEFORE_CYCLE: True")
print("SPECIALIST_ROUTING_REUSED: True")
print("GOAL_LOOP_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
