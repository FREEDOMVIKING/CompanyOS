import time
from .checkpoint import RuntimeCheckpoint
from .health import RuntimeHealth

class AutonomyDaemon:
    def __init__(self, root, loop, interval_seconds=300):
        self.root = root
        self.loop = loop
        self.interval_seconds = int(interval_seconds)
        self.checkpoint = RuntimeCheckpoint(root)
        self.health = RuntimeHealth(root)

    def run_forever(self, max_jobs=25, max_cycles=None):
        cycles = 0
        while True:
            result = self.loop.run_cycle(max_jobs=max_jobs)
            cycles += 1
            self.checkpoint.save({
                "cycle": cycles,
                "result": result,
                "health": self.health.snapshot()
            })

            if max_cycles is not None and cycles >= int(max_cycles):
                return {"success": True, "cycles": cycles}

            time.sleep(max(5, self.interval_seconds))
