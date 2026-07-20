from __future__ import annotations
import os

class CycleBudget:
    """278: configurable limits for repeated autonomous cycles."""

    def limits(self):
        return {
            "max_cycles_per_run": max(1, int(os.getenv("COMPANYOS_MAX_CYCLES_PER_RUN", "3"))),
            "cooldown_seconds": max(0, int(os.getenv("COMPANYOS_IMPROVEMENT_COOLDOWN_SECONDS", "300"))),
            "max_consecutive_failures": max(1, int(os.getenv("COMPANYOS_MAX_CONSECUTIVE_FAILURES", "3"))),
        }
