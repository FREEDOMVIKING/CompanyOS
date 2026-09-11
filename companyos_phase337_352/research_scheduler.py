from __future__ import annotations
import os

class ResearchScheduler:
    """349: configurable autonomous discovery cadence."""

    def cadence(self):
        return {
            "interval_minutes": max(15, int(os.getenv("COMPANYOS_RESEARCH_INTERVAL_MINUTES", "360"))),
            "max_cycles_per_day": max(1, int(os.getenv("COMPANYOS_RESEARCH_MAX_CYCLES_PER_DAY", "4"))),
        }
