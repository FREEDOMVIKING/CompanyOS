from __future__ import annotations

class SourceBackoff:
    """360: bounded retry decisions for public-source failures."""

    def next_delay(self, failures):
        failures = max(0, int(failures))
        return min(3600, 30 * (2 ** min(failures, 6)))
