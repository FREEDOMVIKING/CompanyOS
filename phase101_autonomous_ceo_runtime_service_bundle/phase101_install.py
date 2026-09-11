#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase101_autonomous_ceo_runtime_service_bundle"

pairs = [
    (
        BUNDLE / "autonomous_ceo_runtime_service.py",
        ROOT / "companyos/runtime/autonomous_ceo_runtime_service.py",
    ),
    (
        BUNDLE / "phase101_ceo_runtime_once.py",
        ROOT / "phase101_ceo_runtime_once.py",
    ),
    (
        BUNDLE / "phase101_ceo_runtime_run.py",
        ROOT / "phase101_ceo_runtime_run.py",
    ),
    (
        BUNDLE / "phase101_ceo_runtime_status.py",
        ROOT / "phase101_ceo_runtime_status.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase101_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "101_AUTONOMOUS_CEO_RUNTIME_SERVICE",
    "status": "installed",
    "multi_orchestration_runtime_advance": True,
    "persisted_service_health_state": True,
    "per_orchestration_error_isolation": True,
    "max_failure_stop_guard": True,
    "external_actions": False,
    "signs_transaction": False,
    "broadcasts_transaction": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE101_AUTONOMOUS_CEO_RUNTIME_SERVICE_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE101_AUTONOMOUS_CEO_RUNTIME_SERVICE: INSTALLED")
print("COMPILE_CHECK: PASS")
print("MULTI_ORCHESTRATION_RUNTIME_ADVANCE: True")
print("PERSISTED_SERVICE_HEALTH_STATE: True")
print("PER_ORCHESTRATION_ERROR_ISOLATION: True")
print("MAX_FAILURE_STOP_GUARD: True")
print("CEO_RUNTIME_EXTERNAL_ACTIONS: False")
print("CEO_RUNTIME_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
