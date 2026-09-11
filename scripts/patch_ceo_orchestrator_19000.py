#!/usr/bin/env python3
from pathlib import Path

p = Path.home() / "companyos/companyos/ceointelligence/ceo_orchestrator.py"
if not p.exists():
    print("CEO_ORCHESTRATOR_PATCH_SKIPPED:not_found")
    raise SystemExit(0)

s = p.read_text()
backup = p.with_suffix(".py.phase19000.bak")
backup.write_text(s)

needle = "verification = verifier.verify_execution(before, result.get(\"result\", result))"
if needle in s:
    repl = '''raw_result = result.get("result", result)
            try:
                from companyos.cycleops import ApprovalDeferment
                raw_result = ApprovalDeferment().normalize(before, raw_result)
            except Exception:
                pass
            verification = verifier.verify_execution(before, raw_result)'''
    s = s.replace(needle, repl, 1)
    p.write_text(s)
    print("CEO_ORCHESTRATOR_PHASE19000_PATCHED")
else:
    print("CEO_ORCHESTRATOR_PATCH_TARGET_NOT_FOUND")
