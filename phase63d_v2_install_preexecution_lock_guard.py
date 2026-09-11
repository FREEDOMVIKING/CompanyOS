#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import py_compile, shutil, sys

TARGET = Path.home() / "companyos/companyos/liveintegration/live_orchestrator.py"
if not TARGET.exists(): raise SystemExit(f"TARGET_NOT_FOUND: {TARGET}")
original = TARGET.read_text(encoding="utf-8")
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = TARGET.with_name(f"{TARGET.name}.phase63d_v2_backup_{stamp}")
shutil.copy2(TARGET, backup)
marker = "        readiness=self.readiness.evaluate()"
guard_lines = [
    "        # Phase 63D V2: fail closed on pre-existing post-execution lock.",
    "        postlock_state = self.postlock.status()",
    '        if postlock_state.get("locked") is True:',
    "            return {",
    '                "success": False,',
    '                "status": "post_execution_lock_active",',
    '                "post_execution_lock": postlock_state,',
    '                "authorization_consumed": False,',
    "            }",
    "",
]
guard = "\n".join(guard_lines) + "\n"
if '"status": "post_execution_lock_active"' not in original:
    pos = original.find(marker)
    if pos < 0: raise SystemExit(f"PATCH_NOT_APPLIED: readiness marker not found. BACKUP={backup}")
    method_pos = original.rfind("    def execute_once(", 0, pos)
    if method_pos < 0: raise SystemExit(f"PATCH_NOT_APPLIED: execute_once not found. BACKUP={backup}")
    next_method = original.find("\n    def ", method_pos + 1)
    if next_method >= 0 and next_method < pos: raise SystemExit(f"PATCH_NOT_APPLIED: unsafe marker location. BACKUP={backup}")
    TARGET.write_text(original[:pos] + guard + original[pos:], encoding="utf-8")
try:
    py_compile.compile(str(TARGET), doraise=True)
except Exception:
    shutil.copy2(backup, TARGET)
    print("COMPILE_FAILED: original restored automatically.")
    raise
updated = TARGET.read_text(encoding="utf-8")
method_pos = updated.find("    def execute_once(")
guard_pos = updated.find('"status": "post_execution_lock_active"', method_pos)
ready_pos = updated.find(marker, method_pos)
if min(method_pos, guard_pos, ready_pos) < 0 or guard_pos > ready_pos:
    shutil.copy2(backup, TARGET)
    raise SystemExit("VERIFY_FAILED: guard placement invalid; original restored.")
print("==============================================")
print("PHASE63D_V2_PREEXECUTION_LOCK_GUARD: INSTALLED")
print("==============================================")
print("TARGET:", TARGET)
print("BACKUP:", backup)
print("COMPILE_CHECK: PASS")
print("GUARD_BEFORE_READINESS: True")
print("FAIL_CLOSED_STATUS: post_execution_lock_active")
print("NO_TRANSACTION_CREATED_BY_INSTALLER: True")
print("NO_SIGNING_PERFORMED_BY_INSTALLER: True")
print("NO_BROADCAST_PERFORMED_BY_INSTALLER: True")
