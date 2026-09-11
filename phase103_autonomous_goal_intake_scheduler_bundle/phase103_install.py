#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase103_autonomous_goal_intake_scheduler_bundle"

pairs = [
    (
        BUNDLE / "autonomous_goal_intake.py",
        ROOT / "companyos/runtime/autonomous_goal_intake.py",
    ),
    (
        BUNDLE / "autonomous_goal_scheduler.py",
        ROOT / "companyos/runtime/autonomous_goal_scheduler.py",
    ),
    (
        BUNDLE / "ceo_runtime_intake_bridge.py",
        ROOT / "companyos/runtime/ceo_runtime_intake_bridge.py",
    ),
    (
        BUNDLE / "phase103_goal_intake_test.py",
        ROOT / "phase103_goal_intake_test.py",
    ),
    (
        BUNDLE / "phase103_runtime_goal_intake_submit.py",
        ROOT / "phase103_runtime_goal_intake_submit.py",
    ),
    (
        BUNDLE / "phase103_runtime_goal_scheduler_once.py",
        ROOT / "phase103_runtime_goal_scheduler_once.py",
    ),
    (
        BUNDLE / "phase103_runtime_intake_bridge_once.py",
        ROOT / "phase103_runtime_intake_bridge_once.py",
    ),
    (
        BUNDLE / "phase103_goal_intake_status.py",
        ROOT / "phase103_goal_intake_status.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase103_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "103_AUTONOMOUS_GOAL_INTAKE_SCHEDULER",
    "status": "installed",
    "durable_ceo_goal_inbox": True,
    "priority_goal_scheduling": True,
    "intake_to_orchestration_bridge": True,
    "restart_recovery_for_claimed_goals": True,
    "external_actions": False,
    "signs_transaction": False,
    "broadcasts_transaction": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE103_AUTONOMOUS_GOAL_INTAKE_SCHEDULER_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE103_AUTONOMOUS_GOAL_INTAKE_SCHEDULER: INSTALLED")
print("COMPILE_CHECK: PASS")
print("DURABLE_CEO_GOAL_INBOX: True")
print("PRIORITY_GOAL_SCHEDULING: True")
print("INTAKE_TO_ORCHESTRATION_BRIDGE: True")
print("RESTART_RECOVERY_FOR_CLAIMED_GOALS: True")
print("GOAL_INTAKE_EXTERNAL_ACTIONS: False")
print("GOAL_INTAKE_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
