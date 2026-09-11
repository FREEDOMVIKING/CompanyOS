#!/usr/bin/env python3
from pathlib import Path

p = Path.home() / "companyos/companyos/ceointelligence/verification_engine.py"
if not p.exists():
    raise SystemExit(f"ERROR: missing {p}")

s = p.read_text()
p.with_suffix(".py.phase19000.bak").write_text(s)

new = '''
class VerificationEngine:
    def verify_execution(self, job, result):
        from companyos.cycleops import CycleVerifier
        return CycleVerifier().verify_execution(job, result)

    def summarize_cycle(self, results):
        from companyos.cycleops import CycleVerifier
        return CycleVerifier().summarize_cycle(results)
'''
p.write_text(new.lstrip())
print("CEO_CYCLE_VERIFIER_PHASE19000_PATCHED")
