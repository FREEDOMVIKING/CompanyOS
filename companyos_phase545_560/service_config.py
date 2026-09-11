import os

class ServiceConfig:
    """545: runtime configuration for the continuous CEO service."""

    def load(self):
        return {
            "tick_interval_seconds": max(30, int(os.getenv("COMPANYOS_CEO_TICK_INTERVAL_SECONDS","300"))),
            "quality_cycle_every_ticks": max(1, int(os.getenv("COMPANYOS_QUALITY_CYCLE_EVERY_TICKS","3"))),
            "max_consecutive_failures": max(1, int(os.getenv("COMPANYOS_SERVICE_MAX_FAILURES","5"))),
            "idle_sleep_seconds": max(30, int(os.getenv("COMPANYOS_IDLE_SLEEP_SECONDS","300"))),
            "watchdog_stale_seconds": max(120, int(os.getenv("COMPANYOS_WATCHDOG_STALE_SECONDS","900"))),
        }
