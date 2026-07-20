from __future__ import annotations
import os

class ExecutionBudget:
    """258: configurable retry/call limits to prevent accidental runaway loops."""

    def limits(self):
        return {
            "max_model_calls_per_mission": max(1, int(os.environ.get("COMPANYOS_MAX_MODEL_CALLS_PER_MISSION", "8"))),
            "max_repair_attempts": max(1, int(os.environ.get("COMPANYOS_MAX_REPAIR_ATTEMPTS", "5"))),
            "timeout_seconds": max(30, int(os.environ.get("COMPANYOS_MODEL_TIMEOUT_SECONDS", "600"))),
        }
