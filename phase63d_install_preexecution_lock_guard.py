#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import py_compile
import shutil
import sys

TARGET = Path.home() / "companyos/companyos/liveintegration/live_orchestrator.py"

if not TARGET.exists():
    raise SystemExit(f"TARGET_NOT_FOUND: {TARGET}")

original = TARGET.read_text(encoding="utf-8")
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = TARGET.with_name(f"{TARGET.name}.phase63d_backup_{stamp}")
shutil.copy2(TARGET, backup)

needle = """    def execute_once(
        self,
        *,
        token,
        destination,
        amount,
        balance,
        estimated_fee,
        memo="controlled live execution",
    ):
        readiness=self.readiness.evaluate()
"""

replacement = """    def execute_once(
        self,
        *,
        token,
        destination,
        amount,
        balance,
        estimated_fee,
        memo="controlled live execution",
    ):
        # Fail closed before readiness, authorization, preparation, signing,
        # execution, receipt creation, or any other transaction-side effect.
        postlock_state = self.postlock.status()
        if postlock_state.get("locked") is True:
            return {
                "success": False,
                "status": "post_execution_lock_active",
                "post_execution_lock": postlock_state,
                "authorization_consumed": False,
            }

        readiness=self.readiness.evaluate()
"""

if needle not in original:
    print("PATCH_NOT_APPLIED: expected execute_once structure was not found.")
    print(f"Backup preserved at: {backup}")
    sys.exit(2)

patched = original.replace(needle, replacement, 1)
TARGET.write_text(patched, encoding="utf-8")

try:
    py_compile.compile(str(TARGET), doraise=True)
except Exception:
    shutil.copy2(backup, TARGET)
    print("COMPILE_FAILED: original file restored automatically.")
    raise

print("==============================================")
print("PHASE63D_PREEXECUTION_LOCK_GUARD: INSTALLED")
print("==============================================")
print("TARGET:", TARGET)
print("BACKUP:", backup)
print("COMPILE_CHECK: PASS")
print("LOCK_CHECK_POSITION: BEFORE_READINESS")
print("FAIL_CLOSED_STATUS: post_execution_lock_active")
print("NO_SIGNING_PERFORMED_BY_INSTALLER: True")
print("NO_BROADCAST_PERFORMED_BY_INSTALLER: True")
