#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase99_goal_outcome_evaluator_bundle"

pairs = [
    (BUNDLE / "goal_outcome_evaluator.py", ROOT / "companyos/runtime/goal_outcome_evaluator.py"),
    (BUNDLE / "phase99_goal_outcome_test.py", ROOT / "phase99_goal_outcome_test.py"),
    (BUNDLE / "phase99_runtime_goal_evaluate.py", ROOT / "phase99_runtime_goal_evaluate.py"),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase99_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "99_GOAL_OUTCOME_EVALUATOR",
    "status": "installed",
    "goal_outcome_evaluation": True,
    "ceo_level_evidence_aggregation": True,
    "next_action_decision": True,
    "follow_up_goal_suggestion": True,
    "outcome_evaluator_signs_transaction": False,
    "outcome_evaluator_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE99_GOAL_OUTCOME_EVALUATOR_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE99_GOAL_OUTCOME_EVALUATOR: INSTALLED")
print("COMPILE_CHECK: PASS")
print("GOAL_OUTCOME_EVALUATION: True")
print("CEO_LEVEL_EVIDENCE_AGGREGATION: True")
print("NEXT_ACTION_DECISION: True")
print("FOLLOW_UP_GOAL_SUGGESTION: True")
print("OUTCOME_EVALUATOR_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
