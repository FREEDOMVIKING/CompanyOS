from __future__ import annotations
import os

class AdaptiveScheduler:
    """288: choose delay between persistent improvement cycles."""

    def next_delay(self, last_success=True):
        base = max(30, int(os.getenv("COMPANYOS_PERSISTENT_BASE_DELAY_SECONDS", "600")))
        if last_success:
            return base
        return min(base * 3, 7200)
