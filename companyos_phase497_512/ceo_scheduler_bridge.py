from .ceo_scheduler import AutonomousCEOScheduler

class CEOSchedulerBridge:
    """511: thin bridge for running scheduler ticks from scripts/services."""

    def __init__(self, root):
        self.scheduler = AutonomousCEOScheduler(root)

    def run_tick(self, context=None):
        return self.scheduler.tick(context=context)
