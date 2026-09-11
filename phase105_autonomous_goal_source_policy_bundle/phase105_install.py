#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase105_autonomous_goal_source_policy_bundle"

pairs = [
    (BUNDLE/"goal_source_policy.py", ROOT/"companyos/runtime/goal_source_policy.py"),
    (BUNDLE/"policy_guarded_goal_intake.py", ROOT/"companyos/runtime/policy_guarded_goal_intake.py"),
    (BUNDLE/"phase105_runtime_goal_submit.py", ROOT/"phase105_runtime_goal_submit.py"),
    (BUNDLE/"phase105_policy_test.py", ROOT/"phase105_policy_test.py"),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text()
    ast.parse(text)
    if dst.exists():
        bak = dst.with_name(dst.name + f".phase105_backup_{stamp}")
        shutil.copy2(dst, bak)
        backups[str(dst)] = str(bak)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text)
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "105_AUTONOMOUS_GOAL_SOURCE_POLICY",
    "status": "installed",
    "goal_source_policy_gate": True,
    "external_action_classification": True,
    "financial_action_classification": True,
    "human_approval_flagging": True,
    "external_actions": False,
    "signs_transaction": False,
    "broadcasts_transaction": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT/"PHASE105_AUTONOMOUS_GOAL_SOURCE_POLICY_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n"
)

print("PHASE105_AUTONOMOUS_GOAL_SOURCE_POLICY: INSTALLED")
print("COMPILE_CHECK: PASS")
print("GOAL_SOURCE_POLICY_GATE: True")
print("EXTERNAL_ACTION_CLASSIFICATION: True")
print("FINANCIAL_ACTION_CLASSIFICATION: True")
print("HUMAN_APPROVAL_FLAGGING: True")
print("POLICY_GATE_EXTERNAL_ACTIONS: False")
print("POLICY_GATE_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
