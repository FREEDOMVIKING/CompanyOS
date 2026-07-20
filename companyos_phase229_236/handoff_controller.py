from __future__ import annotations

class HandoffController:
    """235: decide whether CompanyOS is ready for autonomous roadmap generation."""

    REQUIRED = {
        "real_filesystem_workspace",
        "real_test_execution",
        "live_integration",
        "rollback_available",
        "coder_connected",
        "persistent_runtime",
    }

    def evaluate(self, signals):
        passed = {k for k, v in signals.items() if bool(v)}
        missing = sorted(self.REQUIRED - passed)
        return {
            "ready": not missing,
            "missing": missing,
            "autonomous_roadmap_generation_allowed": not missing,
        }
