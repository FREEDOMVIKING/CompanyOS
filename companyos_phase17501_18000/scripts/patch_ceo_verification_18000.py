#!/usr/bin/env python3
from pathlib import Path

p = Path.home() / "companyos/companyos/ceointelligence/verification_engine.py"
if not p.exists():
    print("CEO_VERIFICATION_PATCH_SKIPPED:not_found")
    raise SystemExit(0)

s = p.read_text()
p.with_suffix(".py.phase18000.bak").write_text(s)

new = '''
class VerificationEngine:
    def verify_execution(self, job, result):
        try:
            from companyos.failureops import VerificationPolicy
            return VerificationPolicy().verify(job, result)
        except Exception:
            checks = {
                "job_present": bool(job),
                "result_present": bool(result),
                "execution_success": bool((result or {}).get("success", False)),
            }
            return {
                "passed": all(checks.values()),
                "checks": checks,
                "job_id": (job or {}).get("job_id")
            }

    def summarize_cycle(self, results):
        passed = sum(1 for r in results if r.get("verification", {}).get("passed"))
        failed = len(results) - passed
        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "cycle_verified": failed == 0 and len(results) > 0
        }
'''
p.write_text(new.lstrip())
print("CEO_VERIFICATION_PHASE18000_PATCHED")
