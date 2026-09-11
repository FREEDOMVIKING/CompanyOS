from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LaunchDayGateReport:
    ready: bool
    checks: dict[str,bool]
    reason: str

class LaunchDayGate:
    def evaluate(self, *, stack_verified, qa_passed, project_launch_ready, approval_queue_clear, no_critical_blockers):
        checks={
            "stack_verified":bool(stack_verified),
            "qa_passed":bool(qa_passed),
            "project_launch_ready":bool(project_launch_ready),
            "approval_queue_clear":bool(approval_queue_clear),
            "no_critical_blockers":bool(no_critical_blockers),
        }
        ready=all(checks.values())
        return LaunchDayGateReport(ready,checks,"ready_for_controlled_launch" if ready else "launch_gate_blocked")
