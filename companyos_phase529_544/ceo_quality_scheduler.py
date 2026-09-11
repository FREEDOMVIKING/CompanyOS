from .autonomous_quality_cycle import AutonomousQualityCycle
from .scheduler_quality_hook import SchedulerQualityHook

class CEOQualityScheduler:
    """542: run quality brain and feed only approved next-step missions to scheduler."""

    def __init__(self, root):
        self.cycle = AutonomousQualityCycle(root)
        self.hook = SchedulerQualityHook(root)

    def run(self):
        result = self.cycle.run()
        injected = self.hook.inject(result["generated_missions"])
        return {
            **result,
            "scheduler_injection":injected,
            "status":"quality_aware_scheduler_updated",
        }
