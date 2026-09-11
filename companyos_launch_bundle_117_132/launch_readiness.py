from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LaunchReadinessReport:
    ready: bool
    score: int
    checks: dict[str,bool]
    reason: str

class LaunchReadinessEvaluator:
    def evaluate(self, *, project_stage, blockers, artifacts_count):
        checks={
            "stage_launch_ready": project_stage in ("LAUNCH_READY","COMPLETED"),
            "no_blockers": len(blockers)==0,
            "artifacts_present": artifacts_count > 0,
        }
        score=sum(1 for v in checks.values() if v)
        ready=all(checks.values())
        return LaunchReadinessReport(
            ready=ready,
            score=score,
            checks=checks,
            reason="launch_ready" if ready else "launch_requirements_incomplete",
        )
