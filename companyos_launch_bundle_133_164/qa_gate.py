from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class QAGateReport:
    passed: bool
    score: int
    checks: dict[str,bool]
    reason: str

class QAGate:
    def evaluate(self, *, tests_passed, artifacts_present, blockers_count, critical_risks):
        checks={
            "tests_passed":bool(tests_passed),
            "artifacts_present":bool(artifacts_present),
            "no_blockers":int(blockers_count)==0,
            "no_critical_risks":int(critical_risks)==0,
        }
        score=sum(checks.values())
        passed=all(checks.values())
        return QAGateReport(passed,score,checks,"qa_pass" if passed else "qa_incomplete")
