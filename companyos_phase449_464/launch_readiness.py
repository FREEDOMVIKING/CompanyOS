class LaunchReadiness:
    """449: decide whether a release candidate is ready for a controlled launch step."""

    REQUIRED = (
        "release_candidate_ready",
        "telemetry_ready",
        "rollback_ready",
        "support_path_ready",
    )

    def evaluate(self, state):
        checks = {k: bool(state.get(k)) for k in self.REQUIRED}
        return {
            "ready": all(checks.values()),
            "checks": checks,
            "automatic_irreversible_launch": False,
        }
