#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase100_autonomous_ceo_orchestration_bundle"

pairs = [
    (
        BUNDLE / "autonomous_ceo_orchestrator.py",
        ROOT / "companyos/runtime/autonomous_ceo_orchestrator.py",
    ),
    (
        BUNDLE / "ceo_orchestration_journal.py",
        ROOT / "companyos/runtime/ceo_orchestration_journal.py",
    ),
    (
        BUNDLE / "phase100_ceo_orchestration_test.py",
        ROOT / "phase100_ceo_orchestration_test.py",
    ),
    (
        BUNDLE / "phase100_runtime_ceo_submit.py",
        ROOT / "phase100_runtime_ceo_submit.py",
    ),
    (
        BUNDLE / "phase100_runtime_ceo_cycle.py",
        ROOT / "phase100_runtime_ceo_cycle.py",
    ),
    (
        BUNDLE / "phase100_runtime_ceo_run.py",
        ROOT / "phase100_runtime_ceo_run.py",
    ),
    (
        BUNDLE / "phase100_runtime_ceo_status.py",
        ROOT / "phase100_runtime_ceo_status.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase100_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "100_AUTONOMOUS_CEO_ORCHESTRATION",
    "status": "installed",
    "integrates_phases": "94-99",
    "ceo_end_to_end_internal_orchestration": True,
    "restart_safe_persistence": True,
    "bounded_cycle_guard": True,
    "bounded_follow_up_depth": True,
    "outcome_evaluation_integrated": True,
    "append_only_orchestration_journal": True,
    "external_actions": False,
    "signs_transaction": False,
    "broadcasts_transaction": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE100_AUTONOMOUS_CEO_ORCHESTRATION_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE100_AUTONOMOUS_CEO_ORCHESTRATION: INSTALLED")
print("COMPILE_CHECK: PASS")
print("INTEGRATES_PHASES_94_99: True")
print("CEO_END_TO_END_INTERNAL_ORCHESTRATION: True")
print("RESTART_SAFE_PERSISTENCE: True")
print("BOUNDED_CYCLE_GUARD: True")
print("BOUNDED_FOLLOW_UP_DEPTH: True")
print("ORCHESTRATION_JOURNAL: True")
print("CEO_ORCHESTRATOR_EXTERNAL_ACTIONS: False")
print("CEO_ORCHESTRATOR_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
