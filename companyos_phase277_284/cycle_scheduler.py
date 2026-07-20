from __future__ import annotations
import time

class CycleScheduler:
    """281: cooldown-aware sequential scheduling."""

    def wait(self, seconds):
        seconds = max(0, int(seconds))
        if seconds:
            time.sleep(seconds)
        return {"waited_seconds": seconds}
