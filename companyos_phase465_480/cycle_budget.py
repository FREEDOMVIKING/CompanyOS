import os

class CycleBudget:
    """468: bounded work per persistent CEO cycle."""

    def limits(self):
        return {
            "max_stages_per_cycle": max(1, int(os.getenv("COMPANYOS_CEO_MAX_STAGES_PER_CYCLE","6"))),
            "max_failures_per_cycle": max(1, int(os.getenv("COMPANYOS_CEO_MAX_FAILURES_PER_CYCLE","3"))),
            "max_cycles_per_run": max(1, int(os.getenv("COMPANYOS_CEO_MAX_CYCLES_PER_RUN","3"))),
        }
