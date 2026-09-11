class LaunchReadiness:
    """565: score controlled-launch readiness."""

    CHECKS = [
        "release_candidate_ready",
        "targeted_tests_pass",
        "regression_tests_pass",
        "telemetry_ready",
        "rollback_ready",
        "support_path_ready",
    ]

    def evaluate(self, state):
        checks = {k:bool(state.get(k)) for k in self.CHECKS}
        return {
            "ready":all(checks.values()),
            "checks":checks,
            "missing":[k for k,v in checks.items() if not v],
            "launch_mode":"controlled",
        }
