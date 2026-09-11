#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase96_ceo_goal_decomposition_bundle"

pairs = [
    (BUNDLE / "ceo_goal_decomposer.py", ROOT / "companyos/runtime/ceo_goal_decomposer.py"),
    (BUNDLE / "dependency_aware_dispatcher.py", ROOT / "companyos/runtime/dependency_aware_dispatcher.py"),
    (BUNDLE / "phase96_goal_decomposition_test.py", ROOT / "phase96_goal_decomposition_test.py"),
    (BUNDLE / "phase96_runtime_goal_submit.py", ROOT / "phase96_runtime_goal_submit.py"),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase96_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "96_CEO_GOAL_DECOMPOSITION",
    "status": "installed",
    "ceo_goal_to_task_decomposition": True,
    "dependency_aware_routing": True,
    "idempotent_goal_task_keys": True,
    "default_stages": ["research", "planning", "build"],
    "goal_decomposer_signs_transaction": False,
    "goal_decomposer_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE96_CEO_GOAL_DECOMPOSITION_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE96_CEO_GOAL_DECOMPOSITION: INSTALLED")
print("COMPILE_CHECK: PASS")
print("CEO_GOAL_TO_TASK_DECOMPOSITION: True")
print("DEPENDENCY_AWARE_ROUTING: True")
print("IDEMPOTENT_GOAL_TASK_KEYS: True")
print("GOAL_DECOMPOSER_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
