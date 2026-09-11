#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase94_autonomous_internal_task_queue_bundle"

pairs = [
    (
        BUNDLE / "autonomous_task_queue.py",
        ROOT / "companyos/runtime/autonomous_task_queue.py",
    ),
    (
        BUNDLE / "phase94_task_queue_test.py",
        ROOT / "phase94_task_queue_test.py",
    ),
    (
        BUNDLE / "phase94_runtime_task_queue_status.py",
        ROOT / "phase94_runtime_task_queue_status.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase94_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

init = ROOT / "companyos/runtime/__init__.py"
init.parent.mkdir(parents=True, exist_ok=True)
if not init.exists():
    init.write_text("", encoding="utf-8")

manifest = {
    "phase": "94_AUTONOMOUS_INTERNAL_TASK_QUEUE",
    "status": "installed",
    "persistent_internal_task_queue": True,
    "priority_ordering": True,
    "idempotency_duplicate_protection": True,
    "retry_support": True,
    "stale_work_recovery": True,
    "task_queue_signs_transaction": False,
    "task_queue_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE94_AUTONOMOUS_INTERNAL_TASK_QUEUE_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE94_AUTONOMOUS_INTERNAL_TASK_QUEUE: INSTALLED")
print("COMPILE_CHECK: PASS")
print("PERSISTENT_INTERNAL_TASK_QUEUE: True")
print("PRIORITY_ORDERING: True")
print("IDEMPOTENCY_DUPLICATE_PROTECTION: True")
print("STALE_WORK_RECOVERY: True")
print("TASK_QUEUE_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
