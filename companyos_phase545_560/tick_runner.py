from .quality_tick import QualityTick
from .scheduler_tick import SchedulerTick

class TickRunner:
    """549: coordinate quality and scheduler ticks."""

    def __init__(self, root, quality_every=3):
        self.quality = QualityTick(root)
        self.scheduler = SchedulerTick(root)
        self.quality_every = max(1, int(quality_every))

    def run(self, tick_number):
        quality_result = None
        if tick_number % self.quality_every == 0:
            quality_result = self.quality.run()

        scheduler_result = self.scheduler.run()

        return {
            "success": bool(scheduler_result.get("success")),
            "status": "ceo_service_tick_complete",
            "tick_number": tick_number,
            "quality_result": quality_result,
            "scheduler_result": scheduler_result,
        }
