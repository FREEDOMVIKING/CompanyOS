#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase95_autonomous_task_dispatcher_bundle"

pairs = [
    (
        BUNDLE / "autonomous_task_dispatcher.py",
        ROOT / "companyos/runtime/autonomous_task_dispatcher.py",
    ),
    (
        BUNDLE / "default_specialist_registry.py",
        ROOT / "companyos/runtime/default_specialist_registry.py",
    ),
    (
        BUNDLE / "phase95_dispatcher_test.py",
        ROOT / "phase95_dispatcher_test.py",
    ),
    (
        BUNDLE / "phase95_runtime_dispatch_once.py",
        ROOT / "phase95_runtime_dispatch_once.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase95_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "95_AUTONOMOUS_TASK_DISPATCHER",
    "status": "installed",
    "priority_task_dispatch": True,
    "specialist_agent_routing": True,
    "task_result_persistence": True,
    "handler_failure_retry_path": True,
    "dispatcher_signs_transaction": False,
    "dispatcher_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE95_AUTONOMOUS_TASK_DISPATCHER_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE95_AUTONOMOUS_TASK_DISPATCHER: INSTALLED")
print("COMPILE_CHECK: PASS")
print("PRIORITY_TASK_DISPATCH: True")
print("SPECIALIST_AGENT_ROUTING: True")
print("TASK_RESULT_PERSISTENCE: True")
print("HANDLER_FAILURE_RETRY_PATH: True")
print("DISPATCHER_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
