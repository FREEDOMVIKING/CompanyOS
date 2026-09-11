#!/usr/bin/env python3
from pathlib import Path

p = Path.home() / "companyos/companyos/ceointelligence/ceo_orchestrator.py"
if not p.exists():
    raise SystemExit(f"ERROR: missing {p}")

s = p.read_text()
p.with_suffix(".py.phase21000.bak").write_text(s)

needle = '''        summary = verifier.summarize_cycle(rows)
        output = {
            "success": True,
            "status": "ceo_execution_cycle_complete",
            "executions": rows,
            "verification_summary": summary,
        }
'''

replacement = '''        summary = verifier.summarize_cycle(rows)

        recovery = None
        if not summary.get("cycle_verified"):
            try:
                from companyos.workerops.execution_bridge import ExecutionBridge
                from companyos.recoveryops import AutonomousRecoveryCycle

                recovery_engine = AutonomousRecoveryCycle(
                    self.root,
                    ExecutionBridge(self.root),
                    verifier
                )
                recovery = recovery_engine.recover_unresolved(rows)
                rows = recovery["rows"]
                summary = verifier.summarize_cycle(rows)
            except Exception as recovery_error:
                recovery = {
                    "recovered_count": 0,
                    "error": type(recovery_error).__name__,
                    "message": str(recovery_error)
                }

        output = {
            "success": True,
            "status": "ceo_execution_cycle_complete",
            "executions": rows,
            "verification_summary": summary,
            "recovery": recovery,
        }
'''

if needle not in s:
    print("CEO_RECOVERY_PATCH_TARGET_NOT_FOUND")
    raise SystemExit(1)

p.write_text(s.replace(needle, replacement, 1))
print("CEO_AUTONOMOUS_RECOVERY_PHASE21000_PATCHED")
