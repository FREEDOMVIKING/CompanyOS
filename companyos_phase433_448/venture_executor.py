from .specialist_coordinator import SpecialistCoordinator
from .failure_policy import FailurePolicy
from .retry_scheduler import RetryScheduler

class VentureExecutor:
    """444: determine the next bounded execution action for a venture."""

    def next_action(self, venture):
        if venture.get("blocked_reason"):
            policy = FailurePolicy().decide(
                venture.get("failures",0),
                venture.get("retries",0),
            )
            if policy["action"] == "retry":
                return {
                    **policy,
                    "retry_after_seconds":RetryScheduler().delay_seconds(venture.get("retries",0)),
                }
            return policy

        jobs = venture.get("specialist_jobs") or []
        completed = venture.get("completed_task_ids") or []
        ready = SpecialistCoordinator().ready_jobs(jobs, completed)

        if ready:
            return {"action":"dispatch_jobs","jobs":ready[:3]}
        return {"action":"await_dependencies_or_complete","jobs":[]}
